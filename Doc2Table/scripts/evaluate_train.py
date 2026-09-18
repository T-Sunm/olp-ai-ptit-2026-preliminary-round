"""Evaluate Markdown predictions against TACVU2 training labels.

Usage:
    python evaluate_train.py
    python evaluate_train.py --pred-dir outputs/predictions/training_set
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from difflib import SequenceMatcher
from html import escape
from pathlib import Path

from teds_metric import TEDS
from tqdm.auto import tqdm


SEPARATOR = re.compile(r"^:?-{3,}:?$")
BOLD = re.compile(r"^\*\*(.*)\*\*$", re.DOTALL)


def split_row(line: str) -> list[str]:
    line = line.strip()
    if not (line.startswith("|") and line.endswith("|")):
        raise ValueError(f"Not a Markdown row: {line[:80]!r}")
    cells, current, escaped = [], [], False
    for char in line[1:-1]:
        if char == "|" and not escaped:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        escaped = char == "\\" and not escaped
    cells.append("".join(current).strip())
    return cells


def parse_markdown(text: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    rows: list[list[str]] = []
    for line in text.splitlines():
        if line.strip().startswith("|"):
            row = split_row(line)
            if not all(SEPARATOR.fullmatch(cell) for cell in row):
                rows.append(row)
        elif not line.strip() and rows:
            tables.append(rows)
            rows = []
    if rows:
        tables.append(rows)
    if not tables:
        raise ValueError("No Markdown table found")
    return tables


def plain(value: str) -> str:
    match = BOLD.fullmatch(value)
    return match.group(1) if match else value


def is_bold(value: str) -> bool:
    return BOLD.fullmatch(value) is not None


def shape(table: list[list[str]]) -> tuple[int, ...]:
    return tuple(len(row) for row in table)


def merge_signature(table: list[list[str]]) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(cell if cell in {"[[H]]", "[[V]]"} else "." for cell in row) for row in table)


def table_to_html(table: list[list[str]]) -> str:
    """Convert TACVU2 merge markers into one HTML table for PubTabNet TEDS."""
    rows, cols = len(table), len(table[0])
    if any(len(row) != cols for row in table):
        raise ValueError("Non-rectangular Markdown table")
    parent = list(range(rows * cols))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: int, right: int) -> None:
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left

    for row in range(rows):
        for col in range(cols):
            node = row * cols + col
            if table[row][col] == "[[H]]":
                if col == 0:
                    raise ValueError("[[H]] cannot appear in the first column")
                union(node, node - 1)
            elif table[row][col] == "[[V]]":
                if row == 0:
                    raise ValueError("[[V]] cannot appear in the first row")
                union(node, node - cols)

    components: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row in range(rows):
        for col in range(cols):
            components[find(row * cols + col)].append((row, col))
    anchors = {min(members): members for members in components.values()}

    html_rows = []
    for row in range(rows):
        cells = []
        for col in range(cols):
            members = anchors.get((row, col))
            if members is None:
                continue
            row0, row1 = min(r for r, _ in members), max(r for r, _ in members) + 1
            col0, col1 = min(c for _, c in members), max(c for _, c in members) + 1
            if len(members) != (row1 - row0) * (col1 - col0):
                raise ValueError("Merge markers form a non-rectangular region")
            attributes = ""
            if row1 - row0 > 1:
                attributes += f' rowspan="{row1 - row0}"'
            if col1 - col0 > 1:
                attributes += f' colspan="{col1 - col0}"'
            value = table[row][col].replace("\\|", "|").replace("**", "")
            content = "<br/>".join(escape(part) for part in value.split("<br>"))
            cells.append(f"<td{attributes}>{content}</td>")
        html_rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<html><body><table><tbody>" + "".join(html_rows) + "</tbody></table></body></html>"


CONTENT_TEDS = TEDS(structure_only=False)


def document_teds(expected: list[list[list[str]]], predicted: list[list[list[str]]], scorer: TEDS) -> float:
    table_count = max(len(expected), len(predicted))
    if table_count == 0:
        return 0.0
    scores = []
    for table_id in range(table_count):
        true_html = table_to_html(expected[table_id]) if table_id < len(expected) else ""
        try:
            pred_html = table_to_html(predicted[table_id]) if table_id < len(predicted) else ""
        except ValueError:
            pred_html = ""
        scores.append(scorer.evaluate(pred_html, true_html))
    return sum(scores) / table_count


def compute_document_teds(pair: tuple[list[list[list[str]]], list[list[list[str]]]]) -> float:
    """Worker entry point: each process owns its lightweight TEDS scorer."""
    expected, predicted = pair
    return document_teds(expected, predicted, TEDS(structure_only=False))


def marker_positions(tables: list[list[list[str]]], marker: str) -> set[tuple[int, int, int]]:
    return {
        (table_id, row_id, col_id)
        for table_id, table in enumerate(tables)
        for row_id, row in enumerate(table)
        for col_id, cell in enumerate(row)
        if cell == marker
    }


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    return precision, recall, 2 * precision * recall / max(1e-12, precision + recall)


@dataclass
class Metrics:
    docs: int = 0
    complete: int = 0
    table_count_exact: int = 0
    shape_exact: int = 0
    merge_exact: int = 0
    cells: int = 0
    cell_exact: int = 0
    char_similarity: float = 0.0
    bold_tp: int = 0
    bold_fp: int = 0
    bold_fn: int = 0
    h_tp: int = 0
    h_fp: int = 0
    h_fn: int = 0
    v_tp: int = 0
    v_fp: int = 0
    v_fn: int = 0
    teds: float = 0.0

    def add(self, expected: list[list[list[str]]], predicted: list[list[list[str]]], teds_score: float | None = None) -> None:
        self.docs += 1
        self.complete += expected == predicted
        table_count_exact = len(expected) == len(predicted)
        shape_exact = table_count_exact and all(shape(left) == shape(right) for left, right in zip(expected, predicted))
        self.table_count_exact += table_count_exact
        self.shape_exact += shape_exact
        self.merge_exact += shape_exact and all(
            merge_signature(left) == merge_signature(right) for left, right in zip(expected, predicted)
        )
        self.teds += document_teds(expected, predicted, CONTENT_TEDS) if teds_score is None else teds_score
        if shape_exact:
            for marker, prefix in (("[[H]]", "h"), ("[[V]]", "v")):
                left, right = marker_positions(expected, marker), marker_positions(predicted, marker)
                setattr(self, f"{prefix}_tp", getattr(self, f"{prefix}_tp") + len(left & right))
                setattr(self, f"{prefix}_fp", getattr(self, f"{prefix}_fp") + len(right - left))
                setattr(self, f"{prefix}_fn", getattr(self, f"{prefix}_fn") + len(left - right))
        expected_bold = {
            (table_id, row_id, col_id)
            for table_id, table in enumerate(expected)
            for row_id, row in enumerate(table)
            for col_id, cell in enumerate(row)
            if is_bold(cell)
        }
        predicted_bold = {
            (table_id, row_id, col_id)
            for table_id, table in enumerate(predicted)
            for row_id, row in enumerate(table)
            for col_id, cell in enumerate(row)
            if is_bold(cell)
        }
        self.bold_tp += len(expected_bold & predicted_bold)
        self.bold_fp += len(predicted_bold - expected_bold)
        self.bold_fn += len(expected_bold - predicted_bold)
        for left_table, right_table in zip(expected, predicted):
            for left_row, right_row in zip(left_table, right_table):
                for left, right in zip(left_row, right_row):
                    self.cells += 1
                    self.cell_exact += left == right
                    self.char_similarity += SequenceMatcher(None, plain(left), plain(right)).ratio()

    def report(self, name: str) -> str:
        _, _, bold_f1 = prf(self.bold_tp, self.bold_fp, self.bold_fn)
        return (
            f"{name}: docs={self.docs} | complete={self.complete / max(1, self.docs):.2%} | "
            f"table-count={self.table_count_exact / max(1, self.docs):.2%} | "
            f"shape={self.shape_exact / max(1, self.docs):.2%} | "
            f"merge|shape={self.merge_exact / max(1, self.shape_exact):.2%} | "
            f"TEDS={self.teds / max(1, self.docs):.2%} | "
            f"cell-exact={self.cell_exact / max(1, self.cells):.2%} | "
            f"char-sim={self.char_similarity / max(1, self.cells):.2%} | bold-F1={bold_f1:.2%}"
        )

    def merge_report(self, name: str) -> str:
        h = prf(self.h_tp, self.h_fp, self.h_fn)
        v = prf(self.v_tp, self.v_fp, self.v_fn)
        overall = prf(self.h_tp + self.v_tp, self.h_fp + self.v_fp, self.h_fn + self.v_fn)
        return (
            f"{name}: shape-docs={self.shape_exact}/{self.docs} | "
            f"merge-exact|shape={self.merge_exact / max(1, self.shape_exact):.2%} | "
            f"H P/R/F1={h[0]:.2%}/{h[1]:.2%}/{h[2]:.2%} | "
            f"V P/R/F1={v[0]:.2%}/{v[1]:.2%}/{v[2]:.2%} | "
            f"all P/R/F1={overall[0]:.2%}/{overall[1]:.2%}/{overall[2]:.2%}"
        )


def self_check() -> None:
    table = parse_markdown("| **A** | x\\|y |\n| --- | --- |\n| [[V]] | z |\n")[0]
    assert table == [["**A**", "x\\|y"], ["[[V]]", "z"]]
    score = Metrics()
    score.add([table], [table])
    assert score.complete == score.table_count_exact == score.shape_exact == score.merge_exact == 1 and score.cell_exact == 4
    assert score.teds == 1.0
    merged = parse_markdown("| A | [[H]] | B |\n| --- | --- | --- |\n| [[V]] | [[V]] | C |\n")[0]
    merged_html = table_to_html(merged)
    assert 'rowspan="2" colspan="2"' in merged_html
    wrong = [["**A**", "x\\|y"], ["[[H]]", "z"]]
    score = Metrics()
    score.add([table], [wrong])
    assert (score.h_tp, score.h_fp, score.h_fn, score.v_tp, score.v_fp, score.v_fn) == (0, 1, 0, 0, 0, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred-dir", type=Path, default=Path("outputs/predictions/training_set"))
    parser.add_argument("--difficulty", nargs="+", choices=("M1", "M2", "M3", "M4"))
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1),
                        help="TEDS worker processes (default: up to 8 CPU cores; use 1 to disable parallelism)")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        print("self-check: OK")
        return
    if args.workers < 1:
        parser.error("--workers must be at least 1")

    root = Path(__file__).resolve().parent.parent
    pred_dir = args.pred_dir if args.pred_dir.is_absolute() else root / args.pred_dir
    train_dir = root / "data" / "training_set"
    records = [json.loads(line) for line in (train_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line]
    if args.difficulty:
        records = [record for record in records if record["difficulty"] in args.difficulty]
    evaluations = []
    missing, invalid = [], []
    for record in tqdm(records, desc="Reading Markdown", unit="doc"):
        expected = parse_markdown((train_dir / record["label_path"]).read_text(encoding="utf-8"))
        path = pred_dir / f"{record['id']}.md"
        if not path.is_file():
            missing.append(record["id"])
            predicted = []
        else:
            try:
                predicted = parse_markdown(path.read_text(encoding="utf-8"))
            except ValueError as error:
                invalid.append(f"{record['id']}: {error}")
                predicted = []
        evaluations.append((record, expected, predicted))

    pairs = ((expected, predicted) for _, expected, predicted in evaluations)
    if args.workers == 1:
        teds_scores = (document_teds(expected, predicted, CONTENT_TEDS) for _, expected, predicted in evaluations)
    else:
        pool = ProcessPoolExecutor(max_workers=args.workers)
        teds_scores = pool.map(compute_document_teds, pairs, chunksize=4)

    totals, by_difficulty, m2_groups = Metrics(), defaultdict(Metrics), defaultdict(Metrics)
    try:
        score_iter = tqdm(teds_scores, total=len(evaluations), desc=f"TEDS ({args.workers} workers)", unit="doc")
        for (record, expected, predicted), teds_score in zip(evaluations, score_iter, strict=True):
            totals.add(expected, predicted, teds_score)
            by_difficulty[record["difficulty"]].add(expected, predicted, teds_score)
            if record["difficulty"] == "M2":
                attributes = record["attributes"]
                m2_groups[f"M2 {attributes['table_count']}T{attributes['page_count']}P"].add(expected, predicted, teds_score)
    finally:
        if args.workers > 1:
            pool.shutdown(cancel_futures=True)

    print(f"predictions: {pred_dir}")
    print(f"files missing={len(missing)} | invalid={len(invalid)}")
    print("TEDS uses PubTabNet per table; multiple tables are averaged in document order (diagnostic aggregation)")
    print(totals.report("ALL"))
    for difficulty in sorted(by_difficulty):
        print(by_difficulty[difficulty].report(difficulty))
    print("M2 merge diagnostics (only shape-exact documents contribute marker counts):")
    for group in sorted(m2_groups):
        print(m2_groups[group].merge_report(group))
    if missing:
        print("missing examples:", ", ".join(missing[:10]))
    if invalid:
        print("invalid examples:", " | ".join(invalid[:3]))


if __name__ == "__main__":
    main()

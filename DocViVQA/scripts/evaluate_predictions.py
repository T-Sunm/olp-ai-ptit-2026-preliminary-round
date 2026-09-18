"""Evaluate TACVU2 predictions against training labels."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


DEFAULT_TYPES = ("lookup", "count", "sum", "argmax", "argmin", "compare", "cross_page_sum", "visual_bold_lookup")


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def levenshtein_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_character in enumerate(right, start=1):
            current.append(min(
                current[-1] + 1,
                previous[right_index] + 1,
                previous[right_index - 1] + (left_character != right_character),
            ))
        previous = current
    return previous[-1]


def anls(predicted: str | None, expected: list[str]) -> float:
    if predicted is None or not expected:
        return 0.0
    predicted = str(predicted).strip().lower()
    similarities = []
    for answer in expected:
        answer = str(answer).strip().lower()
        length = max(len(predicted), len(answer))
        similarities.append(1.0 if length == 0 else 1 - levenshtein_distance(predicted, answer) / length)
    best = max(similarities)
    return best if best > 0.5 else 0.0


def bbox_iou(first: dict, second: dict) -> float:
    if int(first["page"]) != int(second["page"]):
        return 0.0
    ax1, ay1, ax2, ay2 = map(float, first["bbox"])
    bx1, by1, bx2, by2 = map(float, second["bbox"])
    intersection = max(0.0, min(ax2, bx2) - max(ax1, bx1)) * max(0.0, min(ay2, by2) - max(ay1, by1))
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - intersection
    return intersection / union if union > 0 else 0.0


def evidence_scores(predicted: list[dict], expected: list[dict]) -> tuple[float, float, float]:
    matches = [-1] * len(expected)

    def match(predicted_index: int, visited: set[int]) -> bool:
        for expected_index, expected_box in enumerate(expected):
            if expected_index in visited or bbox_iou(predicted[predicted_index], expected_box) < 0.5:
                continue
            visited.add(expected_index)
            if matches[expected_index] == -1 or match(matches[expected_index], visited):
                matches[expected_index] = predicted_index
                return True
        return False

    matched = sum(match(index, set()) for index in range(len(predicted)))
    precision = matched / len(predicted) if predicted else float(not expected)
    recall = matched / len(expected) if expected else float(not predicted)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions", type=Path)
    parser.add_argument(
        "--labels",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "training_set" / "labels.jsonl",
    )
    parser.add_argument("--types", nargs="+", default=DEFAULT_TYPES)
    parser.add_argument("--show-failures", type=int, default=5)
    parser.add_argument(
        "--failures-out",
        type=Path,
        help="Defaults to <predictions_stem>_failures.jsonl.",
    )
    args = parser.parse_args()

    predictions = {
        row["question_id"]: row
        for row in read_jsonl(args.predictions)
    }
    metrics = defaultdict(lambda: {
        "total": 0, "answered": 0, "correct": 0,
        "anls": 0.0, "evidence_precision": 0.0,
        "evidence_recall": 0.0, "evidence_f1": 0.0, "score": 0.0,
    })
    failures = []

    for label in read_jsonl(args.labels):
        reasoning_type = label["reasoning_type"]
        if reasoning_type not in args.types:
            continue

        row = metrics[reasoning_type]
        row["total"] += 1
        prediction = predictions.get(label["question_id"])
        answer = prediction.get("answer") if prediction else None
        answered = answer not in (None, "không xác định")
        correct = answered and answer in label["answers"]
        answer_anls = anls(answer if answered else None, label["answers"])
        evidence_precision, evidence_recall, evidence_f1 = evidence_scores(
            prediction.get("evidence", []) if prediction else [],
            label.get("evidence", []),
        )
        question_score = 0.85 * answer_anls + 0.15 * evidence_f1
        row["answered"] += int(answered)
        row["correct"] += int(correct)
        row["anls"] += answer_anls
        row["evidence_precision"] += evidence_precision
        row["evidence_recall"] += evidence_recall
        row["evidence_f1"] += evidence_f1
        row["score"] += question_score

        if question_score < 1.0 - 1e-12:
            failures.append({
                "question_id": label["question_id"],
                "type": reasoning_type,
                "expected": label["answers"],
                "predicted": answer,
                "anls": round(answer_anls, 6),
                "evidence_precision": round(evidence_precision, 6),
                "evidence_recall": round(evidence_recall, 6),
                "evidence_f1": round(evidence_f1, 6),
                "question_score": round(question_score, 6),
            })

    print(
        f"{'type':<18} {'total':>6} {'coverage':>9} {'exact':>8} {'ANLS':>8} "
        f"{'Ev-P':>8} {'Ev-R':>8} {'Ev-F1':>8} {'score':>8}"
    )
    for reasoning_type in args.types:
        row = metrics[reasoning_type]
        total = row["total"]
        coverage = row["answered"] / total if total else 0.0
        accuracy = row["correct"] / total if total else 0.0
        print(
            f"{reasoning_type:<18} {total:>6} {coverage:>8.2%} {accuracy:>7.2%} "
            f"{row['anls'] / total:>7.2%} {row['evidence_precision'] / total:>7.2%} "
            f"{row['evidence_recall'] / total:>7.2%} {row['evidence_f1'] / total:>7.2%} "
            f"{row['score'] / total:>7.2%}"
        )

    totals = {key: sum(row[key] for row in metrics.values()) for key in next(iter(metrics.values()))}
    total = totals["total"]
    print(
        f"{'overall':<18} {total:>6} {totals['answered'] / total:>8.2%} "
        f"{totals['correct'] / total:>7.2%} {totals['anls'] / total:>7.2%} "
        f"{totals['evidence_precision'] / total:>7.2%} {totals['evidence_recall'] / total:>7.2%} "
        f"{totals['evidence_f1'] / total:>7.2%} {totals['score'] / total:>7.2%}"
    )

    failures_out = args.failures_out or args.predictions.with_name(
        f"{args.predictions.stem}_failures.jsonl"
    )
    failures_out.parent.mkdir(parents=True, exist_ok=True)
    with failures_out.open("w", encoding="utf-8") as handle:
        for failure in failures:
            handle.write(json.dumps(failure, ensure_ascii=False) + "\n")

    print(f"\nSaved {len(failures)} failures to: {failures_out}")
    if failures and args.show_failures > 0:
        print("Failures preview:")
        for failure in failures[:args.show_failures]:
            print(json.dumps(failure, ensure_ascii=False))


if __name__ == "__main__":
    main()

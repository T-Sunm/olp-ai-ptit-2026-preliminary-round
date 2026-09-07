"""Evaluate TACVU2 predictions against training labels."""

import argparse
import json
from collections import defaultdict
from pathlib import Path


DEFAULT_TYPES = ("lookup", "count", "sum", "argmax", "argmin", "compare", "cross_page_sum", "visual_bold_lookup")


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
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
    metrics = defaultdict(lambda: {"total": 0, "answered": 0, "correct": 0})
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
        row["answered"] += int(answered)
        row["correct"] += int(correct)

        if not correct:
            failures.append({
                "question_id": label["question_id"],
                "type": reasoning_type,
                "expected": label["answers"],
                "predicted": answer,
            })

    print(f"{'type':<10} {'total':>6} {'answered':>9} {'coverage':>10} {'correct':>8} {'accuracy':>10}")
    for reasoning_type in args.types:
        row = metrics[reasoning_type]
        total = row["total"]
        coverage = row["answered"] / total if total else 0.0
        accuracy = row["correct"] / total if total else 0.0
        print(
            f"{reasoning_type:<10} {total:>6} {row['answered']:>9} "
            f"{coverage:>9.2%} {row['correct']:>8} {accuracy:>9.2%}"
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

"""Ground-truth dataset integrity and prediction metric helpers."""

import json
from pathlib import Path
from typing import Any, Iterable


REQUIRED_FIELDS = {"id", "text", "category", "severity", "sentiment", "priority", "incident", "policy", "decision"}


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    dataset_path = path or Path(__file__).resolve().parents[3] / "data" / "evaluation" / "cases.json"
    return json.loads(dataset_path.read_text(encoding="utf-8"))


def accuracy(expected: Iterable[Any], predicted: Iterable[Any]) -> float:
    expected_values, predicted_values = list(expected), list(predicted)
    if not expected_values or len(expected_values) != len(predicted_values):
        return 0.0
    return sum(left == right for left, right in zip(expected_values, predicted_values)) / len(expected_values)


def evaluate_dataset(cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    records = cases or load_cases()
    missing = sorted({field for record in records for field in REQUIRED_FIELDS - record.keys()})
    return {
        "dataset_size": len(records),
        "schema_complete": not missing,
        "missing_fields": missing,
        "decision_distribution": {
            decision: sum(record.get("decision") == decision for record in records)
            for decision in ("AUTO_RESOLVE", "HUMAN_APPROVAL", "ESCALATE")
        },
        "metrics": {
            "understanding_accuracy": None,
            "priority_agreement": None,
            "rag_top_k_hit_rate": None,
            "resolution_validity": None,
            "incident_precision": None,
            "incident_recall": None,
        },
        "note": "Metrics remain null until model predictions are supplied; no accuracy is fabricated from ground truth alone.",
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_dataset(), indent=2))

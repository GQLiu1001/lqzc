from __future__ import annotations

import json
from pathlib import Path

from app.schemas.eval import EvalCase


DATASET_DIR = Path(__file__).resolve().parent / "datasets"


def list_datasets() -> list[str]:
    if not DATASET_DIR.exists():
        return []
    names = []
    for path in sorted(DATASET_DIR.glob("*.jsonl")):
        names.append(path.stem)
    return names


def load_dataset(dataset_name: str, *, max_cases: int | None = None) -> list[EvalCase]:
    path = DATASET_DIR / f"{dataset_name}.jsonl"
    if not path.exists():
        raise ValueError(f"Unknown dataset: {dataset_name}")

    cases: list[EvalCase] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid json in dataset `{dataset_name}` at line {line_no}: {exc}") from exc
            cases.append(EvalCase.model_validate(payload))
            if max_cases is not None and max_cases > 0 and len(cases) >= max_cases:
                break
    return cases

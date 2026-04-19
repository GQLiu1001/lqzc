import json
from pathlib import Path

from app.eval.schemas import EvalSample


def load_jsonl(path: str | Path) -> list[EvalSample]:
    """Load a golden dataset from JSONL. Skips blank lines and `#` comments."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"eval dataset not found: {p}")

    samples: list[EvalSample] = []
    with p.open("r", encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{p.name}:{lineno} invalid JSON: {exc}") from exc
            samples.append(EvalSample.model_validate(payload))
    return samples

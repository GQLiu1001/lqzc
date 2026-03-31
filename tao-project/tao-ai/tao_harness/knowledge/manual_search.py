"""Simple local manual search.

This file intentionally uses a naive text-ranking strategy.
The point of the first harness version is not retrieval quality;
it is to show how a model can *ask* for knowledge when needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ManualHit:
    manual_name: str
    score: int
    preview: str


class LocalManualSearch:
    """Search local txt manuals from the lqzc workspace."""

    def __init__(self, manuals_dir: Path) -> None:
        self.manuals_dir = manuals_dir

    def search(self, query: str, top_k: int = 3) -> list[dict[str, str | int]]:
        if not self.manuals_dir.exists() or not query.strip():
            return []

        keywords = [part.lower() for part in query.split() if part.strip()]
        if not keywords:
            keywords = [query.lower()]

        hits: list[ManualHit] = []
        for file_path in sorted(self.manuals_dir.glob("*.txt")):
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            paragraphs = [item.strip() for item in text.splitlines() if item.strip()]

            for paragraph in paragraphs:
                lower_text = paragraph.lower()
                score = sum(lower_text.count(word) for word in keywords)
                if score <= 0:
                    continue
                hits.append(
                    ManualHit(
                        manual_name=file_path.name,
                        score=score,
                        preview=paragraph[:300],
                    )
                )

        hits.sort(key=lambda item: item.score, reverse=True)
        return [
            {
                "manual_name": item.manual_name,
                "score": item.score,
                "preview": item.preview,
            }
            for item in hits[:top_k]
        ]


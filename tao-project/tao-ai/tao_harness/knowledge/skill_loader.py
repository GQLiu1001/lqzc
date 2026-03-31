"""On-demand skill loading inspired by learn-claude-code s05."""

from __future__ import annotations

from pathlib import Path


class SkillLoader:
    """Load full skill bodies only when the model asks for them."""

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir

    def list_skill_names(self) -> list[str]:
        if not self.skills_dir.exists():
            return []
        return sorted(path.name for path in self.skills_dir.iterdir() if path.is_dir())

    def load(self, skill_name: str) -> str:
        skill_path = self.skills_dir / skill_name / "SKILL.md"
        if not skill_path.exists():
            available = ", ".join(self.list_skill_names()) or "(none)"
            return f"Skill `{skill_name}` not found. Available skills: {available}"
        return skill_path.read_text(encoding="utf-8")


import threading
from typing import Optional

from openhands.sdk.context.skills import (
    load_public_skills,
    load_project_skills,
    load_user_skills,
)
from openhands.sdk.context.skills.skill import Skill

_lock = threading.Lock()
_cached_public_skills: Optional[list[Skill]] = None
_cached_user_skills: Optional[list[Skill]] = None
_cached_project_skills: dict[str, list[Skill]] = {}


def get_public_skills() -> list[Skill]:
    global _cached_public_skills
    with _lock:
        if _cached_public_skills is None:
            _cached_public_skills = load_public_skills()
        return _cached_public_skills


def get_user_skills() -> list[Skill]:
    global _cached_user_skills
    with _lock:
        if _cached_user_skills is None:
            _cached_user_skills = load_user_skills()
        return _cached_user_skills


def get_project_skills(workspace: str) -> list[Skill]:
    with _lock:
        if workspace not in _cached_project_skills:
            _cached_project_skills[workspace] = load_project_skills(workspace)
        return _cached_project_skills[workspace]


def refresh_skills():
    global _cached_public_skills, _cached_user_skills
    with _lock:
        _cached_public_skills = None
        _cached_user_skills = None
        _cached_project_skills.clear()


def skill_trigger_label(skill: Skill) -> tuple[str, str]:
    """Return (label_text, css_class) for a skill's trigger badge."""
    if skill.trigger is None:
        return "Always active", "skill-badge-always"
    words = getattr(skill.trigger, "keywords", None) or getattr(skill.trigger, "triggers", [])
    label = ", ".join(words[:3]) + ("…" if len(words) > 3 else "")
    return f"Keyword: {label}", "skill-badge-keyword"

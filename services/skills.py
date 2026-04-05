import threading
from typing import Optional

from openhands.sdk.context.skills import load_public_skills, load_project_skills
from openhands.sdk.context.skills.skill import Skill

_lock = threading.Lock()
_cached_public_skills: Optional[list[Skill]] = None
_cached_project_skills: dict[str, list[Skill]] = {}


def get_public_skills() -> list[Skill]:
    global _cached_public_skills
    with _lock:
        if _cached_public_skills is None:
            _cached_public_skills = load_public_skills()
        return _cached_public_skills


def get_project_skills(workspace: str) -> list[Skill]:
    with _lock:
        if workspace not in _cached_project_skills:
            _cached_project_skills[workspace] = load_project_skills(workspace)
        return _cached_project_skills[workspace]


def get_all_skills(workspace: str = ".") -> list[Skill]:
    public = get_public_skills()
    project = get_project_skills(workspace)
    seen = set()
    merged = []
    for s in project + public:
        if s.name not in seen:
            seen.add(s.name)
            merged.append(s)
    return merged


def refresh_skills():
    global _cached_public_skills
    with _lock:
        _cached_public_skills = None
        _cached_project_skills.clear()


def skill_to_dict(skill: Skill) -> dict:
    trigger_info = None
    if skill.trigger:
        trigger_info = {"type": skill.trigger.type}
        words = getattr(skill.trigger, "keywords", None) or getattr(skill.trigger, "triggers", [])
        trigger_info["keywords"] = words
    return {
        "name": skill.name,
        "description": skill.description or "",
        "trigger": trigger_info,
        "is_agentskills_format": skill.is_agentskills_format,
        "source": skill.source,
        "has_resources": skill.resources is not None,
    }

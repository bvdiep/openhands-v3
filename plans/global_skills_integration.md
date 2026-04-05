# Plan: Professional Global Skills Integration (AgentSkills Standard)

## 1. Objective
Enable a robust, standardized skill system following the [AgentSkills specification](https://agentskills.io/specification). This ensures the Web interface provides a superior experience compared to the CLI by integrating both local custom skills and the official OpenHands public skill registry with clear visual feedback.

## 2. Core Requirements

### A. Directory Structure (AgentSkills Standard)
- **Global Skills Directory:** Create a `skills/` folder at the root of the `openhands-v3` project.
- **Skill Format:** Each skill must be its own subdirectory containing a `SKILL.md` file.
    ```
    skills/my-helper-skill/
    ├── SKILL.md       # Required: YAML frontmatter (name, description, triggers) + Markdown content
    ├── scripts/       # Optional: Executable scripts (e.g., .sh, .py)
    └── references/    # Optional: Additional documentation
    ```
- **Frontmatter Requirement:** Every `SKILL.md` must include `name`, `description`, and optional `triggers` (keywords) for automatic activation.

### B. Logical Implementation (`engine/runner.py`)
- **Global Discovery:** Update `TaskRunner` to resolve the absolute path of the root `skills/` directory.
- **SDK Integration:** Use `openhands.sdk.context.skills.load_skills_from_dir` to load skills from the global directory.
- **Public Skills:** Set `load_public_skills=True` in `AgentContext` to automatically pull community-contributed skills from the [OpenHands Extensions registry](https://github.com/OpenHands/extensions).
- **Context Merging:** Ensure both Global (local project-wide) and Public skills are merged into the `AgentContext` passed to the `Agent`.

### C. UI & UX Enhancements
- **Skill Availability Indicator:** Add a "Available Skills" section on the Web UI to display a list of all loaded skills (Name + Short Description).
- **Activation Feedback:** When a `KeywordTrigger` is matched in a conversation, provide a visual indicator (e.g., a toast or a highlight) in the `#conversation-flow` showing which skill's knowledge is being applied.
- **Markdown Rendering:** Ensure skill content and descriptions are rendered correctly using `marked.js`.

### D. API Enhancements
- **`GET /api/skills`**: Update this endpoint to return comprehensive metadata for all loaded skills:
    ```json
    {
      "global_skills": [{"name": "...", "description": "...", "triggers": [...]}],
      "public_skills": [...],
      "workspace_skills": [...]
    }
    ```

## 3. Implementation Steps for OpenHands

### Step 1: Environment Setup
- Create the root `skills/` directory.
- Add a sample skill `skills/test-skill/SKILL.md` with valid frontmatter to verify the loading mechanism.

### Step 2: Update TaskRunner
- Modify `engine/runner.py` to use `load_skills_from_dir`.
- Enable `load_public_skills=True` in the `AgentContext` initialization.

### Step 3: Frontend & API Update
- Update `main.py` to expose the loaded skills via the status or a new API.
- Update the Web UI template to display these skills to the user.

## 4. Definition of Done (DoD)
- [ ] `SKILL.md` files are correctly parsed and their metadata is extracted.
- [ ] Public skills from GitHub are successfully integrated into the Agent's context.
- [ ] The Web UI displays a clear list of "available superpowers" (skills).
- [ ] Agent can reference and execute scripts located within a skill's `scripts/` directory.
- [ ] API provides a clear JSON map of all enabled skills.
- [ ] Documentation (README and API_USAGE) is up-to-date.

# Plan: Deep Reasoning Extraction & Step-by-Step Visualization

## 1. Objective
Refine the "Thinking" mechanism to capture full reasoning blocks (not just summaries) and provide real-time step-by-step status updates on the Web UI. This addresses the current limitation where intermediate steps (e.g., Browser actions) and detailed mental assessments are missing from the UI and database.

## 2. Technical Enhancements

### A. Comprehensive Reasoning Capture (`engine/runner.py`)
- **Deep Extraction:** Update the `_on_event` method in `TaskRunner` to capture detailed reasoning.
    - Intercept `ActionEvent` and extract the `thought` property (which often contains the full reasoning block).
    - If the SDK provides a `Summary` field, capture that as well for a high-level status.
- **Step Tracking:** 
    - Treat each `ActionEvent` (e.g., `BrowserNavigateAction`, `BrowserGetStateAction`) as a distinct "Step" in the thinking process.
    - Capture the specific action name and its summary.

### B. Structured Data Storage (`main.py`)
- **JSON Object Array:** Update the `thoughts` column in `execution_turns` to store a JSON array of objects instead of plain strings:
  ```json
  [
    {
      "step": "BrowserNavigateAction",
      "summary": "Search for news on Iran",
      "reasoning": "Detailed block of text explaining why...",
      "timestamp": "2026-04-05T..."
    }
  ]
  ```
- **Update Logic:** Ensure the database update functions handle this structured JSON correctly.

### C. Live UI Status Bar (Next to Execute Button)
- **Real-time Specificity:** Update the `#live-thought-indicator` (next to the Execute button) to reflect the *specific* current step.
- **Dynamic Format:** `🤔 [Summary]: [Action Name]...` 
    - *Example:* `🤔 Try DuckDuckGo: BrowserNavigateAction...`
- **Instant Sync:** Ensure every `ActionEvent` triggers an `agent_thought` SSE event to keep the UI perfectly in sync with the agent's actual operations.

## 3. API & History Modal Improvements
- **`GET /api/execute/{id}/messages`**: Return the new structured JSON for thoughts, allowing third-party apps to visualize the chain of thought.
- **Conversation Modal:** Update the UI to display the full "Chain of Thought". 
    - Each turn should include a collapsible "Reasoning Details" section.
    - Show the sequence of steps taken (e.g., Navigate -> Get Content -> Analyze) with their respective reasoning blocks.

### D. Documentation & System Updates
- **API_USAGE.md**: Update the documentation for `GET /api/execute/{id}/status` and `GET /api/execute/{id}/messages` to reflect the new structured JSON format for thoughts (an array of objects containing `step`, `summary`, `reasoning`, and `timestamp`).
- **README.md**: Add "Step-by-step AI Reasoning Transparency" and "Deep Thought Chain Analysis" to the features list.

## 4. Implementation Steps for OpenHands
1. **Runner Refactoring**: Improve event handling in `engine/runner.py` to catch and aggregate all intermediate `ActionEvent` data.
2. **Database Update**: Ensure the `thoughts` column can store the larger JSON payloads.
3. **Frontend Scripting**: Update the SSE listener in `main.py` to handle the enriched thought data objects.
4. **API Refresh**: Update status and message endpoints to serve the new structured data.

## 5. Definition of Done (DoD)
- [] Users see real-time updates for *every* tool action (Search, Read, etc.) next to the Execute button.
- [] Full reasoning blocks are successfully captured, stored, and viewable in the history.
- [] The history modal provides a clear step-by-step audit trail of the agent's internal process.
- [] API provides the structured chain of thought for external integrations.
- [] Documentation (`API_USAGE.md`) and Feature list (`README.md`) updated to reflect the new reasoning transparency.

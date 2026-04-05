# Plan: Live Thinking Status & Thought Storage

## 1. Objective
Enhance the UI/UX by showing the Agent's current step ("Thinking...") in real-time right next to the execution controls, and storing the full chain of thought for each turn in the database.

## 2. Technical Requirements

### A. Data Capture (`engine/runner.py`)
- **Intercept Thoughts:** Update the `_on_event` method to catch `ActionEvent` and extract the `thought` property from the action object.
- **Thought Aggregation:** Maintain a list `self._current_turn_thoughts` to collect all thoughts within a single turn.
- **SSE Trigger:** Immediately emit an SSE event of type `agent_thought` with the content of the current thought whenever an `ActionEvent` with a `thought` is processed.

### B. Storage & Database (`main.py`)
- **Schema Update:** Modify `init_db` to ensure the `execution_turns` table contains a `thoughts` column (TEXT type to store a JSON-encoded list).
- **Persistence Logic:**
    - Update `update_turn_status` to accept a `thoughts` parameter.
    - In the task thread, when a turn is finalized (success or error), pass the aggregated thoughts list (as a JSON string) to the database update function.

### C. Web UI (Live "Thinking" Component)
- **New Element:** Add a `#live-thought-indicator` span next to the `Execute` button and the `Conversation #x` link.
- **Visual Style:** Subtle text (e.g., italicized, light blue) with a small spinner icon.
- **Behavior:** 
    - **Update:** When an `agent_thought` event is received via SSE, update the `#live-thought-indicator` text with the latest thought.
    - **One-line Only:** The UI should only show the *most recent* thought, not a list, to prevent clutter.
    - **Clearance:** Automatically clear the text and hide the spinner when the final `agent_message` arrives or when the execution status changes to `waiting_for_input`.

### D. API Updates
- **`GET /api/execute/{id}/status`**: Include `current_thought` in the response when the agent is in the `running` state.
- **`GET /api/execute/{id}/messages`**: Include a `thoughts` field (parsed JSON array) for each turn/message in the history.

## 3. Documentation & System Updates

### A. API_USAGE.md
- Document the new `current_thought` field in the status endpoint.
- Document the `thoughts` array in the message history endpoint with JSON examples.

### B. README.md
- Update the "Features" section to include "Real-time Agent Thinking Status" and "Historical Chain of Thought Storage".

## 4. Implementation Steps for OpenHands

### Step 1: Database Migration
- Add the `thoughts` column to the `execution_turns` table in `main.py`.

### Step 2: Runner Modification
- Update `engine/runner.py` to collect thoughts and trigger the `agent_thought` SSE event.

### Step 3: Frontend Update
- Add the `#live-thought-indicator` element to the main page layout in `main.py`.
- Update the `EventSource` listener in the `post_execute` response to handle the `agent_thought` event type and update the UI indicator.

### Step 4: API & Documentation
- Update the API endpoints in `main.py`.
- Update `get_conversation` and `get_execution_detail` modals to display the stored thoughts (e.g., in a collapsed `<details>` section).
- Update `API_USAGE.md` and `README.md` as specified in Section 3.

## 5. Definition of Done (DoD)
- [x] Users see a real-time "Thinking..." status next to the Execute button.
- [x] The indicator only shows the current step, preventing UI jitter.
- [x] Every thought in the chain is saved to the SQLite database.
- [x] History and API correctly expose the full thinking process for analysis.
- [x] Documentation (README and API_USAGE) is up-to-date.

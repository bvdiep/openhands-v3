# Plan: Upgrade Conversation Interface & Message API

## 1. Objective
Transform the current technical log viewer into a human-centric AI conversation interface. This involves visualizing the agent's thinking process (agent messages) separately from technical logs on the Web UI and exposing these messages via a structured API.

## 2. Web UI Enhancements (The "Thinking Flow")

### A. Dedicated Conversation Area
- **Component:** Add a new container `#conversation-flow` above the terminal output.
- **Visual Style:** 
    - Display messages from the agent as distinct "Chat Bubbles" or styled blocks.
    - Use a different background (e.g., light blue or soft gray) and an icon (🤖) to identify Agent messages.
    - Messages must be rendered as Markdown (using `marked.js`) to support code blocks, bold text, and lists.
- **Dynamic Updates:** 
    - Every time a turn finishes (received via SSE), the `agent_message` from that turn must be appended to `#conversation-flow`.
    - Automatically scroll to the bottom of the conversation when a new message arrives.

### B. Logical Separation
- **The Terminal:** Keep the terminal for raw execution data (shell commands, file outputs, system logs).
- **The Thought Flow:** Use the new conversation area for "Human-to-AI" communication (explanations, questions, and status updates from the Agent).
- **Interaction Point:** The most recent message in the flow serves as the current context/request for the user.

## 3. API Enhancements (Message Retrieval)

### A. New Endpoint: `GET /api/execute/{id}/messages`
- **Description:** Retrieve a structured list of all agent messages for a specific execution.
- **Response Format:**
```json
{
  "execution_id": 123,
  "messages": [
    {
      "turn_number": 1,
      "role": "agent",
      "content": "I will start by listing the files in the directory...",
      "timestamp": "2024-03-21T10:00:00"
    },
    {
      "turn_number": 2,
      "role": "agent",
      "content": "I found a bug in line 45. Should I fix it?",
      "timestamp": "2024-03-21T10:05:00"
    }
  ]
}
```

### B. Update: `GET /api/execute/{id}/status`
- Ensure `last_agent_message` and `current_turn` are always up-to-date by querying the `execution_turns` table.

## 4. Implementation Steps for OpenHands

### Step 1: Database Verification
- Ensure `agent_message` is being correctly saved to the `execution_turns` table in `main.py` after each turn.

### Step 2: Backend Logic (FastHTML)
- Create a helper function `render_thought_flow(exec_id)` that retrieves all turns and returns a list of styled `Div` elements containing the agent messages.
- Update the `/conversation/{exec_id}` modal to show this flow clearly.

### Step 3: Frontend Scripting
- Update the `EventSource` logic in `main.py` to detect when a turn is complete and trigger a partial refresh or DOM append for the conversation area.

### Step 4: API Routes
- Implement the `/api/execute/{id}/messages` route in `main.py`.

## 5. Documentation Updates
- **API_USAGE.md:** Add documentation for the new `/api/execute/{id}/messages` endpoint.
- **README.md:** Update "Features" to include "Conversation & Thinking Process Visualization".

## 6. Definition of Done (DoD)
- [ ] Agent messages are visually separated from terminal logs on the Web UI.
- [ ] All past agent messages are stored and viewable in the execution history.
- [ ] Third-party developers can retrieve the full conversation history via the `/api/execute/{id}/messages` endpoint.
- [ ] Web UI automatically scrolls and highlights the latest agent request.
- [ ] Markdown rendering works correctly for code blocks within agent messages.

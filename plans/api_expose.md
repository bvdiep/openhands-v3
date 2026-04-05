# Plan: Expose OpenHands-v3 as a Secure Third-Party API

## 1. Objective
Expose the current form-based task execution as a RESTful API to allow third-party integrations. The API must support secure authentication, session/conversation persistence, and optimized resource management.

## 2. Core Requirements

### A. Authentication & Security
- **API Key Implementation:** Add an `API_KEY` variable to the project configuration (and `.env`).
- **Middleware/Auth Update:** Modify `auth_before` in `main.py` to support `X-API-Key` or `Bearer Token` headers specifically for `/api/*` routes.
- **Environment Protection:** Ensure sensitive keys are not exposed in logs or version control.

### B. Logical Refactoring
- **Task Thread Decoupling:** Extract the core `run_task_thread` logic from the FastHTML `/execute` route into a reusable function or class method that can be invoked by both the Web UI and the new API.
- **State Management:** Ensure `execution_inputs` and `execution_queues` are correctly initialized and cleaned up when a session ends (success, error, or timeout).

### C. Conversation Persistence & Optimization
- **Persistent Sessions:** API must allow sending follow-up prompts to an active `execution_id` to maintain conversation context within the same `TaskRunner` instance.
- **Waiting Mechanism Timeout:** Implement a timeout (e.g., 3600 seconds) for `in_q.get(block=True)`. If no input is received within the timeout, the session should automatically send a `__STOP__` command to free system resources.
- **SSE Heartbeat:** Ensure the `/stream/{id}` endpoint sends periodic keep-alive comments to prevent connection drops by proxies or load balancers.

### D. New API Endpoints
- `POST /api/execute`: Initialize a new task.
    - Input: `{"prompt": string, "model": string, "workspace": string, "mcp_ids": array}`
    - Output: `{"execution_id": integer, "status": "running"}`
- `POST /api/execute/{id}/message`: Send a follow-up prompt to a waiting session.
    - Input: `{"prompt": string}`
    - Output: `{"status": "message_sent"}`
- `GET /api/execute/{id}/status`: Fetch current execution status and metrics.
    - Output: `{"status": "running|waiting_for_input|completed|error", "metrics": {...}}`
- `POST /api/execute/{id}/stop`: Forcefully terminate an active session.

## 3. Documentation & System Updates
- **README.md:** Add a section for "API Integration" detailing the available endpoints.
- **.env.sample:** Add `API_KEY=your_secret_key_here` and other necessary environment variables.
- **API_USAGE.md:** (New) Create a dedicated guide for third-party developers, including cURL examples for starting a task, listening to SSE logs, and continuing a conversation.

## 4. Definition of Done (DoD)
- [x] API routes are protected by the `API_KEY`.
- [x] Third-party requests can successfully start a task and receive an `execution_id`.
- [x] Follow-up messages correctly resume the conversation in the same environment.
- [x] Inactive threads are automatically closed after the defined timeout.
- [x] Web UI functionality remains intact and bug-free.
- [x] Documentation is updated and accurate.

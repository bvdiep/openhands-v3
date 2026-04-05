# OpenHands-v3 API Usage Guide

This guide explains how to use the OpenHands-v3 REST API to integrate task execution into your own applications.

## Authentication

All API endpoints under `/api/*` require authentication using an API key. You can provide the API key in one of two ways:

1. **X-API-Key Header**: `X-API-Key: your_secret_api_key_here`
2. **Bearer Token**: `Authorization: Bearer your_secret_api_key_here`

The API key must match the `API_KEY` environment variable set in your `.env` file.

## Endpoints

### 1. Start a New Task

Initialize a new task execution session.

**Endpoint:** `POST /api/execute`

**Request Body (JSON):**
```json
{
  "prompt": "Your task description here",
  "model": "gpt-4o",
  "workspace": "/path/to/workspace",
  "mcp_ids": ["mcp_server_1", "mcp_server_2"]
}
```

**Response:**
```json
{
  "execution_id": 123,
  "status": "running"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8101/api/execute \
  -H "X-API-Key: your_secret_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "List files in the workspace", "model": "gpt-4o", "workspace": "/tmp"}'
```

### 2. Stream Logs (SSE)

Listen to real-time logs from an active execution session using Server-Sent Events (SSE).

**Endpoint:** `GET /stream/{execution_id}`

*Note: This endpoint does not require the API key as it is used by the frontend as well, but you need the `execution_id`.*

**cURL Example:**
```bash
curl -N http://localhost:8101/stream/123
```

### 3. Send a Follow-up Message

Send a follow-up prompt to a waiting session to continue the conversation.

**Endpoint:** `POST /api/execute/{execution_id}/message`

**Request Body (JSON):**
```json
{
  "prompt": "Please explain the previous output."
}
```

**Response:**
```json
{
  "status": "message_sent"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8101/api/execute/123/message \
  -H "X-API-Key: your_secret_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Please explain the previous output."}'
```

### 4. Check Execution Status

Fetch the current status and metrics of an execution.

**Endpoint:** `GET /api/execute/{execution_id}/status`

**Response:**
```json
{
  "status": "running",
  "last_agent_message": "I have listed the files in the directory. What would you like me to do next?",
  "current_turn": 1,
  "metrics": {
    "total_tokens": 1500,
    "cost": 0.015
  },
  "current_thought": {
    "step": "BrowserNavigateAction",
    "summary": "Search for news on Iran",
    "reasoning": "Detailed block of text explaining why...",
    "timestamp": "2026-04-05T14:00:00.000000"
  }
}
```

**Understanding the Status:**
- `status`:
    - `running`: The agent is currently processing the task.
    - `waiting_for_input`: The agent has completed its current set of actions and is waiting for further instructions from the user.
    - `completed`: The session has been closed.
    - `error`: An error occurred during execution.
- `last_agent_message`: This contains the textual response from the agent in the most recent turn. When `status` is `waiting_for_input`, this message usually explains what the agent has done or asks the user for clarification/next steps.
- `current_turn`: The sequence number of the most recent turn.
- `current_thought`: A structured object representing the agent's *active* step, including:
    - `step`: The action name (e.g., `BrowserNavigateAction`).
    - `summary`: A high-level description of what the agent is doing.
    - `reasoning`: The detailed thought process behind this specific action.
    - `timestamp`: When this step was initiated.

**Integrator Tip:**
To distinguish between an ongoing task and a request for user input, check if `status` is `waiting_for_input`. If it is, you should display `last_agent_message` to the user and provide an interface for them to send a follow-up message using the `/api/execute/{execution_id}/message` endpoint. For real-time updates, the `current_thought` provides granular visibility into the agent's internal steps.

**cURL Example:**
```bash
curl -X GET http://localhost:8101/api/execute/123/status \
  -H "X-API-Key: your_secret_api_key_here"
```

### 5. Stop an Execution

Forcefully terminate an active session.

**Endpoint:** `POST /api/execute/{execution_id}/stop`

**Response:**
```json
{
  "status": "stop_signal_sent"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8101/api/execute/123/stop \
  -H "X-API-Key: your_secret_api_key_here"
```

## Session Management

- **Timeouts**: If an execution session is waiting for input and no message is received within 3600 seconds (1 hour), the session will automatically terminate to free up resources.
- **Heartbeats**: The SSE stream sends periodic keep-alive comments (`: heartbeat`) every 15 seconds to prevent connection drops by proxies or load balancers.

### 6. Get Conversation Messages

Retrieve a structured list of all agent messages for a specific execution.

**Endpoint:** `GET /api/execute/{execution_id}/messages`

**Response:**
```json
{
  "execution_id": 123,
  "messages": [
    {
      "turn_number": 1,
      "role": "agent",
      "content": "I will start by listing the files in the directory...",
      "timestamp": "2024-03-21T10:00:00",
      "thoughts": [
        {
          "step": "TerminalAction",
          "summary": "List files in workspace",
          "reasoning": "I should use the ls command to see what files are here.",
          "timestamp": "2026-04-05T13:59:00.000000"
        },
        {
          "step": "FinishAction",
          "summary": "Found several python files",
          "reasoning": "The directory contains several python files.",
          "timestamp": "2026-04-05T14:00:00.000000"
        }
      ]
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

**cURL Example:**
```bash
curl -X GET http://localhost:8101/api/execute/123/messages \
  -H "X-API-Key: your_secret_api_key_here"
```

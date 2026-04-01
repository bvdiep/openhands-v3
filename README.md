# FastHTML Executor App

A FastHTML web application that allows users to input a prompt and specify a model to execute a backend process. The application provides real-time streaming of execution logs (similar to a terminal) and maintains a history of all executions in a SQLite database.

## Setup

1. Install dependencies:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2. Run the application:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8101
    ```
    Or using PM2:
    ```bash
    pm2 start ecosystem.config.json
    ```

## Features

- Form with prompt textarea and model input
- Real-time log streaming via Server-Sent Events (SSE)
- Execution history stored in SQLite database
- HTMX-powered seamless UI updates

## Database

The application uses SQLite to store execution history. The database file (`executor.db`) will be created in the same directory.

Table: `executions`
- `id` (Integer, Primary Key, Auto-increment): Unique identifier for the execution.
- `prompt` (Text): The prompt entered by the user.
- `model` (Text): The model name specified by the user.
- `status` (Text): Current status of the execution. Values: `running`, `success`, `error`.
- `created_at` (Datetime): Timestamp when the execution was initiated.

## API Endpoints

- `GET /`: Renders the main page with the form and history.
- `POST /execute`: Handles form submission, creates a new execution record, and returns the SSE connection trigger.
- `GET /stream/{execution_id}`: Provides Server-Sent Events for log streaming of a specific execution.

## Deployment

The application can be deployed using PM2 with the provided `ecosystem.config.json` file.

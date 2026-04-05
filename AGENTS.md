# Repository: openhands-v3

## Overview
This repository contains the `openhands-v3` project — a task execution platform with a FastHTML web UI and API.

## Project Structure
- `engine/`: Core logic — `runner.py` (TaskRunner), `config.py` (MCP config).
- `main.py`: Entry point — FastHTML app, routes, UI rendering. Still contains all original code; new modules below are extracted copies for future migration.
- `db/`: Database layer (extracted from main.py).
  - `db/queries.py`: All SQLite functions (`init_db`, `add_execution`, `update_execution_status`, `add_execution_turn`, `update_turn_status`, `get_executions`, `get_execution`, `get_execution_turns`). Uses `get_db()` context manager.
- `services/`: Business logic (extracted from main.py).
  - `services/execution.py`: Thread-safe execution state (`execution_queues`, `execution_inputs`, `execution_thoughts`, `turn_thoughts`), `ThreadSafeStdout`, `QueueWriter`, `start_execution_thread`.
- `plans/`: Architecture and improvement plans.
- `requirements.txt`: Project dependencies.
- `ecosystem.config.json`: PM2 configuration file.
- `executor.db`: SQLite database.

## Key Patterns
- Database functions use `with get_db() as conn:` context manager pattern (in `db/queries.py`).
- Execution threads use thread-local stdout via `ThreadSafeStdout` + `set_thread_writer`/`clear_thread_writer` (in `services/execution.py`).
- Global execution state is protected by `threading.Lock` (`_lock` in `services/execution.py`).

import sqlite3
import json
from contextlib import contextmanager

DB_FILE = "executor.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                model TEXT NOT NULL,
                workspace TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS execution_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id INTEGER,
                turn_number INTEGER,
                prompt TEXT NOT NULL,
                logs TEXT,
                agent_message TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                reasoning_tokens INTEGER,
                cache_read_tokens INTEGER,
                cache_write_tokens INTEGER,
                latency REAL,
                cost REAL,
                status TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (execution_id) REFERENCES executions(id)
            )
        ''')

        # Check if columns exist and add missing ones
        c.execute("PRAGMA table_info(execution_turns)")
        columns = [col[1] for col in c.fetchall()]
        if "agent_message" not in columns:
            c.execute("ALTER TABLE execution_turns ADD COLUMN agent_message TEXT")
        if "reasoning_tokens" not in columns:
            c.execute("ALTER TABLE execution_turns ADD COLUMN reasoning_tokens INTEGER")
        if "cache_read_tokens" not in columns:
            c.execute("ALTER TABLE execution_turns ADD COLUMN cache_read_tokens INTEGER")
        if "cache_write_tokens" not in columns:
            c.execute("ALTER TABLE execution_turns ADD COLUMN cache_write_tokens INTEGER")
        if "latency" not in columns:
            c.execute("ALTER TABLE execution_turns ADD COLUMN latency REAL")
        if "thoughts" not in columns:
            c.execute("ALTER TABLE execution_turns ADD COLUMN thoughts TEXT")

        conn.commit()


def add_execution(prompt, model, workspace):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO executions (prompt, model, workspace, status) VALUES (?, ?, ?, ?)",
            (prompt, model, workspace, "running")
        )
        exec_id = c.lastrowid
        conn.commit()
        return exec_id


def update_execution_status(exec_id, status):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE executions SET status = ? WHERE id = ?", (status, exec_id))
        conn.commit()


def add_execution_turn(exec_id, turn_number, prompt):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO execution_turns (execution_id, turn_number, prompt, status) VALUES (?, ?, ?, ?)",
            (exec_id, turn_number, prompt, "running")
        )
        turn_id = c.lastrowid
        conn.commit()
        return turn_id


def update_turn_status(turn_id, status, logs=None, prompt_tokens=None, completion_tokens=None, total_tokens=None, cost=None,
                       agent_message=None, reasoning_tokens=None, cache_read_tokens=None, cache_write_tokens=None, latency=None, thoughts=None):
    with get_db() as conn:
        c = conn.cursor()
        update_fields = ["status = ?"]
        params = [status]

        if logs is not None:
            update_fields.append("logs = ?")
            params.append(logs)
        if agent_message is not None:
            update_fields.append("agent_message = ?")
            params.append(agent_message)
        if thoughts is not None:
            update_fields.append("thoughts = ?")
            params.append(json.dumps(thoughts))
        if prompt_tokens is not None:
            update_fields.append("prompt_tokens = ?")
            params.append(prompt_tokens)
        if completion_tokens is not None:
            update_fields.append("completion_tokens = ?")
            params.append(completion_tokens)
        if total_tokens is not None:
            update_fields.append("total_tokens = ?")
            params.append(total_tokens)
        if reasoning_tokens is not None:
            update_fields.append("reasoning_tokens = ?")
            params.append(reasoning_tokens)
        if cache_read_tokens is not None:
            update_fields.append("cache_read_tokens = ?")
            params.append(cache_read_tokens)
        if cache_write_tokens is not None:
            update_fields.append("cache_write_tokens = ?")
            params.append(cache_write_tokens)
        if latency is not None:
            update_fields.append("latency = ?")
            params.append(latency)
        if cost is not None:
            update_fields.append("cost = ?")
            params.append(cost)

        params.append(turn_id)
        c.execute(f"UPDATE execution_turns SET {', '.join(update_fields)} WHERE id = ?", tuple(params))
        conn.commit()


def get_executions(page=1, page_size=10):
    offset = (page - 1) * page_size
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT e.id, e.prompt, e.model, e.workspace, e.status, e.created_at,
                   (SELECT COUNT(*) FROM execution_turns WHERE execution_id = e.id) as turns_count,
                   (SELECT SUM(total_tokens) FROM execution_turns WHERE execution_id = e.id) as total_tokens,
                   (SELECT SUM(cost) FROM execution_turns WHERE execution_id = e.id) as total_cost
            FROM executions e ORDER BY e.id DESC LIMIT ? OFFSET ?
            """,
            (page_size, offset)
        )
        rows = c.fetchall()
        c.execute("SELECT COUNT(*) FROM executions")
        total_count = c.fetchone()[0]

    return [
        {
            "id": r[0], "prompt": r[1], "model": r[2], "workspace": r[3], "status": r[4], "created_at": r[5],
            "turns_count": r[6] or 0, "total_tokens": r[7] or 0, "cost": r[8] or 0.0
        }
        for r in rows
    ], total_count


def get_execution(exec_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, prompt, model, workspace, status, created_at FROM executions WHERE id = ?", (exec_id,))
        row = c.fetchone()
        if not row:
            return None

        exec_data = {"id": row[0], "prompt": row[1], "model": row[2], "workspace": row[3], "status": row[4], "created_at": row[5]}

        c.execute("SELECT turn_number, prompt, logs, status, prompt_tokens, completion_tokens, total_tokens, cost, created_at, agent_message, thoughts FROM execution_turns WHERE execution_id = ? ORDER BY turn_number ASC", (exec_id,))
        turns = c.fetchall()
        exec_data["turns"] = [
            {
                "turn_number": t[0], "prompt": t[1], "logs": t[2], "status": t[3],
                "prompt_tokens": t[4] or 0, "completion_tokens": t[5] or 0, "total_tokens": t[6] or 0, "cost": t[7] or 0.0, "created_at": t[8],
                "agent_message": t[9], "thoughts": t[10]
            } for t in turns
        ]

        exec_data["total_tokens"] = sum(t["total_tokens"] for t in exec_data["turns"])
        exec_data["cost"] = sum(t["cost"] for t in exec_data["turns"])

    return exec_data


def get_execution_turns(exec_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT turn_number, prompt, logs, status, prompt_tokens, completion_tokens, total_tokens, cost, created_at,
                   agent_message, reasoning_tokens, cache_read_tokens, cache_write_tokens, latency, thoughts
            FROM execution_turns
            WHERE execution_id = ?
            ORDER BY created_at DESC
        """, (exec_id,))
        turns = c.fetchall()

    return [
        {
            "turn_number": t[0], "prompt": t[1], "logs": t[2], "status": t[3],
            "prompt_tokens": t[4] or 0, "completion_tokens": t[5] or 0, "total_tokens": t[6] or 0, "cost": t[7] or 0.0, "created_at": t[8],
            "agent_message": t[9], "reasoning_tokens": t[10] or 0, "cache_read_tokens": t[11] or 0, "cache_write_tokens": t[12] or 0, "latency": t[13] or 0.0, "thoughts": t[14]
        } for t in turns
    ]

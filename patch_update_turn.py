import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """def update_turn_status(turn_id, status, logs=None, prompt_tokens=None, completion_tokens=None, total_tokens=None, cost=None,
                       agent_message=None, reasoning_tokens=None, cache_read_tokens=None, cache_write_tokens=None, latency=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    update_fields = ["status = ?"]
    params = [status]

    if logs is not None:
        update_fields.append("logs = ?")
        params.append(logs)
    if agent_message is not None:
        update_fields.append("agent_message = ?")
        params.append(agent_message)"""

new_str = """def update_turn_status(turn_id, status, logs=None, prompt_tokens=None, completion_tokens=None, total_tokens=None, cost=None,
                       agent_message=None, reasoning_tokens=None, cache_read_tokens=None, cache_write_tokens=None, latency=None, thoughts=None):
    conn = sqlite3.connect(DB_FILE)
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
        params.append(thoughts)"""

content = content.replace(old_str, new_str)

with open('main.py', 'w') as f:
    f.write(content)

import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """    c.execute("SELECT turn_number, prompt, logs, status, prompt_tokens, completion_tokens, total_tokens, cost, created_at, agent_message FROM execution_turns WHERE execution_id = ? ORDER BY turn_number ASC", (exec_id,))
    turns = c.fetchall()
    exec_data["turns"] = [
        {
            "turn_number": t[0], "prompt": t[1], "logs": t[2], "status": t[3],
            "prompt_tokens": t[4] or 0, "completion_tokens": t[5] or 0, "total_tokens": t[6] or 0, "cost": t[7] or 0.0, "created_at": t[8],
            "agent_message": t[9]
        } for t in turns
    ]"""

new_str = """    c.execute("SELECT turn_number, prompt, logs, status, prompt_tokens, completion_tokens, total_tokens, cost, created_at, agent_message, thoughts FROM execution_turns WHERE execution_id = ? ORDER BY turn_number ASC", (exec_id,))
    turns = c.fetchall()
    exec_data["turns"] = [
        {
            "turn_number": t[0], "prompt": t[1], "logs": t[2], "status": t[3],
            "prompt_tokens": t[4] or 0, "completion_tokens": t[5] or 0, "total_tokens": t[6] or 0, "cost": t[7] or 0.0, "created_at": t[8],
            "agent_message": t[9], "thoughts": t[10]
        } for t in turns
    ]"""

content = content.replace(old_str, new_str)

with open('main.py', 'w') as f:
    f.write(content)

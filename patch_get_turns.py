import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """        SELECT turn_number, prompt, logs, status, prompt_tokens, completion_tokens, total_tokens, cost, created_at,
               agent_message, reasoning_tokens, cache_read_tokens, cache_write_tokens, latency
        FROM execution_turns"""

new_str = """        SELECT turn_number, prompt, logs, status, prompt_tokens, completion_tokens, total_tokens, cost, created_at,
               agent_message, reasoning_tokens, cache_read_tokens, cache_write_tokens, latency, thoughts
        FROM execution_turns"""

content = content.replace(old_str, new_str)

old_str2 = """            "agent_message": t[9], "reasoning_tokens": t[10] or 0, "cache_read_tokens": t[11] or 0, "cache_write_tokens": t[12] or 0, "latency": t[13] or 0.0
        } for t in turns"""

new_str2 = """            "agent_message": t[9], "reasoning_tokens": t[10] or 0, "cache_read_tokens": t[11] or 0, "cache_write_tokens": t[12] or 0, "latency": t[13] or 0.0, "thoughts": t[14]
        } for t in turns"""

content = content.replace(old_str2, new_str2)

with open('main.py', 'w') as f:
    f.write(content)

import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """    if "latency" not in columns:
        c.execute("ALTER TABLE execution_turns ADD COLUMN latency REAL")"""

new_str = """    if "latency" not in columns:
        c.execute("ALTER TABLE execution_turns ADD COLUMN latency REAL")
    if "thoughts" not in columns:
        c.execute("ALTER TABLE execution_turns ADD COLUMN thoughts TEXT")"""

content = content.replace(old_str, new_str)

with open('main.py', 'w') as f:
    f.write(content)

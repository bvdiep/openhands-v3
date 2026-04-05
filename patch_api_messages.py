import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """    messages = []
    for t in exec_data["turns"]:
        if t.get("agent_message"):
            messages.append({
                "turn_number": t["turn_number"],
                "role": "agent",
                "content": t["agent_message"],
                "timestamp": t["created_at"]
            })"""

new_str = """    import json
    messages = []
    for t in exec_data["turns"]:
        if t.get("agent_message"):
            msg = {
                "turn_number": t["turn_number"],
                "role": "agent",
                "content": t["agent_message"],
                "timestamp": t["created_at"]
            }
            if t.get("thoughts"):
                try:
                    msg["thoughts"] = json.loads(t["thoughts"])
                except:
                    msg["thoughts"] = []
            messages.append(msg)"""

content = content.replace(old_str, new_str)

with open('main.py', 'w') as f:
    f.write(content)

import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """            Div(t["agent_message"] or "No message", cls="markdown-content"),
            Details(
                Summary("📜 View Logs", style="color: #007acc; text-decoration: underline;"),
                Pre(t["logs"] or "No logs", cls="terminal", style="max-height: 250px; overflow-y: auto;"),
                cls="log-accordion"
            ),"""

new_str = """            Div(t["agent_message"] or "No message", cls="markdown-content"),
            Details(
                Summary("🧠 View Thoughts", style="color: #007acc; text-decoration: underline; margin-top: 0.5rem;"),
                Pre(t.get("thoughts") or "No thoughts recorded", style="white-space: pre-wrap; background: #f9f9f9; padding: 10px; border: 1px solid #eee; max-height: 200px; overflow-y: auto; font-style: italic;"),
                cls="thought-accordion"
            ),
            Details(
                Summary("📜 View Logs", style="color: #007acc; text-decoration: underline; margin-top: 0.5rem;"),
                Pre(t["logs"] or "No logs", cls="terminal", style="max-height: 250px; overflow-y: auto;"),
                cls="log-accordion"
            ),"""

content = content.replace(old_str, new_str)

with open('main.py', 'w') as f:
    f.write(content)

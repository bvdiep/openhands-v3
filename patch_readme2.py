import re

with open('README.md', 'r') as f:
    content = f.read()

old_str = """- HTMX-powered seamless UI updates
- Conversation & Thinking Process Visualization"""

new_str = """- HTMX-powered seamless UI updates
- Conversation & Thinking Process Visualization
- Real-time Agent Thinking Status
- Historical Chain of Thought Storage"""

content = content.replace(old_str, new_str)

with open('README.md', 'w') as f:
    f.write(content)

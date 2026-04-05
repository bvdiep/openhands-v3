import re

with open('README.md', 'r') as f:
    content = f.read()

old_str = """## Features

- Form with prompt textarea and model input
- Real-time log streaming via Server-Sent Events (SSE)
- Execution history stored in SQLite database
- HTMX-powered seamless UI updates"""

new_str = """## Features

- Form with prompt textarea and model input
- Real-time log streaming via Server-Sent Events (SSE)
- Execution history stored in SQLite database
- HTMX-powered seamless UI updates
- Conversation & Thinking Process Visualization"""

content = content.replace(old_str, new_str)

with open('README.md', 'w') as f:
    f.write(content)

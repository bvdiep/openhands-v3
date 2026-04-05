import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """        if t.get("agent_message"):
            conversation_history.append(
                Div(
                    Span("🤖 Agent: ", style="font-weight: bold;"),
                    Div(t["agent_message"], cls="markdown-content"),
                    cls="agent-message",
                    style="background: #e3f2fd; padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2196f3;"
                )
            )"""

new_str = """        if t.get("thoughts"):
            import json
            try:
                thoughts_list = json.loads(t["thoughts"])
                for thought in thoughts_list:
                    conversation_history.append(
                        Div(
                            Span("🧠 Thinking: ", style="font-weight: bold; color: #007bff;"),
                            Span(thought, style="font-style: italic;"),
                            style="background: #f8f9fa; padding: 8px; border-radius: 8px; margin-bottom: 5px; border-left: 4px solid #007bff; font-size: 0.9em;"
                        )
                    )
            except:
                pass
        if t.get("agent_message"):
            conversation_history.append(
                Div(
                    Span("🤖 Agent: ", style="font-weight: bold;"),
                    Div(t["agent_message"], cls="markdown-content"),
                    cls="agent-message",
                    style="background: #e3f2fd; padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2196f3;"
                )
            )"""

content = content.replace(old_str, new_str)

with open('main.py', 'w') as f:
    f.write(content)

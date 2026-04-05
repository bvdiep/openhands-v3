import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """    # Render all logs from all turns
    all_logs = []
    for t in exec_data["turns"]:
        all_logs.append(f"> User [Turn {t['turn_number']}]: {t['prompt']}")
        all_logs.append(t['logs'] or "No logs available")
    full_log_text = "\\n\\n".join(all_logs)

    if exec_data["status"] in ["running", "waiting_for_input"]:
        # Tái hiện màn hình Live Terminal nếu phiên làm việc vẫn còn Active
        is_waiting = (exec_data["status"] == "waiting_for_input")
        return Dialog(
            Article(
                Header(
                    Button(aria_label="Close", cls="close", onclick="this.closest('dialog').removeAttribute('open')"),
                    P(Strong(f"Execution #{exec_id} is {exec_data['status']}"))
                ),
                Div(
                    P(Strong("Prompt History:")),
                    Div(*prompt_history, style="max-height: 200px; overflow-y: auto; margin-bottom: 20px; border: 1px solid #ccc; padding: 10px;"),
                    P(Strong("Conversation Flow:")),
                    Div(id=f"conversation-flow-{exec_id}", cls="conversation-flow", style="margin-bottom: 1rem; max-height: 200px; overflow-y: auto; padding: 10px; background: #f9f9f9; border-radius: 8px;"),
                    P(Strong("Live Logs:")),
                    Div(full_log_text, id=f"terminal-output-{exec_id}", cls="terminal", style="white-space: pre-wrap; height: 300px;"),
                ),"""

new_str = """    # Render all logs from all turns
    all_logs = []
    conversation_history = []
    for t in exec_data["turns"]:
        all_logs.append(f"> User [Turn {t['turn_number']}]: {t['prompt']}")
        all_logs.append(t['logs'] or "No logs available")
        if t.get("agent_message"):
            conversation_history.append(
                Div(
                    Span("🤖 Agent: ", style="font-weight: bold;"),
                    Div(t["agent_message"], cls="markdown-content"),
                    cls="agent-message",
                    style="background: #e3f2fd; padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2196f3;"
                )
            )
    full_log_text = "\\n\\n".join(all_logs)

    if exec_data["status"] in ["running", "waiting_for_input"]:
        # Tái hiện màn hình Live Terminal nếu phiên làm việc vẫn còn Active
        is_waiting = (exec_data["status"] == "waiting_for_input")
        return Dialog(
            Article(
                Header(
                    Button(aria_label="Close", cls="close", onclick="this.closest('dialog').removeAttribute('open')"),
                    P(Strong(f"Execution #{exec_id} is {exec_data['status']}"))
                ),
                Div(
                    P(Strong("Prompt History:")),
                    Div(*prompt_history, style="max-height: 200px; overflow-y: auto; margin-bottom: 20px; border: 1px solid #ccc; padding: 10px;"),
                    P(Strong("Conversation Flow:")),
                    Div(*conversation_history, id=f"conversation-flow-{exec_id}", cls="conversation-flow", style="margin-bottom: 1rem; max-height: 200px; overflow-y: auto; padding: 10px; background: #f9f9f9; border-radius: 8px;"),
                    P(Strong("Live Logs:")),
                    Div(full_log_text, id=f"terminal-output-{exec_id}", cls="terminal", style="white-space: pre-wrap; height: 300px;"),
                ),"""

content = content.replace(old_str, new_str)

with open('main.py', 'w') as f:
    f.write(content)

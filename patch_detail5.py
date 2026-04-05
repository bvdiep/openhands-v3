import re

with open('main.py', 'r') as f:
    lines = f.readlines()

start_idx = -1
for i, line in enumerate(lines):
    if "all_logs = []" in line and "for t in exec_data[\"turns\"]:" in lines[i+1]:
        start_idx = i
        break

if start_idx != -1:
    end_idx = start_idx
    for i in range(start_idx, len(lines)):
        if "Div(full_log_text, id=f\"terminal-output-{exec_id}\", cls=\"terminal\", style=\"white-space: pre-wrap; height: 300px;\")," in lines[i]:
            end_idx = i
            break
    
    new_lines = """    # Render all logs from all turns
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
"""
    
    lines = lines[:start_idx] + [new_lines] + lines[end_idx+1:]
    
    with open('main.py', 'w') as f:
        f.writelines(lines)

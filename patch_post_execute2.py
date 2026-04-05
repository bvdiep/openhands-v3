import re

with open('main.py', 'r') as f:
    lines = f.readlines()

start_idx = -1
for i, line in enumerate(lines):
    if "    return Div(" in line and "H4(f\"Execution #{exec_id} started\")," in lines[i+1]:
        start_idx = i
        break

if start_idx != -1:
    end_idx = start_idx
    for i in range(start_idx, len(lines)):
        if "source.onmessage = function(event) {" in lines[i]:
            end_idx = i
            break
    
    new_lines = """    return Div(
        H4(f"Execution #{exec_id} started"),
        Div(id=f"conversation-flow-{exec_id}", cls="conversation-flow", style="margin-bottom: 1rem; max-height: 300px; overflow-y: auto; padding: 10px; background: #f9f9f9; border-radius: 8px;"),
        Div(id=f"terminal-output-{exec_id}", cls="terminal", style="height: 300px;"),
        Script(f\"\"\"
            (function() {{
                const term = document.getElementById('terminal-output-{exec_id}');
                const convFlow = document.getElementById('conversation-flow-{exec_id}');
                const btn = document.querySelector('.button-execute');
                const promptArea = document.getElementById('prompt');
                const taskForm = document.getElementById('task-form');

                if (btn) {{ btn.classList.add('is-loading'); btn.disabled = true; }}

                const source = new EventSource('/stream/{exec_id}');
                
                source.addEventListener('agent_message', function(event) {{
                    const data = JSON.parse(event.data);
                    const msgDiv = document.createElement('div');
                    msgDiv.className = 'agent-message';
                    msgDiv.style.cssText = 'background: #e3f2fd; padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2196f3;';

                    const iconSpan = document.createElement('span');
                    iconSpan.textContent = '🤖 Agent: ';
                    iconSpan.style.fontWeight = 'bold';

                    const contentDiv = document.createElement('div');
                    if (typeof marked !== 'undefined') {{
                        contentDiv.innerHTML = marked.parse(data.content);
                    }} else {{
                        contentDiv.textContent = data.content;
                    }}

                    msgDiv.appendChild(iconSpan);
                    msgDiv.appendChild(contentDiv);
                    convFlow.appendChild(msgDiv);
                    convFlow.scrollTop = convFlow.scrollHeight;
                }});

                source.onmessage = function(event) {{
"""
    
    lines = lines[:start_idx] + [new_lines] + lines[end_idx+1:]
    
    with open('main.py', 'w') as f:
        f.writelines(lines)

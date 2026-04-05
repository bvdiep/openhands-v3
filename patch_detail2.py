import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """                Div(
                    P(Strong("Prompt History:")),
                    Div(*prompt_history, style="max-height: 200px; overflow-y: auto; margin-bottom: 20px; border: 1px solid #ccc; padding: 10px;"),
                    P(Strong("Live Logs:")),
                    Div(full_log_text, id=f"terminal-output-{exec_id}", cls="terminal", style="white-space: pre-wrap; height: 300px;"),
                ),
                Script(f\"\"\"
                    (function() {{
                        const term = document.getElementById('terminal-output-{exec_id}');
                        term.scrollTop = term.scrollHeight;
                        const source = new EventSource('/stream/{exec_id}');
                        source.onmessage = function(event) {{
                            const data = event.data;
                            term.textContent += data + '\\n';
                            term.scrollTop = term.scrollHeight;
                        }};
                        source.onerror = function(event) {{
                            source.close();
                        }};
                    }})();
                \"\"\")"""

new_str = """                Div(
                    P(Strong("Prompt History:")),
                    Div(*prompt_history, style="max-height: 200px; overflow-y: auto; margin-bottom: 20px; border: 1px solid #ccc; padding: 10px;"),
                    P(Strong("Conversation Flow:")),
                    Div(id=f"conversation-flow-{exec_id}", cls="conversation-flow", style="margin-bottom: 1rem; max-height: 200px; overflow-y: auto; padding: 10px; background: #f9f9f9; border-radius: 8px;"),
                    P(Strong("Live Logs:")),
                    Div(full_log_text, id=f"terminal-output-{exec_id}", cls="terminal", style="white-space: pre-wrap; height: 300px;"),
                ),
                Script(f\"\"\"
                    (function() {{
                        const term = document.getElementById('terminal-output-{exec_id}');
                        const convFlow = document.getElementById('conversation-flow-{exec_id}');
                        term.scrollTop = term.scrollHeight;
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
                            const data = event.data;
                            term.textContent += data + '\\n';
                            term.scrollTop = term.scrollHeight;
                        }};
                        source.onerror = function(event) {{
                            source.close();
                        }};
                    }})();
                \"\"\")"""

content = content.replace(old_str, new_str)

with open('main.py', 'w') as f:
    f.write(content)

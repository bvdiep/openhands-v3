import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """                Button(
                    Div(Span(cls="spinner"), "Execute", cls="loading-indicator"),
                    Span("Execute", cls="normal-text"),
                    type="submit", hx_post="/execute", hx_target="#loading-indicator", hx_swap="none", cls="button-execute", disabled=True
                ),
                A("Conversation", id="conversation-link", cls="conversation-link", href="#",
                  hx_get="/conversation", hx_target="#modal-placeholder",
                  hx_trigger="click",
                  onclick="const execId = document.getElementById('task-form').dataset.activeExecId; if(!execId) { alert('No active execution'); return false; } this.setAttribute('hx-get', '/conversation/' + execId); htmx.process(this);",
                  style="display: none; margin-left: 1rem;"),"""

new_str = """                Button(
                    Div(Span(cls="spinner"), "Execute", cls="loading-indicator"),
                    Span("Execute", cls="normal-text"),
                    type="submit", hx_post="/execute", hx_target="#loading-indicator", hx_swap="none", cls="button-execute", disabled=True
                ),
                A("Conversation", id="conversation-link", cls="conversation-link", href="#",
                  hx_get="/conversation", hx_target="#modal-placeholder",
                  hx_trigger="click",
                  onclick="const execId = document.getElementById('task-form').dataset.activeExecId; if(!execId) { alert('No active execution'); return false; } this.setAttribute('hx-get', '/conversation/' + execId); htmx.process(this);",
                  style="display: none; margin-left: 1rem;"),
                Span(id="live-thought-indicator", style="display: none; margin-left: 1rem; font-style: italic; color: #007bff; font-size: 0.9em;"),"""

content = content.replace(old_str, new_str)

old_str2 = """                const evtSource = new EventSource('/stream/{exec_id}');
                evtSource.onmessage = function(e) {
                    const data = JSON.parse(e.data);
                    if (data.event === 'log') {
                        term.innerHTML += data.data.content;
                        term.scrollTop = term.scrollHeight;
                    } else if (data.event === 'agent_message') {
                        const msgDiv = document.createElement('div');
                        msgDiv.className = 'chat-bubble agent-message';
                        msgDiv.innerHTML = marked.parse(data.data.content);
                        convFlow.appendChild(msgDiv);
                        convFlow.scrollTop = convFlow.scrollHeight;
                    } else if (data.event === 'status') {
                        if (data.data.status === 'success' || data.data.status === 'error' || data.data.status === 'waiting_for_input') {
                            evtSource.close();
                            if (btn) { btn.classList.remove('is-loading'); btn.disabled = false; }
                            if (promptArea) { promptArea.value = ''; }
                            htmx.ajax('GET', '/history', '#history-container');
                        }
                    }
                };"""

new_str2 = """                const evtSource = new EventSource('/stream/{exec_id}');
                const thoughtIndicator = document.getElementById('live-thought-indicator');
                evtSource.onmessage = function(e) {
                    const data = JSON.parse(e.data);
                    if (data.event === 'log') {
                        term.innerHTML += data.data.content;
                        term.scrollTop = term.scrollHeight;
                    } else if (data.event === 'agent_thought') {
                        if (thoughtIndicator) {
                            thoughtIndicator.style.display = 'inline-block';
                            thoughtIndicator.innerHTML = '<span class="spinner" style="width: 1rem; height: 1rem; border-top-color: #007bff; margin-right: 0.5rem;"></span>' + data.data.content;
                        }
                    } else if (data.event === 'agent_message') {
                        const msgDiv = document.createElement('div');
                        msgDiv.className = 'chat-bubble agent-message';
                        msgDiv.innerHTML = marked.parse(data.data.content);
                        convFlow.appendChild(msgDiv);
                        convFlow.scrollTop = convFlow.scrollHeight;
                        if (thoughtIndicator) {
                            thoughtIndicator.style.display = 'none';
                            thoughtIndicator.innerHTML = '';
                        }
                    } else if (data.event === 'status') {
                        if (data.data.status === 'success' || data.data.status === 'error' || data.data.status === 'waiting_for_input') {
                            evtSource.close();
                            if (btn) { btn.classList.remove('is-loading'); btn.disabled = false; }
                            if (promptArea) { promptArea.value = ''; }
                            if (thoughtIndicator) {
                                thoughtIndicator.style.display = 'none';
                                thoughtIndicator.innerHTML = '';
                            }
                            htmx.ajax('GET', '/history', '#history-container');
                        }
                    }
                };"""

content = content.replace(old_str2, new_str2)

with open('main.py', 'w') as f:
    f.write(content)

import asyncio
import json
import queue as queue_module

from fasthtml.common import (
    Titled, Div, H3, H4, A, P, Pre, Form, Grid, Label, Select, Option,
    Input, Textarea, Button, Span, Small, Strong, Em, Article, Script,
    Details, Summary, Header, Footer, Dialog, Grid,
)

from db.queries import (
    add_execution, get_executions, get_execution, get_execution_turns,
)
from engine.config import AVAILABLE_MCP_SERVERS, get_mcp_config
from services.execution import (
    execution_inputs,
    register_execution,
    start_execution_thread,
)
from services.skills import get_public_skills, get_user_skills, skill_trigger_label


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

MODELS = [
    "gemini/gemini-3-flash-preview",
    "gemini/gemma-4-31b-it",
    "litellm/nvidia-minimax-m2.7",
    "litellm/nvidia-glm-4.7",
    "litellm/GLM-5",
    "litellm/sonnet-4.5",
    "litellm/fpt-ai-nemotron-3-super",
    "litellm/nvidia-step-3.5-flash",
    "litellm/nvidia-phi4-multimodal",
]


def _render_history(page=1):
    page_size = 10
    executions, total_count = get_executions(page, page_size)
    total_pages = (total_count + page_size - 1) // page_size

    pagination_controls = []
    if total_pages > 1:
        if page > 1:
            pagination_controls.append(
                Button("Prev", hx_get=f"/history?page={page-1}", hx_target="#history-container", cls="outline small")
            )
        pagination_controls.append(Span(f"Page {page} of {total_pages}"))
        if page < total_pages:
            pagination_controls.append(
                Button("Next", hx_get=f"/history?page={page+1}", hx_target="#history-container", cls="outline small")
            )

    cards = [
        Article(
            Div(
                Div(
                    A(f"Execution #{exc['id']}", hx_get=f"/conversation/{exc['id']}", hx_target="#modal-placeholder", style="font-weight: bold; font-size: 1.1rem;"),
                    cls="card-header",
                ),
                Div(
                    P(Strong("Prompt: "), Span(exc["prompt"][:200] + ("..." if len(exc["prompt"]) > 200 else ""))),
                    Div(
                        Div(Small("Model: "), Strong(exc["model"])),
                        Div(Small("Workspace: "), Span(exc["workspace"])),
                        Div(Small("Turns: "), Span(str(exc["turns_count"]))),
                        Div(Small("Usage: "), Span(f"{exc['total_tokens']} tokens / ${exc['cost']:.4f}")),
                        cls="card-grid",
                    ),
                    cls="card-body",
                ),
                Div(
                    Small(exc["created_at"], style="color: #999;"),
                    A(
                        "Copy", href="#",
                        onclick=f"resumeTask({json.dumps(exc['prompt'])}, {json.dumps(exc['model'])}, {json.dumps(exc['workspace'])}); return false;",
                        style="font-size: 0.9rem; text-decoration: underline;",
                    ),
                    cls="card-footer",
                ),
            ),
            cls="execution-card",
        )
        for exc in executions
    ] if executions else [P("No executions yet")]

    return Div(
        H3("Execution History"),
        Div(*cards, cls="history-cards"),
        Div(*pagination_controls, cls="pagination-container"),
    )


def _sse_live_script(exec_id: int) -> str:
    """Return the JS that connects an EventSource for a live execution."""
    return f"""
    (function() {{
        const term = document.getElementById('terminal-output-{exec_id}');
        const convFlow = document.getElementById('conversation-flow-{exec_id}');
        const btn = document.querySelector('.button-execute');
        const promptArea = document.getElementById('prompt');
        const taskForm = document.getElementById('task-form');

        function setOptionsLocked(locked) {{
            document.querySelectorAll('.options-section').forEach(function(sec) {{
                sec.classList.toggle('options-locked', locked);
                sec.querySelectorAll('input, select').forEach(function(el) {{ el.disabled = locked; }});
            }});
        }}

        if (btn) {{ btn.classList.add('is-loading'); btn.disabled = true; }}
        setOptionsLocked(true);

        const source = new EventSource('/stream/{exec_id}');

        source.addEventListener('agent_thought', function(event) {{
            const data = JSON.parse(event.data);
            const indicator = document.getElementById('live-thought-indicator');
            if (indicator) {{
                indicator.textContent = '\U0001f914 ' + data.summary + ': ' + data.step + '...';
            }}
        }});

        source.addEventListener('agent_message', function(event) {{
            const data = JSON.parse(event.data);
            const indicator = document.getElementById('live-thought-indicator');
            if (indicator) {{ indicator.textContent = ''; }}
            const msgDiv = document.createElement('div');
            msgDiv.className = 'agent-message';
            msgDiv.style.cssText = 'background: #e3f2fd; padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2196f3;';

            const iconSpan = document.createElement('span');
            iconSpan.textContent = '🤖 Agent: ';
            iconSpan.style.fontWeight = 'bold';

            const contentDiv = document.createElement('div');
            if (typeof marked !== 'undefined') {{
                contentDiv.innerHTML = renderMarkdownSafe(data.content);
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

            if (data.includes('[System: G\\u00f5 l\\u1ec7nh ti\\u1ebfp theo')) {{
                if (btn) {{
                    btn.classList.remove('is-loading');
                    btn.disabled = true;
                }}
                if (promptArea) {{
                    promptArea.value = '';
                    promptArea.placeholder = 'G\\u00f5 y\\u00eau c\\u1ea7u ti\\u1ebfp theo...';
                    let inputExec = taskForm.querySelector('input[name="exec_id"]');
                    if(!inputExec) {{
                        inputExec = document.createElement('input');
                        inputExec.type = 'hidden';
                        inputExec.name = 'exec_id';
                        inputExec.value = '{exec_id}';
                        taskForm.appendChild(inputExec);
                    }}
                }}
            }}
            else if (data.includes('> User:')) {{
                if (btn) {{ btn.classList.add('is-loading'); btn.disabled = true; }}
            }}
        }};
        source.onerror = function(event) {{
            source.close();
            if (btn) {{
                btn.classList.remove('is-loading');
                if(promptArea && promptArea.value.trim()) btn.disabled = false; else if(btn) btn.disabled = true;
            }}
            if(taskForm) {{
                let inputExec = taskForm.querySelector('input[name="exec_id"]');
                if(inputExec) inputExec.remove();
            }}
            if(promptArea) promptArea.placeholder = '';
            setOptionsLocked(false);
        }};
    }})();
    """


def _sse_detail_script(exec_id: int) -> str:
    """Return the JS for the live terminal inside execution-detail modal."""
    return f"""
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
                contentDiv.innerHTML = renderMarkdownSafe(data.content);
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
    """


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

def register(app, rt):  # noqa: C901  (complex but faithful port)
    @rt("/")
    def get_index(session):
        return Titled(
            "Task Runner",
            Div(
                A("Logout", href="/logout", style="float: right"),
                Form(
                    H3("Execute Task"),
                    Grid(
                        Div(
                            Label("Model:", fr="model"),
                            Select(*[Option(m, value=m) for m in MODELS], name="model", id="model", required=True),
                        ),
                        Div(
                            Label("Working Directory:", fr="workspace"),
                            Input(type="text", name="workspace", id="workspace", required=True, value="."),
                        ),
                    ),
                    Div(
                        H4("Skills:"),
                        Grid(
                            Div(
                                Label(
                                    Input(type="checkbox", name="skill_opts", value="public", id="skill-public", checked=True),
                                    Span(" Public Skills"),
                                ),
                                A("ⓘ", href="#", title="View public skills",
                                  hx_get="/skills/public", hx_target="#modal-placeholder", hx_trigger="click",
                                  cls="info-icon"),
                                cls="option-with-info",
                            ),
                            Div(
                                Label(
                                    Input(type="checkbox", name="skill_opts", value="user", id="skill-user", checked=True),
                                    Span(" User Skills"),
                                ),
                                A("ⓘ", href="#", title="View user skills",
                                  hx_get="/skills/user", hx_target="#modal-placeholder", hx_trigger="click",
                                  cls="info-icon"),
                                cls="option-with-info",
                            ),
                        ),
                        cls="options-section",
                    ),
                    Div(
                        H4("Select MCP Servers:"),
                        Grid(
                            *[
                                Div(
                                    Label(
                                        Input(type="checkbox", name="mcp_ids", value=m_id, id=f"mcp-{m_id}"),
                                        Span(f" {m_info['name']}"),
                                        title=m_info["description"],
                                    ),
                                    style="margin-bottom: 0.5rem;",
                                )
                                for m_id, m_info in AVAILABLE_MCP_SERVERS.items()
                            ]
                        ),
                        cls="options-section",
                    ),
                    Label("Prompt:", fr="prompt"),
                    Textarea(
                        name="prompt", id="prompt", rows=4, required=True,
                        oninput="const btn = document.querySelector('.button-execute'); if(this.value.trim()){ btn.disabled = false; } else { btn.disabled = true; }",
                    ),
                    Div(
                        Button(
                            Div(Span(cls="spinner"), "Execute", cls="loading-indicator"),
                            Span("Execute", cls="normal-text"),
                            type="submit", hx_post="/execute", hx_target="#loading-indicator", hx_swap="none",
                            cls="button-execute", disabled=True,
                        ),
                        A(
                            "Conversation", id="conversation-link", cls="conversation-link", href="#",
                            hx_get="/conversation", hx_target="#modal-placeholder", hx_trigger="click",
                            onclick="const execId = document.getElementById('task-form').dataset.activeExecId; if(!execId) { alert('No active execution'); return false; } this.setAttribute('hx-get', '/conversation/' + execId); htmx.process(this);",
                            style="display:none",
                        ),
                        Span(id="live-thought-indicator"),
                        cls="execute-row",
                    ),
                    id="task-form",
                    hx_on__after_request="""
                        if(event.detail.successful) {
                            const execId = event.detail.xhr.responseText.match(/execution-(\\d+)/)?.[1];
                            if(execId) {
                                this.dataset.activeExecId = execId;
                                const convLink = document.getElementById('conversation-link');
                                convLink.style.display = 'inline-block';
                                convLink.innerText = 'Conversation #' + execId;
                            }
                        }
                    """,
                ),
                Div(Span("Loading...", cls="loading-indicator"), id="loading-indicator"),
                Div(id="executions-container"),
                Div(id="modal-placeholder"),
                Div(_render_history(1), id="history-container"),
            ),
        )

    @rt("/history")
    def get_history(page: int = 1):
        return _render_history(page)

    def _render_skills_modal(skills, title):
        skill_items = []
        for s in skills:
            label_text, badge_cls = skill_trigger_label(s)
            skill_items.append(
                Div(
                    Div(
                        Strong(s.name),
                        Span(label_text, cls=f"skill-badge {badge_cls}"),
                        cls="skill-item-header",
                    ),
                    P(s.description or "No description", cls="skill-item-desc"),
                    cls="skill-item",
                )
            )
        if not skill_items:
            skill_items = [P("No skills found.", style="color: #999; text-align: center; padding: 2rem 0;")]
        return Dialog(
            Article(
                Header(
                    Button(aria_label="Close", cls="close", onclick="this.closest('dialog').removeAttribute('open')"),
                    P(Strong(f"🧩 {title} ({len(skills)})")),
                ),
                Div(*skill_items, cls="skills-list"),
                Footer(
                    Button("Close", onclick="this.closest('dialog').removeAttribute('open')", cls="outline"),
                ),
            ),
            open=True, id="skills-modal",
        )

    @rt("/skills/public")
    def get_public_skills_modal():
        return _render_skills_modal(get_public_skills(), "Public Skills")

    @rt("/skills/user")
    def get_user_skills_modal():
        return _render_skills_modal(get_user_skills(), "User Skills")

    @rt("/execute")
    async def post_execute(request):
        form = await request.form()
        prompt = form.get("prompt", "").strip()
        model = form.get("model", "").strip()
        workspace = form.get("workspace", "").strip()
        exec_id_active = form.get("exec_id", "").strip()
        selected_mcp_ids = form.getlist("mcp_ids")
        mcp_config = get_mcp_config(selected_mcp_ids)
        skill_opts = form.getlist("skill_opts")

        if exec_id_active and exec_id_active.isdigit():
            exec_id = int(exec_id_active)
            in_q = execution_inputs.get(exec_id)
            if prompt and in_q:
                in_q.put(prompt)
            return ""

        if not prompt or not model or not workspace:
            return Div("Prompt, model, and workspace are required", cls="error")

        exec_id = add_execution(prompt, model, workspace)

        loop = asyncio.get_running_loop()
        q = asyncio.Queue()
        in_q = queue_module.Queue()
        register_execution(exec_id, q, in_q)

        start_execution_thread(
            exec_id, prompt, model, workspace, mcp_config, loop, q, in_q,
            load_public_skills="public" in skill_opts,
            load_user_skills="user" in skill_opts,
        )

        return Div(
            H4(f"Execution #{exec_id} started"),
            Div(id=f"conversation-flow-{exec_id}", cls="conversation-flow",
                style="margin-bottom: 1rem; overflow-y: auto; padding: 10px; background: #f9f9f9; border-radius: 8px;"),
            Div(id=f"terminal-output-{exec_id}", cls="terminal", style="height: 300px;"),
            Script(_sse_live_script(exec_id)),
            id=f"execution-{exec_id}",
            hx_swap_oob="afterbegin:#executions-container",
        )

    @rt("/execute/{exec_id}/message")
    async def post_message(exec_id: int, request):
        form = await request.form()
        prompt = form.get("prompt", "").strip()
        in_q = execution_inputs.get(exec_id)
        if prompt and in_q:
            in_q.put(prompt)
        return ""

    @rt("/execute/{exec_id}/stop")
    def post_stop(exec_id: int):
        in_q = execution_inputs.get(exec_id)
        if in_q:
            in_q.put("__STOP__")
        return ""

    @rt("/conversation/{exec_id}")
    def get_conversation(exec_id: int):
        turns = get_execution_turns(exec_id)

        turn_elements = []
        for t in turns:
            metrics_badges = [
                Span(f"Tokens: {t['total_tokens']} (P: {t['prompt_tokens']}, C: {t['completion_tokens']})", cls="metric-badge"),
                Span(f"Reasoning: {t['reasoning_tokens']}", cls="metric-badge"),
                Span(f"Cache: R {t['cache_read_tokens']}, W {t['cache_write_tokens']}", cls="metric-badge"),
                Span(f"Latency: {t['latency']:.2f}s", cls="metric-badge"),
                Span(f"Cost: ${t['cost']:.4f}", cls="metric-badge"),
                Span(f"Status: {t['status']}", cls=f"metric-badge status-{t['status']}"),
            ]

            thoughts_elements = []
            if t.get("thoughts"):
                try:
                    thoughts_data = json.loads(t["thoughts"])
                    if isinstance(thoughts_data, list):
                        for idx, step in enumerate(thoughts_data):
                            thoughts_elements.append(Div(
                                Div(
                                    Strong(f"Step {idx+1}: {step.get('step', 'Action')}"),
                                    Span(f" ({step.get('timestamp', '')})", style="color: #999; font-size: 0.8em;"),
                                    style="margin-bottom: 0.2rem;",
                                ),
                                Div(Em(step.get("summary", "")), style="color: #555; margin-bottom: 0.3rem;"),
                                Details(
                                    Summary("View Reasoning Details", style="font-size: 0.85em; color: #007acc; cursor: pointer;"),
                                    Pre(step.get("reasoning", ""), style="white-space: pre-wrap; background: #fff; padding: 5px; border: 1px solid #ddd; margin-top: 5px; font-size: 0.9em;"),
                                    style="margin-left: 10px;",
                                ),
                                style="border-bottom: 1px solid #eee; padding: 10px; margin-bottom: 10px; background: #fff; border-radius: 4px;",
                            ))
                    else:
                        thoughts_elements.append(Pre(str(thoughts_data)))
                except Exception as e:
                    thoughts_elements.append(Pre(f"Error parsing thoughts: {e}"))
            else:
                thoughts_elements.append(P("No thoughts recorded"))

            turn_elements.append(Div(
                Div(
                    H4(f"Turn {t['turn_number']}", style="margin:0;"),
                    Div(*metrics_badges, cls="turn-metrics"),
                    Small(t["created_at"], style="color: #999;"),
                    cls="turn-header",
                ),
                Pre(t["prompt"], style="white-space: pre-wrap; background: #f0f0f0; padding: 10px; border-radius: 4px;"),
                Div(t["agent_message"] or "No message", cls="markdown-content"),
                Details(
                    Summary("\U0001f9e0 View Chain of Thought", style="color: #007acc; text-decoration: underline; margin-top: 0.5rem;"),
                    Div(*thoughts_elements, style="background: #f1f1f1; padding: 10px; border: 1px solid #eee; max-height: 400px; overflow-y: auto;"),
                    cls="thought-accordion",
                ),
                Details(
                    Summary("\U0001f4dc View Logs", style="color: #007acc; text-decoration: underline; margin-top: 0.5rem;"),
                    Pre(t["logs"] or "No logs", cls="terminal", style="max-height: 250px; overflow-y: auto;"),
                    cls="log-accordion",
                ),
                style="margin-bottom: 1rem; padding-bottom: 1rem;",
            ))

        return Dialog(
            Article(
                Header(
                    Button(aria_label="Close", cls="close", onclick="this.closest('dialog').removeAttribute('open')"),
                    P(Strong(f"Conversation #{exec_id}")),
                ),
                Div(*turn_elements, id="conversation-content", style="overflow-y: auto; max-height: calc(90vh - 150px);"),
                Script("""
                    document.querySelectorAll('.markdown-content').forEach(function(el) {
                        if (!el.dataset.rendered) {
                            el.innerHTML = renderMarkdownSafe(el.textContent || el.innerText);
                            el.dataset.rendered = "true";
                        }
                    });
                """),
            ),
            open=True, id="conversation-modal",
        )

    @rt("/execution/{exec_id}")
    def get_execution_detail(exec_id: int):
        exec_data = get_execution(exec_id)
        if not exec_data:
            return Dialog(
                Article(
                    Header(Button(aria_label="Close", cls="close", onclick="this.closest('dialog').removeAttribute('open')"), P(Strong("Error"))),
                    P("Execution not found"),
                ),
                open=True,
            )

        # Prompt history
        prompt_history = [
            Div(
                P(Strong("Turn 1 (Root):")),
                Pre(exec_data["prompt"], style="white-space: pre-wrap; background: #f9f9f9; padding: 10px; border: 1px solid #eee;"),
            )
        ]
        for t in exec_data["turns"]:
            if t["turn_number"] > 1:
                prompt_history.append(Div(
                    P(Strong(f"Turn {t['turn_number']}:")),
                    Pre(t["prompt"], style="white-space: pre-wrap; background: #f9f9f9; padding: 10px; border: 1px solid #eee;"),
                ))

        # Logs + conversation flow
        all_logs = []
        conversation_history = []
        for t in exec_data["turns"]:
            all_logs.append(f"> User [Turn {t['turn_number']}]: {t['prompt']}")
            all_logs.append(t["logs"] or "No logs available")
            if t.get("thoughts"):
                try:
                    thoughts_list = json.loads(t["thoughts"])
                    if isinstance(thoughts_list, list):
                        for thought_obj in thoughts_list:
                            summary = thought_obj.get("summary", "") if isinstance(thought_obj, dict) else str(thought_obj)
                            conversation_history.append(Div(
                                Span("\U0001f9e0 Thinking: ", style="font-weight: bold; color: #007bff;"),
                                Span(summary, style="font-style: italic;"),
                                style="background: #f8f9fa; padding: 8px; border-radius: 8px; margin-bottom: 5px; border-left: 4px solid #007bff; font-size: 0.9em;",
                            ))
                except (json.JSONDecodeError, TypeError):
                    pass
            if t.get("agent_message"):
                conversation_history.append(Div(
                    Span("\U0001f916 Agent: ", style="font-weight: bold;"),
                    Div(t["agent_message"], cls="markdown-content"),
                    cls="agent-message",
                    style="background: #e3f2fd; padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2196f3;",
                ))

        full_log_text = "\n\n".join(all_logs)

        if exec_data["status"] in ("running", "waiting_for_input"):
            return Dialog(
                Article(
                    Header(
                        Button(aria_label="Close", cls="close", onclick="this.closest('dialog').removeAttribute('open')"),
                        P(Strong(f"Execution #{exec_id} is {exec_data['status']}")),
                    ),
                    Div(
                        P(Strong("Prompt History:")),
                        Div(*prompt_history, style="max-height: 200px; overflow-y: auto; margin-bottom: 20px; border: 1px solid #ccc; padding: 10px;"),
                        P(Strong("Conversation Flow:")),
                        Div(*conversation_history, id=f"conversation-flow-{exec_id}", cls="conversation-flow",
                            style="margin-bottom: 1rem; max-height: 200px; overflow-y: auto; padding: 10px; background: #f9f9f9; border-radius: 8px;"),
                        P(Strong("Live Logs:")),
                        Div(full_log_text, id=f"terminal-output-{exec_id}", cls="terminal", style="white-space: pre-wrap; height: 300px;"),
                    ),
                    Script(_sse_detail_script(exec_id)),
                ),
                open=True, id="execution-modal",
            )

        # Completed / error — static view
        return Dialog(
            Article(
                Header(
                    Button(aria_label="Close", cls="close", onclick="this.closest('dialog').removeAttribute('open')"),
                    P(Strong(f"Execution Details #{exec_id} - {exec_data['created_at']}")),
                ),
                Div(
                    P(Strong("Status: "), Span(exec_data["status"], cls=f"status-{exec_data['status']}"), " - ", exec_data["model"]),
                    P(Strong("Workspace: "), exec_data["workspace"]),
                    Grid(
                        Div(P(Strong("Total Prompt Tokens: ")), P(str(exec_data["total_tokens"] or 0))),
                        Div(P(Strong("Total Cost: ")), P(f"${exec_data['cost'] or 0:.4f}")),
                    ),
                    P(Strong("Prompt History:")),
                    Div(*prompt_history, style="max-height: 250px; overflow-y: auto; margin-bottom: 20px; border: 1px solid #ccc; padding: 10px;"),
                    P(Strong("Full Conversation Logs:")),
                    Pre(full_log_text, cls="terminal", style="max-height: 400px; overflow-y: auto;"),
                ),
                Footer(Button("Close", onclick="this.closest('dialog').removeAttribute('open')", cls="outline")),
            ),
            open=True, id="execution-modal",
        )

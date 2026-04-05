import os
import sqlite3
import asyncio
import queue
import json
import sys
import threading
from datetime import datetime
from fasthtml.common import *
from starlette.responses import StreamingResponse
from dotenv import load_dotenv

# Import MCP configuration
from engine.config import AVAILABLE_MCP_SERVERS, get_mcp_config

load_dotenv()

LOGIN_USER = os.getenv("LOGIN_USER", "admin")
LOGIN_PASS = os.getenv("LOGIN_PASS", "bsm4321")

API_KEY = os.getenv("API_KEY")



# Database setup
DB_FILE = "executor.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            model TEXT NOT NULL,
            workspace TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS execution_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id INTEGER,
            turn_number INTEGER,
            prompt TEXT NOT NULL,
            logs TEXT,
            agent_message TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            reasoning_tokens INTEGER,
            cache_read_tokens INTEGER,
            cache_write_tokens INTEGER,
            latency REAL,
            cost REAL,
            status TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (execution_id) REFERENCES executions(id)
        )
    ''')
    
    # Check if agent_message column exists
    c.execute("PRAGMA table_info(execution_turns)")
    columns = [col[1] for col in c.fetchall()]
    if "agent_message" not in columns:
        c.execute("ALTER TABLE execution_turns ADD COLUMN agent_message TEXT")
    if "reasoning_tokens" not in columns:
        c.execute("ALTER TABLE execution_turns ADD COLUMN reasoning_tokens INTEGER")
    if "cache_read_tokens" not in columns:
        c.execute("ALTER TABLE execution_turns ADD COLUMN cache_read_tokens INTEGER")
    if "cache_write_tokens" not in columns:
        c.execute("ALTER TABLE execution_turns ADD COLUMN cache_write_tokens INTEGER")
    if "latency" not in columns:
        c.execute("ALTER TABLE execution_turns ADD COLUMN latency REAL")

    conn.commit()
    conn.close()

def add_execution(prompt, model, workspace):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO executions (prompt, model, workspace, status) VALUES (?, ?, ?, ?)",
        (prompt, model, workspace, "running")
    )
    exec_id = c.lastrowid
    conn.commit()
    conn.close()
    return exec_id

def update_execution_status(exec_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE executions SET status = ? WHERE id = ?", (status, exec_id))
    conn.commit()
    conn.close()

def add_execution_turn(exec_id, turn_number, prompt):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO execution_turns (execution_id, turn_number, prompt, status) VALUES (?, ?, ?, ?)",
        (exec_id, turn_number, prompt, "running")
    )
    turn_id = c.lastrowid
    conn.commit()
    conn.close()
    return turn_id

def update_turn_status(turn_id, status, logs=None, prompt_tokens=None, completion_tokens=None, total_tokens=None, cost=None,
                       agent_message=None, reasoning_tokens=None, cache_read_tokens=None, cache_write_tokens=None, latency=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    update_fields = ["status = ?"]
    params = [status]
    
    if logs is not None:
        update_fields.append("logs = ?")
        params.append(logs)
    if agent_message is not None:
        update_fields.append("agent_message = ?")
        params.append(agent_message)
    if prompt_tokens is not None:
        update_fields.append("prompt_tokens = ?")
        params.append(prompt_tokens)
    if completion_tokens is not None:
        update_fields.append("completion_tokens = ?")
        params.append(completion_tokens)
    if total_tokens is not None:
        update_fields.append("total_tokens = ?")
        params.append(total_tokens)
    if reasoning_tokens is not None:
        update_fields.append("reasoning_tokens = ?")
        params.append(reasoning_tokens)
    if cache_read_tokens is not None:
        update_fields.append("cache_read_tokens = ?")
        params.append(cache_read_tokens)
    if cache_write_tokens is not None:
        update_fields.append("cache_write_tokens = ?")
        params.append(cache_write_tokens)
    if latency is not None:
        update_fields.append("latency = ?")
        params.append(latency)
    if cost is not None:
        update_fields.append("cost = ?")
        params.append(cost)
        
    params.append(turn_id)
    c.execute(f"UPDATE execution_turns SET {', '.join(update_fields)} WHERE id = ?", tuple(params))
    conn.commit()
    conn.close()

def get_executions(page=1, page_size=10):
    offset = (page - 1) * page_size
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """
        SELECT e.id, e.prompt, e.model, e.workspace, e.status, e.created_at,
               (SELECT COUNT(*) FROM execution_turns WHERE execution_id = e.id) as turns_count,
               (SELECT SUM(total_tokens) FROM execution_turns WHERE execution_id = e.id) as total_tokens,
               (SELECT SUM(cost) FROM execution_turns WHERE execution_id = e.id) as total_cost
        FROM executions e ORDER BY e.id DESC LIMIT ? OFFSET ?
        """,
        (page_size, offset)
    )
    rows = c.fetchall()
    c.execute("SELECT COUNT(*) FROM executions")
    total_count = c.fetchone()[0]
    conn.close()
    
    return [
        {
            "id": r[0], "prompt": r[1], "model": r[2], "workspace": r[3], "status": r[4], "created_at": r[5],
            "turns_count": r[6] or 0, "total_tokens": r[7] or 0, "cost": r[8] or 0.0
        }
        for r in rows
    ], total_count

def get_execution(exec_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, prompt, model, workspace, status, created_at FROM executions WHERE id = ?", (exec_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    
    exec_data = {"id": row[0], "prompt": row[1], "model": row[2], "workspace": row[3], "status": row[4], "created_at": row[5]}
    
    c.execute("SELECT turn_number, prompt, logs, status, prompt_tokens, completion_tokens, total_tokens, cost, created_at, agent_message FROM execution_turns WHERE execution_id = ? ORDER BY turn_number ASC", (exec_id,))
    turns = c.fetchall()
    exec_data["turns"] = [
        {
            "turn_number": t[0], "prompt": t[1], "logs": t[2], "status": t[3],
            "prompt_tokens": t[4] or 0, "completion_tokens": t[5] or 0, "total_tokens": t[6] or 0, "cost": t[7] or 0.0, "created_at": t[8],
            "agent_message": t[9]
        } for t in turns
    ]
    
    exec_data["total_tokens"] = sum(t["total_tokens"] for t in exec_data["turns"])
    exec_data["cost"] = sum(t["cost"] for t in exec_data["turns"])
    
    conn.close()
    return exec_data

def render_history(page=1):
    page_size = 10
    executions, total_count = get_executions(page, page_size)
    total_pages = (total_count + page_size - 1) // page_size
    
    pagination_controls = []
    if total_pages > 1:
        if page > 1:
            pagination_controls.append(Button("Prev", hx_get=f"/history?page={page-1}", hx_target="#history-container", cls="outline small"))
        pagination_controls.append(Span(f"Page {page} of {total_pages}"))
        if page < total_pages:
            pagination_controls.append(Button("Next", hx_get=f"/history?page={page+1}", hx_target="#history-container", cls="outline small"))

    return Div(
        H3("Execution History"),
        Div(
            *[Article(
                Div(
                    Div(
                        A(f"Execution #{exec['id']}", hx_get=f"/conversation/{exec['id']}", hx_target="#modal-placeholder", style="font-weight: bold; font-size: 1.1rem;"),
                        cls="card-header"
                    ),
                    Div(
                        P(Strong("Prompt: "), Span(exec["prompt"][:200] + ("..." if len(exec["prompt"]) > 200 else ""))),
                        Div(
                            Div(Small("Model: "), Strong(exec["model"])),
                            Div(Small("Workspace: "), Span(exec["workspace"])),
                            Div(Small("Turns: "), Span(str(exec["turns_count"]))),
                            Div(Small("Usage: "), Span(f"{exec['total_tokens']} tokens / ${exec['cost']:.4f}")),
                            cls="card-grid"
                        ),
                        cls="card-body"
                    ),
                    Div(
                        Small(exec["created_at"], style="color: #999;"),
                        A("Copy", href="#", onclick=f"resumeTask({json.dumps(exec['prompt'])}, {json.dumps(exec['model'])}, {json.dumps(exec['workspace'])}); return false;",
                          style="font-size: 0.9rem; text-decoration: underline;"),
                        cls="card-footer"
                    ),
                ),
                cls="execution-card"
            ) for exec in executions] if executions else P("No executions yet"),
            cls="history-cards"
        ),
        Div(*pagination_controls, cls="pagination-container")
    )

init_db()

execution_queues = {} # For SSE output stream
execution_inputs = {} # For input messages

class QueueWriter:
    def __init__(self, queue, loop):
        self.queue = queue
        self.loop = loop
        self.full_logs = []

    def write(self, data):
        if data:
            self.full_logs.append(data)
            asyncio.run_coroutine_threadsafe(self.queue.put(data), self.loop)
            sys.__stdout__.write(data)
            sys.__stdout__.flush()
            
    def clear_logs(self):
        self.full_logs = []

    def flush(self):
        sys.__stdout__.flush()

    def get_logs(self):
        return "".join(self.full_logs)

    @property
    def encoding(self):
        return getattr(sys.__stdout__, 'encoding', 'utf-8')

def auth_before(request, session):
    path = request.scope['path']
    if path in ['/login', '/favicon.ico', '/static']: return
    
    # API Authentication
    if path.startswith('/api/'):
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if not API_KEY or api_key != API_KEY:
            from starlette.responses import JSONResponse
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return
        
    if 'auth' not in session: return RedirectResponse('/login', status_code=303)

app, rt = fast_app(
    pico=True,
    before=auth_before,
    hdrs=(
        Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
        Script("""
            function resumeTask(prompt, model, workspace) {
                document.getElementById('prompt').value = prompt;
                document.getElementById('model').value = model;
                document.getElementById('workspace').value = workspace;
                window.scrollTo({ top: 0, behavior: 'smooth' });
                const btn = document.querySelector('.button-execute');
                if(prompt.trim()) btn.disabled = false;
            }
        """),
        Style("""
            .terminal { 
                border: 1px solid #ccc; padding: 1rem; margin: 1rem 0; min-height: 100px; 
                background-color: #1e1e1e; color: #d4d4d4; font-family: 'Courier New', monospace;
                overflow-y: auto; max-height: 500px; white-space: pre-wrap; border-radius: 4px;
            }
            .markdown-content { 
                background: #e8f4fd; padding: 15px; border-radius: 4px; margin-bottom: 10px; 
                border-left: 4px solid #2196F3; line-height: 1.6;
            }
            .markdown-content h1, .markdown-content h2, .markdown-content h3 { margin-top: 1rem; margin-bottom: 0.5rem; }
            .markdown-content p { margin-bottom: 0.8rem; }
            .markdown-content code { background: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: monospace; }
            .markdown-content pre { background: #f8f8f8; padding: 10px; border-radius: 4px; overflow-x: auto; }
            .markdown-content pre code { background: transparent; padding: 0; }
            .markdown-content ul, .markdown-content ol { padding-left: 1.5rem; margin-bottom: 1rem; }
            
            details.log-accordion { 
                border: 1px solid #eee; border-radius: 4px; margin-top: 10px; 
            }
            details.log-accordion summary { 
                padding: 8px 12px; cursor: pointer; background: #f9f9f9; font-weight: bold; list-style: none;
            }
            details.log-accordion summary::-webkit-details-marker { display: none; }
            details.log-accordion summary:hover { background: #f0f0f0; }
            details.log-accordion[open] summary { border-bottom: 1px solid #eee; margin-bottom: 10px; }
            
            .turn-header {
                display: grid;
                grid-template-columns: auto 1fr auto;
                gap: 20px;
                align-items: center;
                background: #f8f9fa;
                padding: 10px 15px;
                border-radius: 6px;
                margin-bottom: 15px;
                border: 1px solid #e9ecef;
            }
            .turn-metrics {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                font-size: 0.85rem;
                color: #666;
            }
            .metric-badge {
                background: #fff;
                padding: 2px 8px;
                border-radius: 4px;
                border: 1px solid #dee2e6;
            }
            
            .execution-card {
                margin-bottom: 1.5rem;
                padding: 1.2rem;
                border: 1px solid #e1e4e8;
                border-radius: 10px;
                background: white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }
            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
                border-bottom: 1px solid #f1f1f1;
                padding-bottom: 0.5rem;
            }
            .card-body p { margin-bottom: 0.8rem; }
            .card-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                font-size: 0.9rem;
                margin-top: 10px;
                background: #fcfcfc;
                padding: 10px;
                border-radius: 6px;
            }
            .card-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 1rem;
                padding-top: 0.8rem;
                border-top: 1px solid #f1f1f1;
            }
            
            .user-msg { color: #569cd6; font-weight: bold; }
            .sys-msg { color: #c586c0; font-style: italic; }
            .history-table { width: 100%; border-collapse: collapse; }
            .history-table th, .history-table td { border: 1px solid #ddd; padding: 0.5rem; text-align: left; }
            .history-table th { background-color: #f2f2f2; }
            .status-running { color: orange; font-weight: bold; }
            .status-waiting_for_input { color: #007acc; font-weight: bold; }
            .status-success { color: green; font-weight: bold; }
            .status-completed { color: green; font-weight: bold; }
            .status-error { color: red; font-weight: bold; }
            .error { color: red; font-weight: bold; margin-bottom: 1rem; }
            .loading-indicator { display: none; }
            .htmx-request .loading-indicator, .is-loading .loading-indicator { display: flex; align-items: center; justify-content: center; }
            .htmx-request .normal-text, .is-loading .normal-text { display: none; }
            .htmx-request.button-execute, .is-loading.button-execute { pointer-events: none; opacity: 0.8; }
            .spinner { display: inline-block; width: 1.2rem; height: 1.2rem; border: 2px solid rgba(255,255,255,.3); border-radius: 50%; border-top-color: #fff; animation: spin 0.8s linear infinite; margin-right: 0.5rem; }
            @keyframes spin { to { transform: rotate(360deg); } }
            .button-execute { width: 150px !important; display: inline-block !important; margin-right: 1rem !important; }
            #execution-modal article { width: 95%; max-width: 1200px; }
            .conversation-link { display: inline-block; vertical-align: middle; }
            #conversation-modal article { 
                width: 95%; 
                max-width: 1200px;
                height: 90vh; 
            }
            @media (min-width: 768px) {
                #conversation-modal article { width: 80%; }
            }
            @media (min-width: 1200px) {
                #conversation-modal article { width: 70%; }
            }
            @media (max-width: 767px) {
                .turn-header {
                    grid-template-columns: 1fr;
                    gap: 10px;
                }
                .turn-metrics {
                    order: 3;
                }
            }
            .pagination-container { display: flex; align-items: center; justify-content: center; margin-top: 1rem; gap: 1rem; }
            .pagination-container button { margin-bottom: 0; }
            .followup-box { background: #f4f4f4; padding: 1rem; border-radius: 8px; margin-top: 1rem; border: 1px solid #ccc; }
        """),
    )
)

@rt("/")
def get_index(session):
    models = [
        "gemini/gemini-3-flash-preview",
        "gemini/gemini-2.0-flash-exp",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "anthropic/claude-3-5-sonnet-20240620"
    ]
    return Titled("Task Runner",
        Div(
            A("Logout", href="/logout", style="float: right"),
            Form(
                H3("Execute Task"),
                Grid(
                    Div(
                        Label("Model:", fr="model"),
                        Select(
                            *[Option(m, value=m) for m in models],
                            name="model", id="model", required=True
                        ),
                    ),
                    Div(
                        Label("Working Directory:", fr="workspace"),
                        Input(type="text", name="workspace", id="workspace", required=True, value="."),
                    ),
                ),
                Div(
                    H4("Select MCP Servers:"),
                    Grid(
                        *[Div(
                            Label(
                                Input(type="checkbox", name="mcp_ids", value=m_id, id=f"mcp-{m_id}"),
                                Span(f" {m_info['name']}"),
                                title=m_info['description']
                            ),
                            style="margin-bottom: 0.5rem;"
                        ) for m_id, m_info in AVAILABLE_MCP_SERVERS.items()]
                    ),
                    style="margin-bottom: 1rem; padding: 1rem; border: 1px solid #eee; border-radius: 8px;"
                ),
                Label("Prompt:", fr="prompt"),
                Textarea(name="prompt", id="prompt", rows=4, required=True, 
                         oninput="const btn = document.querySelector('.button-execute'); if(this.value.trim()){ btn.disabled = false; } else { btn.disabled = true; }"),
                Button(
                    Div(Span(cls="spinner"), "Execute", cls="loading-indicator"),
                    Span("Execute", cls="normal-text"),
                    type="submit", hx_post="/execute", hx_target="#loading-indicator", hx_swap="none", cls="button-execute", disabled=True
                ),
                A("Conversation", id="conversation-link", cls="conversation-link", href="#", 
                  hx_get="/conversation", hx_target="#modal-placeholder", 
                  hx_trigger="click",
                  onclick="const execId = document.getElementById('task-form').dataset.activeExecId; if(!execId) { alert('No active execution'); return false; } this.setAttribute('hx-get', '/conversation/' + execId); htmx.process(this);",
                  style="display:none"),
                id="task-form",
                hx_on__after_request="""
                    if(event.detail.successful) { 
                        const execId = event.detail.xhr.responseText.match(/execution-(\d+)/)?.[1];
                        if(execId) {
                            this.dataset.activeExecId = execId;
                            const convLink = document.getElementById('conversation-link');
                            convLink.style.display = 'inline-block';
                            convLink.innerText = 'Conversation #' + execId;
                        }
                    }
                """
            ),
            Div(Span("Loading...", cls="loading-indicator"), id="loading-indicator"),
            Div(id="executions-container"),
            Div(id="modal-placeholder"),
            Div(render_history(1), id="history-container")
        )
    )

@rt("/history")
def get_history(page: int = 1):
    return render_history(page)


def start_execution_thread(exec_id, prompt, model, workspace, mcp_config, loop, q, in_q):
    def run_task_thread():
        old_stdout = sys.stdout
        writer = QueueWriter(q, loop)
        sys.stdout = writer
        try:
            from engine.runner import TaskRunner
            runner = TaskRunner(workspace=workspace, model=model, mcp_config=mcp_config)
            success_init, _ = runner.start_session()
            if not success_init:
                update_execution_status(exec_id, "error")
                return

            turn_number = 1
            current_prompt = prompt

            while True:
                turn_id = add_execution_turn(exec_id, turn_number, current_prompt)

                sys.stdout.write(f"\n> User: {current_prompt}\n")
                success, metrics = runner.send_task(current_prompt)

                status = "success" if success else "error"
                update_turn_status(
                    turn_id, status, writer.get_logs(),
                    agent_message=metrics.get("agent_message"),
                    prompt_tokens=metrics.get("prompt_tokens"),
                    completion_tokens=metrics.get("completion_tokens"),
                    total_tokens=metrics.get("total_tokens"),
                    reasoning_tokens=metrics.get("reasoning_tokens"),
                    cache_read_tokens=metrics.get("cache_read_tokens"),
                    cache_write_tokens=metrics.get("cache_write_tokens"),
                    latency=metrics.get("latency"),
                    cost=metrics.get("cost")
                )
                writer.clear_logs()

                update_execution_status(exec_id, "waiting_for_input")
                sys.stdout.write("\n[System: Gõ lệnh tiếp theo]\n")

                try:
                    msg = in_q.get(block=True, timeout=3600)
                except queue.Empty:
                    msg = "__STOP__"
                    sys.stdout.write("\n[System: Timeout waiting for input]\n")

                if msg == "__STOP__":
                    update_execution_status(exec_id, "completed")
                    sys.stdout.write("\n[System: Phiên làm việc đã kết thúc]\n")
                    break

                current_prompt = msg
                turn_number += 1
                update_execution_status(exec_id, "running")

        except Exception as e:
            sys.stdout.write(f"Error: {str(e)}\n")
            import traceback
            traceback.print_exc()
            update_execution_status(exec_id, "error")
        finally:
            if 'runner' in locals() and hasattr(runner, 'close_session'):
                runner.close_session()
            sys.stdout = old_stdout
            asyncio.run_coroutine_threadsafe(q.put(None), loop)
            if exec_id in execution_queues:
                del execution_queues[exec_id]
            if exec_id in execution_inputs:
                del execution_inputs[exec_id]

    thread = threading.Thread(target=run_task_thread)
    thread.start()

@rt("/execute")
async def post_execute(request):
    form = await request.form()
    prompt = form.get("prompt", "").strip()
    model = form.get("model", "").strip()
    workspace = form.get("workspace", "").strip()
    exec_id_active = form.get("exec_id", "").strip()
    
    # Get selected MCP IDs
    selected_mcp_ids = form.getlist("mcp_ids")
    mcp_config = get_mcp_config(selected_mcp_ids)
    
    if exec_id_active and exec_id_active.isdigit():
        exec_id = int(exec_id_active)
        if prompt and exec_id in execution_inputs:
            execution_inputs[exec_id].put(prompt)
        # Return nothing to avoid replacing the terminal container, 
        # but the client-side Script in the initial /execute call handles state
        return ""

    if not prompt or not model or not workspace:
        return Div("Prompt, model, and workspace are required", cls="error")
    
    exec_id = add_execution(prompt, model, workspace)
    
    loop = asyncio.get_running_loop()
    q = asyncio.Queue()
    in_q = queue.Queue()
    execution_queues[exec_id] = q
    execution_inputs[exec_id] = in_q
    
    start_execution_thread(exec_id, prompt, model, workspace, mcp_config, loop, q, in_q)
    
    return Div(
        H4(f"Execution #{exec_id} started"),
        Div(id=f"terminal-output-{exec_id}", cls="terminal"),
        Script(f"""
            (function() {{
                const term = document.getElementById('terminal-output-{exec_id}');
                const btn = document.querySelector('.button-execute');
                const promptArea = document.getElementById('prompt');
                const taskForm = document.getElementById('task-form');
                
                if (btn) {{ btn.classList.add('is-loading'); btn.disabled = true; }}
                
                const source = new EventSource('/stream/{exec_id}');
                source.onmessage = function(event) {{
                    const data = event.data;
                    term.textContent += data + '\\n';
                    term.scrollTop = term.scrollHeight;
                    
                    if (data.includes('[System: Gõ lệnh tiếp theo')) {{
                        if (btn) {{ 
                            btn.classList.remove('is-loading'); 
                            btn.disabled = true; // Always disable first because we clear prompt
                        }}
                        if (promptArea) {{
                            promptArea.value = '';
                            promptArea.placeholder = 'Gõ yêu cầu tiếp theo...';
                            // Add hidden input for exec_id if not exists
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
                    // Remove hidden input when finished
                    if(taskForm) {{
                        let inputExec = taskForm.querySelector('input[name="exec_id"]');
                        if(inputExec) inputExec.remove();
                    }}
                    if(promptArea) promptArea.placeholder = '';
                }};
            }})();
        """),
        id=f"execution-{exec_id}",
        hx_swap_oob="afterbegin:#executions-container"
    )

@rt("/execute/{exec_id}/message")
async def post_message(exec_id: int, request):
    form = await request.form()
    prompt = form.get("prompt", "").strip()
    if prompt and exec_id in execution_inputs:
        execution_inputs[exec_id].put(prompt)
    return ""

@rt("/execute/{exec_id}/stop")
def post_stop(exec_id: int):
    if exec_id in execution_inputs:
        execution_inputs[exec_id].put("__STOP__")
    return ""

@rt("/stream/{exec_id}")
async def get_stream(exec_id: int):
    async def event_stream():
        q = execution_queues.get(exec_id)
        if q is None: return
        while True:
            try:
                line = await q.get()
            except asyncio.CancelledError:
                break
            if line is None:
                await asyncio.sleep(0.1)
                break
            lines = line.splitlines(keepends=True)
            for l in lines:
                data_content = l.rstrip('\n').rstrip('\r')
                yield f"data: {data_content}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})

def get_execution_turns(exec_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT turn_number, prompt, logs, status, prompt_tokens, completion_tokens, total_tokens, cost, created_at,
               agent_message, reasoning_tokens, cache_read_tokens, cache_write_tokens, latency
        FROM execution_turns 
        WHERE execution_id = ? 
        ORDER BY created_at DESC
    """, (exec_id,))
    turns = c.fetchall()
    conn.close()
    return [
        {
            "turn_number": t[0], "prompt": t[1], "logs": t[2], "status": t[3],
            "prompt_tokens": t[4] or 0, "completion_tokens": t[5] or 0, "total_tokens": t[6] or 0, "cost": t[7] or 0.0, "created_at": t[8],
            "agent_message": t[9], "reasoning_tokens": t[10] or 0, "cache_read_tokens": t[11] or 0, "cache_write_tokens": t[12] or 0, "latency": t[13] or 0.0
        } for t in turns
    ]

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
            Span(f"Status: {t['status']}", cls=f"metric-badge status-{t['status']}")
        ]
        
        turn_elements.append(Div(
            Div(
                H4(f"Turn {t['turn_number']}", style="margin:0;"),
                Div(*metrics_badges, cls="turn-metrics"),
                Small(t['created_at'], style="color: #999;"),
                cls="turn-header"
            ),
            Pre(t["prompt"], style="white-space: pre-wrap; background: #f0f0f0; padding: 10px; border-radius: 4px;"),
            Div(t["agent_message"] or "No message", cls="markdown-content"),
            Details(
                Summary("📜 View Logs", style="color: #007acc; text-decoration: underline;"),
                Pre(t["logs"] or "No logs", cls="terminal", style="max-height: 250px; overflow-y: auto;"),
                cls="log-accordion"
            ),
            style="margin-bottom: 1rem; padding-bottom: 1rem;"
        ))

    return Dialog(
        Article(
            Header(
                Button(aria_label="Close", cls="close", onclick="this.closest('dialog').removeAttribute('open')"),
                P(Strong(f"Conversation #{exec_id}"))
            ),
            Div(*turn_elements, id="conversation-content", style="overflow-y: auto; max-height: calc(90vh - 150px);"),
            Script("""
                document.querySelectorAll('.markdown-content').forEach(function(el) {
                    if (!el.dataset.rendered) {
                        el.innerHTML = marked.parse(el.textContent || el.innerText);
                        el.dataset.rendered = "true";
                    }
                });
            """)
        ),
        open=True, id="conversation-modal"
    )

@rt("/execution/{exec_id}")
def get_execution_detail(exec_id: int):
    exec_data = get_execution(exec_id)
    if not exec_data:
        return Dialog(Article(Header(Button(aria_label="Close", cls="close", onclick="this.closest('dialog').removeAttribute('open')"), P(Strong("Error"))), P("Execution not found")), open=True)
    
    # Prepare Prompt History
    prompt_history = [Div(P(Strong("Turn 1 (Root):")), Pre(exec_data["prompt"], style="white-space: pre-wrap; background: #f9f9f9; padding: 10px; border: 1px solid #eee;"))]
    for t in exec_data["turns"]:
        if t['turn_number'] > 1:
            prompt_history.append(Div(P(Strong(f"Turn {t['turn_number']}:")), Pre(t["prompt"], style="white-space: pre-wrap; background: #f9f9f9; padding: 10px; border: 1px solid #eee;")))
    
    # Render all logs from all turns
    all_logs = []
    for t in exec_data["turns"]:
        all_logs.append(f"> User [Turn {t['turn_number']}]: {t['prompt']}")
        all_logs.append(t['logs'] or "No logs available")
    full_log_text = "\n\n".join(all_logs)
    
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
                    P(Strong("Live Logs:")),
                    Div(full_log_text, id=f"terminal-output-{exec_id}", cls="terminal", style="white-space: pre-wrap; height: 300px;"),
                ),
                Script(f"""
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
                """)
            ),
            open=True, id="execution-modal"
        )
    else:
        # Nếu đã hoàn thành hoặc huỷ, in ra thông báo tĩnh và lịch sử toàn bộ prompt
        return Dialog(
            Article(
                Header(
                    Button(aria_label="Close", cls="close", onclick="this.closest('dialog').removeAttribute('open')"),
                    P(Strong(f"Execution Details #{exec_id} - {exec_data['created_at']}"))
                ),
                Div(
                    P(Strong("Status: "), Span(exec_data["status"], cls=f"status-{exec_data['status']}"), " - ", exec_data["model"]),
                    P(Strong("Workspace: "), exec_data["workspace"]),
                    Grid(
                        Div(P(Strong("Total Prompt Tokens: ")), P(str(exec_data["total_tokens"] or 0))),
                        Div(P(Strong("Total Cost: ")), P(f"${exec_data['cost'] or 0:.4f}"))
                    ),
                    P(Strong("Prompt History:")),
                    Div(*prompt_history, style="max-height: 250px; overflow-y: auto; margin-bottom: 20px; border: 1px solid #ccc; padding: 10px;"),
                    P(Strong("Full Conversation Logs:")),
                    Pre(full_log_text, cls="terminal", style="max-height: 400px; overflow-y: auto;")
                ),
                Footer(Button("Close", onclick="this.closest('dialog').removeAttribute('open')", cls="outline"))
            ),
            open=True, id="execution-modal"
        )

@app.get("/login")
def get_login():
    return Titled("Task runner", Main(Card(Form(Label("Username", fr="username"), Input(type="text", name="username", id="username", required=True), Label("Password", fr="password"), Input(type="password", name="password", id="password", required=True), Button("Login", type="submit"), action="/login", method="post"), header=Header(H2("Authentication Required"))), cls="container", style="max-width: 400px; margin-top: 100px;"))

@app.post("/login")
def post_login(username: str, password: str, session):
    if username == LOGIN_USER and password == LOGIN_PASS:
        session['auth'] = username
        return RedirectResponse("/", status_code=303)
    return Titled("Task runner", Main(Card(P("Invalid username or password", style="color: red"), Form(Label("Username", fr="username"), Input(type="text", name="username", id="username", required=True), Label("Password", fr="password"), Input(type="password", name="password", id="password", required=True), Button("Login", type="submit"), action="/login", method="post"), header=Header(H2("Authentication Required"))), cls="container", style="max-width: 400px; margin-top: 100px;"))

@app.get("/logout")
def get_logout(session):
    session.pop('auth', None)
    return RedirectResponse("/login", status_code=303)


from starlette.responses import JSONResponse

@app.post("/api/execute")
async def api_execute(request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
        
    prompt = data.get("prompt", "").strip()
    model = data.get("model", "").strip()
    workspace = data.get("workspace", "").strip()
    mcp_ids = data.get("mcp_ids", [])
    
    if not prompt or not model or not workspace:
        return JSONResponse({"error": "Prompt, model, and workspace are required"}, status_code=400)
        
    mcp_config = get_mcp_config(mcp_ids)
    exec_id = add_execution(prompt, model, workspace)
    
    loop = asyncio.get_running_loop()
    q = asyncio.Queue()
    in_q = queue.Queue()
    execution_queues[exec_id] = q
    execution_inputs[exec_id] = in_q
    
    start_execution_thread(exec_id, prompt, model, workspace, mcp_config, loop, q, in_q)
    
    return JSONResponse({"execution_id": exec_id, "status": "running"})

@app.post("/api/execute/{exec_id}/message")
async def api_execute_message(exec_id: int, request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
        
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return JSONResponse({"error": "Prompt is required"}, status_code=400)
        
    if exec_id in execution_inputs:
        execution_inputs[exec_id].put(prompt)
        return JSONResponse({"status": "message_sent"})
    else:
        return JSONResponse({"error": "Execution not found or not waiting for input"}, status_code=404)

@app.get("/api/execute/{exec_id}/status")
def api_execute_status(exec_id: int):
    exec_data = get_execution(exec_id)
    if not exec_data:
        return JSONResponse({"error": "Execution not found"}, status_code=404)
    
    last_turn = exec_data["turns"][-1] if exec_data["turns"] else None
    
    return JSONResponse({
        "status": exec_data["status"],
        "last_agent_message": last_turn["agent_message"] if last_turn else None,
        "current_turn": last_turn["turn_number"] if last_turn else 0,
        "metrics": {
            "total_tokens": exec_data.get("total_tokens", 0),
            "cost": exec_data.get("cost", 0.0)
        }
    })

@app.post("/api/execute/{exec_id}/stop")
def api_execute_stop(exec_id: int):
    if exec_id in execution_inputs:
        execution_inputs[exec_id].put("__STOP__")
        return JSONResponse({"status": "stop_signal_sent"})
    else:
        return JSONResponse({"error": "Execution not found or not active"}, status_code=404)

serve()

import re

with open('main.py', 'r') as f:
    content = f.read()

# Add API_KEY to dotenv loading
api_key_code = """
API_KEY = os.getenv("API_KEY")
"""
content = content.replace('LOGIN_PASS = os.getenv("LOGIN_PASS", "bsm4321")', 'LOGIN_PASS = os.getenv("LOGIN_PASS", "bsm4321")\n' + api_key_code)

# Modify auth_before
auth_before_old = """def auth_before(request, session):
    path = request.scope['path']
    if path in ['/login', '/favicon.ico', '/static']: return
    if 'auth' not in session: return RedirectResponse('/login', status_code=303)"""

auth_before_new = """def auth_before(request, session):
    path = request.scope['path']
    if path in ['/login', '/favicon.ico', '/static']: return
    
    # API Authentication
    if path.startswith('/api/'):
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if not API_KEY or api_key != API_KEY:
            from starlette.responses import JSONResponse
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return
        
    if 'auth' not in session: return RedirectResponse('/login', status_code=303)"""

content = content.replace(auth_before_old, auth_before_new)

# Extract run_task_thread
run_task_thread_code = """
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

                sys.stdout.write(f"\\n> User: {current_prompt}\\n")
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
                sys.stdout.write("\\n[System: Gõ lệnh tiếp theo]\\n")

                try:
                    msg = in_q.get(block=True, timeout=3600)
                except queue.Empty:
                    msg = "__STOP__"
                    sys.stdout.write("\\n[System: Timeout waiting for input]\\n")

                if msg == "__STOP__":
                    update_execution_status(exec_id, "completed")
                    sys.stdout.write("\\n[System: Phiên làm việc đã kết thúc]\\n")
                    break

                current_prompt = msg
                turn_number += 1
                update_execution_status(exec_id, "running")

        except Exception as e:
            sys.stdout.write(f"Error: {str(e)}\\n")
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
"""

# We need to insert start_execution_thread before post_execute
# Let's find post_execute
post_execute_idx = content.find('@rt("/execute")\nasync def post_execute')
if post_execute_idx == -1:
    post_execute_idx = content.find('async def post_execute')

content = content[:post_execute_idx] + run_task_thread_code + "\n" + content[post_execute_idx:]

# Now replace the inner run_task_thread in post_execute
old_post_execute_inner = """    def run_task_thread():
        old_stdout = sys.stdout
        writer = QueueWriter(q, loop)
        sys.stdout = writer
        try:
            from engine.runner import TaskRunner
            # Pass mcp_config to TaskRunner
            runner = TaskRunner(workspace=workspace, model=model, mcp_config=mcp_config)
            success_init, _ = runner.start_session()
            if not success_init:
                update_execution_status(exec_id, "error")
                return

            turn_number = 1
            current_prompt = prompt

            while True:
                turn_id = add_execution_turn(exec_id, turn_number, current_prompt)

                sys.stdout.write(f"\\n> User: {current_prompt}\\n")
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
                sys.stdout.write("\\n[System: Gõ lệnh tiếp theo]\\n")

                msg = in_q.get(block=True)
                if msg == "__STOP__":
                    update_execution_status(exec_id, "completed")
                    sys.stdout.write("\\n[System: Phiên làm việc đã kết thúc]\\n")
                    break

                current_prompt = msg
                turn_number += 1
                update_execution_status(exec_id, "running")

        except Exception as e:
            sys.stdout.write(f"Error: {str(e)}\\n")
            import traceback
            traceback.print_exc()
            update_execution_status(exec_id, "error")
        finally:
            if 'runner' in locals() and hasattr(runner, 'close_session'):
                runner.close_session()
            sys.stdout = old_stdout
            asyncio.run_coroutine_threadsafe(q.put(None), loop)
            # Cleanup mappings
            if exec_id in execution_queues:
                del execution_queues[exec_id]
            if exec_id in execution_inputs:
                del execution_inputs[exec_id]

    thread = threading.Thread(target=run_task_thread)
    thread.start()"""

new_post_execute_inner = """    start_execution_thread(exec_id, prompt, model, workspace, mcp_config, loop, q, in_q)"""

content = content.replace(old_post_execute_inner, new_post_execute_inner)

with open('main.py', 'w') as f:
    f.write(content)


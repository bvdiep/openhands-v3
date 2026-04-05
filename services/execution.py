import sys
import asyncio
import threading
import queue as queue_module
import traceback

from db.queries import add_execution_turn, update_turn_status, update_execution_status

# ---------------------------------------------------------------------------
# Thread-safe global state
# ---------------------------------------------------------------------------

_lock = threading.Lock()
execution_queues = {}    # exec_id -> asyncio.Queue
execution_inputs = {}    # exec_id -> queue.Queue
execution_thoughts = {}  # exec_id -> current thought dict
turn_thoughts = {}       # exec_id -> list of thoughts for current turn


def register_execution(exec_id, q, in_q):
    with _lock:
        execution_queues[exec_id] = q
        execution_inputs[exec_id] = in_q


def cleanup_execution(exec_id):
    with _lock:
        execution_queues.pop(exec_id, None)
        execution_inputs.pop(exec_id, None)
        execution_thoughts.pop(exec_id, None)
        turn_thoughts.pop(exec_id, None)


# ---------------------------------------------------------------------------
# Thread-safe stdout redirect
# ---------------------------------------------------------------------------

_thread_local = threading.local()


class ThreadSafeStdout:
    """Thread-local stdout redirect. Each execution thread gets its own writer."""

    def write(self, data):
        writer = getattr(_thread_local, 'writer', None)
        if writer:
            writer.write(data)
        else:
            sys.__stdout__.write(data)

    def flush(self):
        writer = getattr(_thread_local, 'writer', None)
        if writer:
            writer.flush()
        else:
            sys.__stdout__.flush()

    @property
    def encoding(self):
        return getattr(sys.__stdout__, 'encoding', 'utf-8')

    def isatty(self):
        return False


def install_thread_safe_stdout():
    """Install once at app startup."""
    sys.stdout = ThreadSafeStdout()


def set_thread_writer(writer):
    _thread_local.writer = writer


def clear_thread_writer():
    if hasattr(_thread_local, 'writer'):
        del _thread_local.writer


# ---------------------------------------------------------------------------
# QueueWriter
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Execution thread
# ---------------------------------------------------------------------------

def start_execution_thread(exec_id, prompt, model, workspace, mcp_config, loop, q, in_q):
    def run_task_thread():
        writer = QueueWriter(q, loop)
        set_thread_writer(writer)
        try:
            from engine.runner import TaskRunner
            active_turn_id = None

            def on_thought(thought_data):
                nonlocal active_turn_id
                with _lock:
                    if exec_id not in turn_thoughts:
                        turn_thoughts[exec_id] = []
                    turn_thoughts[exec_id].append(thought_data)
                    execution_thoughts[exec_id] = thought_data

                if active_turn_id:
                    update_turn_status(active_turn_id, "running", thoughts=turn_thoughts.get(exec_id, []))

                asyncio.run_coroutine_threadsafe(q.put({"event": "agent_thought", "data": thought_data}), loop)

            runner = TaskRunner(workspace=workspace, model=model, mcp_config=mcp_config, on_thought=on_thought)
            success_init, _ = runner.start_session()
            if not success_init:
                update_execution_status(exec_id, "error")
                return

            turn_number = 1
            current_prompt = prompt

            while True:
                active_turn_id = add_execution_turn(exec_id, turn_number, current_prompt)
                turn_id = active_turn_id
                with _lock:
                    turn_thoughts[exec_id] = []

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
                    cost=metrics.get("cost"),
                    thoughts=metrics.get("thoughts")
                )
                writer.clear_logs()

                if metrics.get("agent_message"):
                    asyncio.run_coroutine_threadsafe(
                        q.put({"event": "agent_message", "data": {"content": metrics.get("agent_message")}}), loop
                    )

                update_execution_status(exec_id, "waiting_for_input")
                sys.stdout.write("\n[System: Gõ lệnh tiếp theo]\n")

                try:
                    msg = in_q.get(block=True, timeout=3600)
                except queue_module.Empty:
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
            traceback.print_exc()
            update_execution_status(exec_id, "error")
        finally:
            if 'runner' in locals() and hasattr(runner, 'close_session'):
                runner.close_session()
            clear_thread_writer()
            asyncio.run_coroutine_threadsafe(q.put(None), loop)
            cleanup_execution(exec_id)

    thread = threading.Thread(target=run_task_thread)
    thread.start()

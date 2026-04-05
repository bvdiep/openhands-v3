import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """execution_queues = {} # For SSE output stream
execution_inputs = {} # For input messages"""

new_str = """execution_queues = {} # For SSE output stream
execution_inputs = {} # For input messages
execution_thoughts = {} # For current thought"""

content = content.replace(old_str, new_str)

old_str2 = """            def on_thought(thought):
                asyncio.run_coroutine_threadsafe(q.put({"event": "agent_thought", "data": {"content": thought}}), loop)"""

new_str2 = """            def on_thought(thought):
                execution_thoughts[exec_id] = thought
                asyncio.run_coroutine_threadsafe(q.put({"event": "agent_thought", "data": {"content": thought}}), loop)"""

content = content.replace(old_str2, new_str2)

old_str3 = """            if exec_id in execution_queues:
                del execution_queues[exec_id]
            if exec_id in execution_inputs:
                del execution_inputs[exec_id]"""

new_str3 = """            if exec_id in execution_queues:
                del execution_queues[exec_id]
            if exec_id in execution_inputs:
                del execution_inputs[exec_id]
            if exec_id in execution_thoughts:
                del execution_thoughts[exec_id]"""

content = content.replace(old_str3, new_str3)

with open('main.py', 'w') as f:
    f.write(content)

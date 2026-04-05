import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """            from engine.runner import TaskRunner
            runner = TaskRunner(workspace=workspace, model=model, mcp_config=mcp_config)"""

new_str = """            from engine.runner import TaskRunner
            def on_thought(thought):
                asyncio.run_coroutine_threadsafe(q.put({"event": "agent_thought", "data": {"content": thought}}), loop)
            runner = TaskRunner(workspace=workspace, model=model, mcp_config=mcp_config, on_thought=on_thought)"""

content = content.replace(old_str, new_str)

old_str2 = """                update_turn_status(
                    turn_id, status, writer.get_logs(),
                    agent_message=metrics.get("agent_message"),
                    prompt_tokens=metrics.get("prompt_tokens"),
                    completion_tokens=metrics.get("completion_tokens"),
                    total_tokens=metrics.get("total_tokens"),
                    cost=metrics.get("cost"),
                    reasoning_tokens=metrics.get("reasoning_tokens"),
                    cache_read_tokens=metrics.get("cache_read_tokens"),
                    cache_write_tokens=metrics.get("cache_write_tokens"),
                    latency=metrics.get("latency")
                )"""

new_str2 = """                import json
                thoughts_json = json.dumps(metrics.get("thoughts", [])) if metrics.get("thoughts") else None
                update_turn_status(
                    turn_id, status, writer.get_logs(),
                    agent_message=metrics.get("agent_message"),
                    prompt_tokens=metrics.get("prompt_tokens"),
                    completion_tokens=metrics.get("completion_tokens"),
                    total_tokens=metrics.get("total_tokens"),
                    cost=metrics.get("cost"),
                    reasoning_tokens=metrics.get("reasoning_tokens"),
                    cache_read_tokens=metrics.get("cache_read_tokens"),
                    cache_write_tokens=metrics.get("cache_write_tokens"),
                    latency=metrics.get("latency"),
                    thoughts=thoughts_json
                )"""

content = content.replace(old_str2, new_str2)

with open('main.py', 'w') as f:
    f.write(content)

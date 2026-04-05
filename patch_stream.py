import re

with open('main.py', 'r') as f:
    content = f.read()

old_stream = """async def get_stream(exec_id: int):
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
                data_content = l.rstrip('\\n').rstrip('\\r')
                yield f"data: {data_content}\\n\\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})"""

new_stream = """async def get_stream(exec_id: int):
    async def event_stream():
        q = execution_queues.get(exec_id)
        if q is None: return
        while True:
            try:
                # Wait for 15 seconds for new data, otherwise send a heartbeat
                line = await asyncio.wait_for(q.get(), timeout=15.0)
            except asyncio.TimeoutError:
                yield ": heartbeat\\n\\n"
                continue
            except asyncio.CancelledError:
                break
                
            if line is None:
                await asyncio.sleep(0.1)
                break
            lines = line.splitlines(keepends=True)
            for l in lines:
                data_content = l.rstrip('\\n').rstrip('\\r')
                yield f"data: {data_content}\\n\\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})"""

content = content.replace(old_stream, new_stream)

with open('main.py', 'w') as f:
    f.write(content)


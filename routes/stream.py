import asyncio
from starlette.responses import StreamingResponse
import json

from services.execution import execution_queues


def register(app):
    @app.get("/stream/{exec_id}")
    async def get_stream(exec_id: int):
        async def event_stream():
            q = execution_queues.get(exec_id)
            if q is None:
                return
            while True:
                try:
                    line = await asyncio.wait_for(q.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
                    continue
                except asyncio.CancelledError:
                    break
                if line is None:
                    await asyncio.sleep(0.1)
                    break
                if isinstance(line, dict):
                    yield f"event: {line['event']}\ndata: {json.dumps(line['data'])}\n\n"
                    continue
                for l in line.splitlines(keepends=True):
                    data_content = l.rstrip("\n").rstrip("\r")
                    yield f"data: {data_content}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

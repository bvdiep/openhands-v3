import asyncio
import json
import queue as queue_module
from starlette.responses import JSONResponse

from db.queries import add_execution, get_execution
from engine.config import get_mcp_config
from services.execution import (
    execution_inputs,
    execution_thoughts,
    register_execution,
    start_execution_thread,
)


def register(app):
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
        in_q = queue_module.Queue()
        register_execution(exec_id, q, in_q)

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

        in_q = execution_inputs.get(exec_id)
        if in_q:
            in_q.put(prompt)
            return JSONResponse({"status": "message_sent"})
        return JSONResponse({"error": "Execution not found or not waiting for input"}, status_code=404)

    @app.get("/api/execute/{exec_id}/status")
    def api_execute_status(exec_id: int):
        exec_data = get_execution(exec_id)
        if not exec_data:
            return JSONResponse({"error": "Execution not found"}, status_code=404)

        last_turn = exec_data["turns"][-1] if exec_data["turns"] else None
        total_tokens = sum(t.get("total_tokens", 0) for t in exec_data["turns"])
        total_cost = sum(t.get("cost", 0.0) for t in exec_data["turns"])

        response_data = {
            "status": exec_data["status"],
            "last_agent_message": last_turn["agent_message"] if last_turn else None,
            "current_turn": last_turn["turn_number"] if last_turn else 0,
            "metrics": {"total_tokens": total_tokens, "cost": total_cost},
        }
        if exec_data["status"] == "running" and exec_id in execution_thoughts:
            response_data["current_thought"] = execution_thoughts[exec_id]

        return JSONResponse(response_data)

    @app.get("/api/execute/{exec_id}/messages")
    def api_execute_messages(exec_id: int):
        exec_data = get_execution(exec_id)
        if not exec_data:
            return JSONResponse({"error": "Execution not found"}, status_code=404)

        messages = []
        for t in exec_data["turns"]:
            if t.get("agent_message"):
                msg = {
                    "turn_number": t["turn_number"],
                    "role": "agent",
                    "content": t["agent_message"],
                    "timestamp": t["created_at"],
                }
                if t.get("thoughts"):
                    try:
                        msg["thoughts"] = json.loads(t["thoughts"])
                    except (json.JSONDecodeError, TypeError):
                        msg["thoughts"] = []
                messages.append(msg)

        return JSONResponse({"execution_id": exec_id, "messages": messages})

    @app.post("/api/execute/{exec_id}/stop")
    def api_execute_stop(exec_id: int):
        in_q = execution_inputs.get(exec_id)
        if in_q:
            in_q.put("__STOP__")
            return JSONResponse({"status": "stop_signal_sent"})
        return JSONResponse({"error": "Execution not found or not active"}, status_code=404)

import re

with open('main.py', 'r') as f:
    content = f.read()

api_endpoints = """
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
        
    return JSONResponse({
        "status": exec_data["status"],
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
"""

# Insert before serve()
serve_idx = content.rfind('serve()')
content = content[:serve_idx] + api_endpoints + "\n" + content[serve_idx:]

with open('main.py', 'w') as f:
    f.write(content)


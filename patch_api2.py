import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """@app.get("/api/execute/{exec_id}/status")
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
    })"""

new_str = """@app.get("/api/execute/{exec_id}/status")
def api_execute_status(exec_id: int):
    exec_data = get_execution(exec_id)
    if not exec_data:
        return JSONResponse({"error": "Execution not found"}, status_code=404)

    last_turn = exec_data["turns"][-1] if exec_data["turns"] else None
    total_tokens = sum(t.get("total_tokens", 0) for t in exec_data["turns"])
    total_cost = sum(t.get("cost", 0.0) for t in exec_data["turns"])

    return JSONResponse({
        "status": exec_data["status"],
        "last_agent_message": last_turn["agent_message"] if last_turn else None,
        "current_turn": last_turn["turn_number"] if last_turn else 0,
        "metrics": {
            "total_tokens": total_tokens,
            "cost": total_cost
        }
    })

@app.get("/api/execute/{exec_id}/messages")
def api_execute_messages(exec_id: int):
    exec_data = get_execution(exec_id)
    if not exec_data:
        return JSONResponse({"error": "Execution not found"}, status_code=404)

    messages = []
    for t in exec_data["turns"]:
        if t.get("agent_message"):
            messages.append({
                "turn_number": t["turn_number"],
                "role": "agent",
                "content": t["agent_message"],
                "timestamp": t["created_at"]
            })

    return JSONResponse({
        "execution_id": exec_id,
        "messages": messages
    })"""

content = content.replace(old_str, new_str)

with open('main.py', 'w') as f:
    f.write(content)

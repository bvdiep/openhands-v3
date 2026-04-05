import re

with open('main.py', 'r') as f:
    content = f.read()

old_str = """    return JSONResponse({
        "status": exec_data["status"],
        "last_agent_message": last_turn["agent_message"] if last_turn else None,
        "current_turn": last_turn["turn_number"] if last_turn else 0,
        "metrics": {
            "total_tokens": total_tokens,
            "cost": total_cost
        }
    })"""

new_str = """    response_data = {
        "status": exec_data["status"],
        "last_agent_message": last_turn["agent_message"] if last_turn else None,
        "current_turn": last_turn["turn_number"] if last_turn else 0,
        "metrics": {
            "total_tokens": total_tokens,
            "cost": total_cost
        }
    }
    if exec_data["status"] == "running" and exec_id in execution_thoughts:
        response_data["current_thought"] = execution_thoughts[exec_id]

    return JSONResponse(response_data)"""

content = content.replace(old_str, new_str)

with open('main.py', 'w') as f:
    f.write(content)

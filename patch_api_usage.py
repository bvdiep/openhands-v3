import re

with open('API_USAGE.md', 'r') as f:
    content = f.read()

old_str = """  "status": "waiting_for_input",
  "last_agent_message": "I have listed the files in the directory. What would you like me to do next?",
  "current_turn": 1,
  "metrics": {
    "total_tokens": 1500,
    "cost": 0.015
  }
}"""

new_str = """  "status": "running",
  "last_agent_message": "I have listed the files in the directory. What would you like me to do next?",
  "current_turn": 1,
  "metrics": {
    "total_tokens": 1500,
    "cost": 0.015
  },
  "current_thought": "I need to check the contents of the src directory next."
}"""

content = content.replace(old_str, new_str)

old_str2 = """      "turn_number": 1,
      "role": "agent",
      "content": "I will start by listing the files in the directory...",
      "timestamp": "2024-03-21T10:00:00"
    },"""

new_str2 = """      "turn_number": 1,
      "role": "agent",
      "content": "I will start by listing the files in the directory...",
      "timestamp": "2024-03-21T10:00:00",
      "thoughts": [
        "I should use the ls command to see what files are here.",
        "The directory contains several python files."
      ]
    },"""

content = content.replace(old_str2, new_str2)

with open('API_USAGE.md', 'w') as f:
    f.write(content)

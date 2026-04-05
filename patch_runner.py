import re

with open('engine/runner.py', 'r') as f:
    content = f.read()

old_str = """    def __init__(
        self,
        workspace: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Tool]] = None,
        agent_name: str = "OpenHands-Agent",
        mcp_config: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ):"""

new_str = """    def __init__(
        self,
        workspace: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Tool]] = None,
        agent_name: str = "OpenHands-Agent",
        mcp_config: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        on_thought: Optional[callable] = None
    ):"""

content = content.replace(old_str, new_str)

old_str2 = """        if system_prompt:
            agent_kwargs["system_prompt"] = system_prompt

        self.agent = Agent(**agent_kwargs)

        # Ensure workspace exists
        os.makedirs(self.workspace, exist_ok=True)"""

new_str2 = """        if system_prompt:
            agent_kwargs["system_prompt"] = system_prompt

        self.agent = Agent(**agent_kwargs)
        self.on_thought = on_thought
        self._current_turn_thoughts = []

        # Ensure workspace exists
        os.makedirs(self.workspace, exist_ok=True)"""

content = content.replace(old_str2, new_str2)

old_str3 = """    def _on_event(self, event: Event):
        try:
            if isinstance(event, MessageEvent):"""

new_str3 = """    def _on_event(self, event: Event):
        try:
            if isinstance(event, ActionEvent):
                action = getattr(event, 'action', None)
                if action:
                    thought = getattr(action, 'thought', None)
                    if thought:
                        self._current_turn_thoughts.append(thought)
                        if self.on_thought:
                            self.on_thought(thought)
                    if type(action).__name__ == 'FinishAction':
                        msg = getattr(action, 'message', '')
                        if msg:
                            self._agent_messages.append(msg)
            elif isinstance(event, MessageEvent):"""

content = content.replace(old_str3, new_str3)

old_str4 = """            elif isinstance(event, ActionEvent):
                action = getattr(event, 'action', None)
                if action and type(action).__name__ == 'FinishAction':
                    msg = getattr(action, 'message', '')
                    if msg:
                        self._agent_messages.append(msg)"""

new_str4 = """"""

content = content.replace(old_str4, new_str4)

old_str5 = """    def send_task(self, task_prompt: str, success_message: str = "Nhiệm vụ hoàn tất!"):
        \"\"\"Send a task to an existing session.\"\"\"
        metrics = {}
        if not hasattr(self, 'conversation') or self.conversation is None:
            print("\\n❌ Lỗi: Session chưa được khởi tạo.")
            return False, metrics

        try:
            num_before = len(self._agent_messages)
            self.conversation.send_message(task_prompt)
            print("--- Đang thực thi ---")
            self.conversation.run()"""

new_str5 = """    def send_task(self, task_prompt: str, success_message: str = "Nhiệm vụ hoàn tất!"):
        \"\"\"Send a task to an existing session.\"\"\"
        metrics = {}
        if not hasattr(self, 'conversation') or self.conversation is None:
            print("\\n❌ Lỗi: Session chưa được khởi tạo.")
            return False, metrics

        try:
            num_before = len(self._agent_messages)
            self._current_turn_thoughts = []
            self.conversation.send_message(task_prompt)
            print("--- Đang thực thi ---")
            self.conversation.run()"""

content = content.replace(old_str5, new_str5)

old_str6 = """                    "cache_write_tokens": tu.cache_write_tokens or 0,
                    "latency": m.response_latencies[-1].latency if m.response_latencies else 0.0,
                    "agent_message": new_messages[-1] if new_messages else ""
                }"""

new_str6 = """                    "cache_write_tokens": tu.cache_write_tokens or 0,
                    "latency": m.response_latencies[-1].latency if m.response_latencies else 0.0,
                    "agent_message": new_messages[-1] if new_messages else "",
                    "thoughts": self._current_turn_thoughts.copy()
                }"""

content = content.replace(old_str6, new_str6)

with open('engine/runner.py', 'w') as f:
    f.write(content)

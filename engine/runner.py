from engine.config import DEFAULT_LLM_MODEL
from engine.config import LLM_TEMPERATURE
from typing import List, Optional, Dict, Any
import os
import traceback
from datetime import datetime
from openhands.sdk import LLM, Agent, AgentContext, Conversation, Tool
from openhands.sdk.event import Event, MessageEvent, ActionEvent, ObservationEvent
from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.browser_use import BrowserToolSet
from openhands.tools.task import TaskToolSet

from .config import get_model_api_key_and_base_url

class TaskRunner:
    def __init__(
        self,
        workspace: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Tool]] = None,
        agent_name: str = "OpenHands-Agent",
        mcp_config: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        on_thought: Optional[callable] = None,
        load_public_skills: bool = True,
        load_user_skills: bool = True,
    ):
        """
        Initialize the TaskRunner.
        
        Args:
            workspace: Path to the workspace directory.
            model: Optional model override with provider prefix (e.g., "litellm/model-name" or "gemini/model-name"). Defaults to LLM_MODEL env var or "gemini/gemma-4-31b-it".
            temperature: Optional temperature override.
            tools: Optional list of tools. Defaults to Terminal, FileEditor, and Browser.
            agent_name: Name of the agent.
            mcp_config: Optional MCP configuration.
            system_prompt: Optional system prompt for the agent.
            on_thought: Optional callback for thought events.
            load_public_skills: Whether to load public skills.
            load_user_skills: Whether to load user skills.
        """
        self.workspace = os.path.abspath(os.path.expanduser(workspace))
        get_model = model or DEFAULT_LLM_MODEL
        # prefix = get_model.split('/', 1)[0].lower()
        # if prefix != 'litellm':
        #     self.model = get_model
        # else:
        #     self.model = get_model.split('/', 1)[1]
        self.model, self.api_key, self.base_url = get_model_api_key_and_base_url(get_model)
        self.temperature = temperature if temperature is not None else LLM_TEMPERATURE
        
        # Default tools if none provided
        self.tools = tools if tools is not None else [
            Tool(name=TerminalTool.name),
            Tool(name=FileEditorTool.name),
            Tool(name=BrowserToolSet.name),
            Tool(name=TaskToolSet.name)
        ]
        
        # Initialize LLM using shared config
        self.llm = LLM(
            model=self.model,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=self.temperature,
        )
        
        # Setup AgentContext with skills
        self.agent_context = AgentContext(
            load_public_skills=load_public_skills,
            load_user_skills=load_user_skills,
        )

        # Setup Agent
        agent_kwargs = {
            "llm": self.llm,
            "tools": self.tools,
            "name": agent_name,
            "agent_context": self.agent_context,
        }
        if mcp_config:
            agent_kwargs["mcp_config"] = mcp_config
        if system_prompt:
            agent_kwargs["system_prompt"] = system_prompt
            
        self.agent = Agent(**agent_kwargs)
        self.on_thought = on_thought
        self._agent_messages = []
        self._current_turn_thoughts = []
        self._pending_thought = "" # To capture thoughts from MessageEvent
        
        # Ensure workspace exists
        os.makedirs(self.workspace, exist_ok=True)
            
    def start_session(self):
        """Initialize the single conversation session."""
        print(f"🚀 OpenHands Runner session starting at: {self.workspace}")
        print(f"🤖 Model: {self.model}")
        metrics = {}
        self._agent_messages = []
        try:
            self.conversation = Conversation(
                agent=self.agent, 
                workspace=self.workspace,
                callbacks=[self._on_event]
            )
            return True, metrics
        except Exception as e:
            print(f"\n❌ Lỗi khởi tạo session: {e}")
            traceback.print_exc()
            return False, metrics

    def _extract_thought_metadata(self, obj: Any) -> tuple[str, str]:
        """Trích xuất (reasoning, summary) từ một đối tượng bất kỳ của SDK một cách an toàn."""
        # 1. Tìm reasoning/thought
        reasoning = (getattr(obj, 'reasoning_content', None) or 
                     getattr(obj, 'thought', None))
        
        # Xử lý nếu thought là danh sách (Sequence[TextContent] hoặc raw list)
        if isinstance(reasoning, (list, tuple)):
            reasoning = "\n".join([t.text if hasattr(t, 'text') else str(t) for t in reasoning])
        elif hasattr(reasoning, 'text'):
            reasoning = reasoning.text
            
        # Dữ liệu thô dự phòng từ __dict__ hoặc metadata
        if not reasoning:
            if hasattr(obj, 'metadata') and isinstance(obj.metadata, dict):
                reasoning = obj.metadata.get('thought') or obj.metadata.get('reasoning')
            if not reasoning and hasattr(obj, '__dict__'):
                reasoning = obj.__dict__.get('reasoning') or obj.__dict__.get('thought')

        # 2. Tìm hoặc tự tạo summary
        summary = getattr(obj, 'summary', None)
        if not summary and reasoning:
            # Lấy dòng đầu tiên sạch (không Markdown) làm summary
            first_line = str(reasoning).strip().split('\n')[0].replace('#', '').strip()
            summary = first_line[:100]
            
        return str(reasoning or ""), str(summary or "")

    def _on_event(self, event: Event):
        try:
            reasoning, summary = "", ""
            step_name = "Thought"

            if isinstance(event, ActionEvent):
                action = getattr(event, 'action', None)
                if not action:
                    return
                
                step_name = type(action).__name__
                # Thử trích xuất từ action (chứa thought cụ thể cho action đó)
                reasoning, summary = self._extract_thought_metadata(action)
                # Nếu action không có, thử trích xuất từ event bọc nó
                if not reasoning:
                    reasoning, summary = self._extract_thought_metadata(event)
                
                # Cơ chế dự phòng: dùng pending thought từ tin nhắn trước đó
                if not reasoning and self._pending_thought:
                    reasoning = self._pending_thought
                    if not summary:
                        summary = reasoning.strip().split('\n')[0].replace('#', '').strip()[:100]
                
                # Reset pending thought sau khi đã gắn vào một Action
                self._pending_thought = ""

                # Ghi nhận agent message nếu là FinishAction
                if step_name == 'FinishAction':
                    msg = getattr(action, 'message', '')
                    if msg: self._agent_messages.append(msg)

            elif isinstance(event, MessageEvent):
                if getattr(event, 'source', '') in ['agent', 'model']:
                    # SDK có thể để thông tin trong chính event hoặc llm_message
                    llm_msg = event if hasattr(event, 'role') else getattr(event, 'llm_message', None)
                    if not llm_msg: return

                    step_name = "Deep Reasoning" if getattr(llm_msg, 'role', '') == 'thought' else "Model Thought"
                    
                    # 1. Trích xuất reasoning trực tiếp
                    reasoning, summary = self._extract_thought_metadata(llm_msg)
                    
                    # 2. Duyệt qua các blocks nội dung (cho MessageEvent phức hợp)
                    msg_content = getattr(llm_msg, 'content', [])
                    if isinstance(msg_content, list):
                        content_thoughts = []
                        text_parts = []
                        for part in msg_content:
                            p_type = getattr(part, 'type', '')
                            if p_type == 'thought':
                                content_thoughts.append(getattr(part, 'thought', ''))
                            elif p_type == 'text':
                                text_parts.append(getattr(part, 'text', ''))
                        
                        if content_thoughts:
                            reasoning = (reasoning + "\n" + "\n".join(content_thoughts)).strip()
                        
                        if text_parts:
                            combined_text = "".join(text_parts)
                            self._agent_messages.append(combined_text)
                            # Lưu text làm pending thought cho action tiếp theo nếu action đó thiếu reasoning
                            self._pending_thought = combined_text
                    elif isinstance(msg_content, str) and msg_content:
                        self._agent_messages.append(msg_content)
                        self._pending_thought = msg_content

            # Nếu tìm thấy bất kỳ reasoning nào, lưu vào thoughts của turn hiện tại
            if reasoning:
                thought_data = {
                    "step": step_name,
                    "summary": summary or f"Executing {step_name}",
                    "reasoning": reasoning,
                    "timestamp": datetime.now().isoformat()
                }
                self._current_turn_thoughts.append(thought_data)
                if self.on_thought:
                    self.on_thought(thought_data)

        except Exception:
            pass

    def send_task(self, task_prompt: str, success_message: str = "Nhiệm vụ hoàn tất!"):
        """Send a task to an existing session."""
        metrics = {}
        if not hasattr(self, 'conversation') or self.conversation is None:
            print("\n❌ Lỗi: Session chưa được khởi tạo.")
            return False, metrics

        try:
            num_before = len(self._agent_messages)
            self._current_turn_thoughts = []
            self._pending_thought = ""
            self.conversation.send_message(task_prompt)
            print("--- Đang thực thi ---")
            self.conversation.run()
            
            # Extract metrics
            if hasattr(self.llm, 'metrics'):
                m = self.llm.metrics
                tu = m.accumulated_token_usage
                new_messages = self._agent_messages[num_before:]
                metrics = {
                    "prompt_tokens": tu.prompt_tokens or 0,
                    "completion_tokens": tu.completion_tokens or 0,
                    "total_tokens": (tu.prompt_tokens or 0) + (tu.completion_tokens or 0),
                    "cost": m.accumulated_cost or 0.0,
                    "reasoning_tokens": tu.reasoning_tokens or 0,
                    "cache_read_tokens": tu.cache_read_tokens or 0,
                    "cache_write_tokens": tu.cache_write_tokens or 0,
                    "latency": m.response_latencies[-1].latency if m.response_latencies else 0.0,
                    "agent_message": new_messages[-1] if new_messages else "",
                    "thoughts": self._current_turn_thoughts.copy()
                }
            print(f"\n✅ {success_message}")
            return True, metrics
        except Exception as e:
            print(f"\n❌ Lỗi thực thi: {e}")
            traceback.print_exc()
            return False, metrics

    def close_session(self):
        """Close the active session."""
        if hasattr(self, 'conversation') and self.conversation:
            try:
                self.conversation.close()
            except Exception as e:
                print(f"Lỗi khi đóng session: {e}")
            self.conversation = None

    def run(self, task_prompt: str, success_message: str = "Nhiệm vụ hoàn tất!"):
        """
        Execute the task (Single Turn) - Backward compatibility.
        
        Args:
            task_prompt: The prompt describing the task to perform.
            success_message: Message to display upon successful completion.
            
        Returns:
            tuple: (bool, dict) - (Success status, Metrics dictionary)
        """
        success_init, metrics = self.start_session()
        if not success_init:
            return False, metrics
            
        try:
            success, run_metrics = self.send_task(task_prompt, success_message)
            # Update metrics if needed, but start_session metrics are empty
            return success, run_metrics
        finally:
            self.close_session()

def run_task(task_prompt: str, **kwargs):
    """
    Convenience function for quick task execution.
    
    Args:
        task_prompt: The prompt describing the task.
        **kwargs: Arguments passed to TaskRunner constructor and run method.
            - workspace (required)
            - model (optional)
            - tools (optional)
            - agent_name (optional)
            - mcp_config (optional)
            - system_prompt (optional)
            - success_message (optional)
            
    Returns:
        tuple: (bool, dict) - (Success status, Metrics dictionary)
            
    Usage:
        success, metrics = run_task(task_prompt="...", workspace="./path", model="...")
    """
    success_msg = kwargs.pop('success_message', "Nhiệm vụ hoàn tất!")
    
    # Check if workspace is provided
    if 'workspace' not in kwargs:
        # Try to infer workspace or use default
        kwargs['workspace'] = os.path.join(os.getcwd(), "workspaces", "default")
        
    runner = TaskRunner(**kwargs)
    return runner.run(task_prompt, success_message=success_msg)

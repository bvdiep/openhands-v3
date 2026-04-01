from typing import List, Optional, Dict, Any
import os
import traceback
from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.browser_use import BrowserToolSet

# Integration with existing config
from .config import LLM_CONFIG

class TaskRunner:
    def __init__(
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
    ):
        """
        Initialize the TaskRunner.
        
        Args:
            workspace: Path to the workspace directory.
            model: Optional model override (e.g., "openai/gpt-4").
            tools: Optional list of tools. Defaults to Terminal, FileEditor, and Browser.
            agent_name: Name of the agent.
            mcp_config: Optional MCP configuration.
            system_prompt: Optional system prompt for the agent.
        """
        self.workspace = os.path.abspath(os.path.expanduser(workspace))
        self.model = model or LLM_CONFIG.get("model")
        self.base_url = base_url or LLM_CONFIG.get("base_url")
        self.api_key = api_key or LLM_CONFIG.get("api_key")
        self.temperature = temperature if temperature is not None else LLM_CONFIG.get("temperature", 0.0)
        
        # Default tools if none provided
        self.tools = tools if tools is not None else [
            Tool(name=TerminalTool.name),
            Tool(name=FileEditorTool.name),
            Tool(name=BrowserToolSet.name)
        ]
        
        # Initialize LLM using shared config
        self.llm = LLM(
            model=self.model,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=self.temperature,
        )
        
        # Setup Agent
        agent_kwargs = {
            "llm": self.llm,
            "tools": self.tools,
            "name": agent_name
        }
        if mcp_config:
            agent_kwargs["mcp_config"] = mcp_config
        if system_prompt:
            agent_kwargs["system_prompt"] = system_prompt
            
        self.agent = Agent(**agent_kwargs)
        
        # Ensure workspace exists
        os.makedirs(self.workspace, exist_ok=True)
            
    def start_session(self):
        """Initialize the single conversation session."""
        print(f"🚀 OpenHands Runner session starting at: {self.workspace}")
        print(f"🤖 Model: {self.model}")
        metrics = {}
        try:
            self.conversation = Conversation(agent=self.agent, workspace=self.workspace)
            return True, metrics
        except Exception as e:
            print(f"\n❌ Lỗi khởi tạo session: {e}")
            traceback.print_exc()
            return False, metrics

    def send_task(self, task_prompt: str, success_message: str = "Nhiệm vụ hoàn tất!"):
        """Send a task to an existing session."""
        metrics = {}
        if not hasattr(self, 'conversation') or self.conversation is None:
            print("\n❌ Lỗi: Session chưa được khởi tạo.")
            return False, metrics

        try:
            self.conversation.send_message(task_prompt)
            print("--- Đang thực thi ---")
            self.conversation.run()
            
            # Extract metrics
            if hasattr(self.llm, 'metrics'):
                m = self.llm.metrics
                metrics = {
                    "prompt_tokens": m.accumulated_token_usage.prompt_tokens,
                    "completion_tokens": m.accumulated_token_usage.completion_tokens,
                    "total_tokens": m.accumulated_token_usage.prompt_tokens + m.accumulated_token_usage.completion_tokens,
                    "cost": m.accumulated_cost
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

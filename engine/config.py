"""
Shared configuration for OpenHands projects.
This file contains base configuration that is shared across all projects.
Project-specific settings should be in project_config.py files.
"""
import os
import uuid
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ProjectConfig:
    """
    Base configuration class for a project.
    Each project should create an instance of this with their specific settings.
    """
    
    def __init__(
        self,
        project_name: str,
        target_url: Optional[str] = None,
        workspace_subdir: Optional[str] = None,
        tech_stack: Optional[Dict[str, str]] = None
    ):
        """
        Initialize project configuration.
        
        Args:
            project_name: Unique name for the project (e.g., "ofood-clone-v1")
            target_url: Target URL to clone (if applicable)
            workspace_subdir: Subdirectory name in workspace (defaults to project_name)
            tech_stack: Technology stack configuration
        """
        self.project_name = project_name
        self.target_url = target_url
        
        # Generate unique conversation ID for this project
        self.conversation_id = uuid.uuid5(uuid.NAMESPACE_DNS, project_name)
        
        # Directory Structure
        self.engine_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(self.engine_dir)
        
        # Workspace for this specific project
        workspace_name = workspace_subdir or project_name
        self.workspace_path = os.path.join(self.base_dir, "workspaces", workspace_name)
        self.metadata_path = os.path.join(self.workspace_path, ".metadata")
        
        # Shared persistence directory (organized by conversation_id)
        self.persistence_dir = os.path.join(self.engine_dir, ".conversations")
        
        # File Names (can be overridden by subclass)
        self.plan_filename = "PROJECT_PLAN.md"
        self.project_log_filename = "PROJECT_LOG.md"
        self.style_guide_filename = ".metadata/style_guide.json"
        self.prompt_steps_filename = "prompts_steps.txt"
        
        # Full Paths
        self.plan_full_path = os.path.join(self.workspace_path, self.plan_filename)
        self.log_full_path = os.path.join(self.workspace_path, self.project_log_filename)
        self.style_guide_full_path = os.path.join(self.workspace_path, self.style_guide_filename)
        self.prompt_steps_full_path = os.path.join(self.workspace_path, self.prompt_steps_filename)
        
        # Tech Stack (default or custom)
        self.tech_stack = tech_stack or {
            "framework": "Vite + React",
            "styling": "Tailwind CSS",
            "language": "TypeScript",
            "icons": "Lucide React"
        }
    
    def ensure_directories(self):
        """Ensure required directories exist. Call this explicitly when needed."""
        for path in [self.workspace_path, self.metadata_path, self.persistence_dir]:
            os.makedirs(path, exist_ok=True)
    
    def get_logging_rules(self) -> str:
        """Get logging rules for this project."""
        return f"""
QUY TẮC GHI NHẬT KÝ BẮT BUỘC:
1. TRACEABILITY: Sau mỗi hành động quan trọng (truy cập URL, chạy lệnh terminal thành công, tạo file), 
   bạn PHẢI cập nhật vào file '{self.log_full_path}'.
2. STRUCTURE: File '{self.log_full_path}' phải bao gồm:
   - [Timestamp]: Mô tả ngắn gọn hành động vừa thực hiện.
   - [Outcome]: Kết quả thu được.
   - [Decision]: Lý do bạn chọn giải pháp này.
3. SNAPSHOTS: Khi phân tích UI, hãy lưu các thông số CSS quan trọng 
   (colors, spacing, font-family) vào file '{self.style_guide_full_path}'.
"""


# Default LLM Configuration (shared across all projects)
def get_api_key() -> str:
    """Get API key from environment with validation."""
    api_key = os.getenv("LITELLM_KEY", "master-diep1234321")
    if not api_key:
        raise ValueError(
            "LITELLM_KEY environment variable is not set. "
            "Please set it before running the pipeline."
        )
    return api_key

# Gọi litellm proxy
# LLM_CONFIG: Dict[str, Any] = {
#     "model": "openai/sonnet-4",
#     "api_key": get_api_key(),  # Fails fast if not set
#     "base_url": "http://localhost:4000/v1",
#     "temperature": 0.0
# }
# Gọi Gemini trực tiếp
LLM_CONFIG: Dict[str, Any] = {
    "model": "gemini/gemini-3-flash-preview",
    "api_key": os.getenv("GEMINI_API_KEY", "no-gemini-api-key"),  # Fails fast if not set
    "base_url": None,
    "temperature": 0.0
}


# Global instance - will be set by each project
# Using a simple global for now, but consider contextvars for thread-safety
_current_project_config: Optional[ProjectConfig] = None


def set_project_config(config: ProjectConfig):
    """
    Set the current project configuration.
    
    Args:
        config: ProjectConfig instance to set as current
    """
    global _current_project_config
    _current_project_config = config
    # Ensure directories exist when config is set
    config.ensure_directories()


def get_project_config() -> ProjectConfig:
    """
    Get the current project configuration.
    
    Returns:
        ProjectConfig: The current project configuration
        
    Raises:
        RuntimeError: If project configuration has not been set
    """
    if _current_project_config is None:
        raise RuntimeError(
            "Project configuration not set. "
            "Please call set_project_config() before using the pipeline."
        )
    return _current_project_config

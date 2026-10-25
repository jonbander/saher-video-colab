import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8000
    comfyui_base_url: str = "http://127.0.0.1:8188"
    workflow_path: Path = Path("workflows/your-approved-workflow-api.json")
    prompt_node_id: str = "6"
    prompt_input: str = "text"
    timeout_seconds: float = 30

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            host=os.getenv("SAHER_HOST", "127.0.0.1"),
            port=int(os.getenv("SAHER_PORT", "8000")),
            comfyui_base_url=os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:8188"),
            workflow_path=Path(os.getenv("COMFYUI_WORKFLOW_PATH", "workflows/your-approved-workflow-api.json")),
            prompt_node_id=os.getenv("COMFYUI_PROMPT_NODE_ID", "6"),
            prompt_input=os.getenv("COMFYUI_PROMPT_INPUT", "text"),
            timeout_seconds=float(os.getenv("COMFYUI_TIMEOUT_SECONDS", "30")),
        )

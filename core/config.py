"""Load an agent's config.yaml (and .env secrets)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"


@dataclass
class AgentConfig:
    name: str
    dir: Path
    model: str = "claude-opus-5-5"
    effort: str = "high"
    max_tokens: int = 16000
    max_iterations: int = 30
    fallbacks: bool = True
    prompt_files: list[str] = field(default_factory=lambda: ["system_prompt.md"])
    variables: dict = field(default_factory=dict)

    @property
    def output_dir(self) -> Path:
        return ROOT / "outputs" / self.name

    @property
    def log_dir(self) -> Path:
        return ROOT / "logs" / self.name


def load_config(agent_name: str) -> AgentConfig:
    load_dotenv(ROOT / ".env")
    agent_dir = AGENTS_DIR / agent_name
    cfg_path = agent_dir / "config.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"No config.yaml for agent '{agent_name}' at {cfg_path}")
    raw = yaml.safe_load(cfg_path.read_text()) or {}
    cfg = AgentConfig(name=agent_name, dir=agent_dir, **raw)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cfg.log_dir.mkdir(parents=True, exist_ok=True)
    # Built-in variables every prompt can use
    cfg.variables = {
        "root": str(ROOT),
        "data_dir": str(ROOT / "data"),
        "output_dir": str(cfg.output_dir),
        **cfg.variables,
    }
    return cfg

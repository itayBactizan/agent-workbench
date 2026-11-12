"""Load Markdown prompt files and fill {{variables}}."""
from __future__ import annotations

import re

from .config import AgentConfig

_VAR = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render(text: str, variables: dict) -> str:
    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in variables:
            raise KeyError(f"Prompt uses {{{{{key}}}}} but it is not defined in config.yaml variables")
        return str(variables[key])

    return _VAR.sub(sub, text)


def load_system_prompt(cfg: AgentConfig) -> str:
    """Concatenate the agent's prompt files in order (e.g. a shared style guide + the agent prompt)."""
    parts = []
    for rel in cfg.prompt_files:
        path = (cfg.dir / rel).resolve()
        parts.append(render(path.read_text(), cfg.variables))
    # Keep the prompt identical between runs (no timestamps) so prompt caching works.
    return "\n\n".join(parts)

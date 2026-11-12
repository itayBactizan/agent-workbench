"""Tools for this agent. Keep it to 3–5 tools; add more only when a real task needs one."""
from anthropic import beta_tool

from core.config import AgentConfig


def build_tools(cfg: AgentConfig):
    @beta_tool
    def example_tool(query: str) -> str:
        """Describe what the tool does, when to use it, and what it returns.

        Args:
            query: What this argument means.
        """
        return f"result for {query}"

    cleanup = None  # e.g. close DB connections or kernels
    return [example_tool], cleanup

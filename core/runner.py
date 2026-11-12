"""Shared agent loop: loads an agent, runs it, logs every step."""
from __future__ import annotations

import importlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import anthropic

from .config import AgentConfig, load_config
from .prompts import load_system_prompt


@dataclass
class RunResult:
    final_text: str
    tool_calls: list[str] = field(default_factory=list)
    stop_reason: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    log_path: Path | None = None


class Agent:
    """An agent = config.yaml + system_prompt.md + tools.py (build_tools(cfg) -> (tools, cleanup))."""

    def __init__(self, name: str, verbose: bool = True):
        self.cfg: AgentConfig = load_config(name)
        self.system = load_system_prompt(self.cfg)
        tools_mod = importlib.import_module(f"agents.{name}.tools")
        self.tools, self._cleanup = tools_mod.build_tools(self.cfg)
        self.client = anthropic.Anthropic()
        self.verbose = verbose

    def _request_kwargs(self) -> dict:
        kw = dict(
            model=self.cfg.model,
            max_tokens=self.cfg.max_tokens,
            # Cache the stable system prompt + tools across loop iterations
            system=[{"type": "text", "text": self.system, "cache_control": {"type": "ephemeral"}}],
            output_config={"effort": self.cfg.effort},
            tools=self.tools,
            max_iterations=self.cfg.max_iterations,
        )
        if self.cfg.fallbacks:
            # If a request is declined by a safety classifier, re-run it on a fallback model
            kw["betas"] = ["server-side-fallback-2026-07-01"]
            kw["fallbacks"] = "default"
        return kw

    def run(self, task: str) -> RunResult:
        start = time.time()
        log_path = self.cfg.log_dir / f"{datetime.now():%Y%m%d-%H%M%S}.jsonl"
        result = RunResult(final_text="", log_path=log_path)

        with log_path.open("w") as log:
            log.write(json.dumps({"event": "start", "task": task, "model": self.cfg.model,
                                  "effort": self.cfg.effort}) + "\n")
            runner = self.client.beta.messages.tool_runner(
                messages=[{"role": "user", "content": task}], **self._request_kwargs()
            )
            for msg in runner:
                result.stop_reason = msg.stop_reason
                result.input_tokens += msg.usage.input_tokens
                result.output_tokens += msg.usage.output_tokens
                texts = []
                for block in msg.content:
                    if block.type == "text":
                        texts.append(block.text)
                        if self.verbose:
                            print(f"\n🤖 {block.text}")
                    elif block.type == "tool_use":
                        result.tool_calls.append(block.name)
                        if self.verbose:
                            print(f"🔧 {block.name}({json.dumps(block.input)[:200]})")
                if texts:
                    result.final_text = "\n".join(texts)
                log.write(json.dumps({"event": "message", "stop_reason": msg.stop_reason,
                                      "content": [b.model_dump() for b in msg.content],
                                      "usage": msg.usage.model_dump()}, default=str) + "\n")

            result.seconds = round(time.time() - start, 1)
            log.write(json.dumps({"event": "end", "stop_reason": result.stop_reason,
                                  "tool_calls": result.tool_calls, "seconds": result.seconds,
                                  "input_tokens": result.input_tokens,
                                  "output_tokens": result.output_tokens}) + "\n")

        if result.stop_reason == "refusal":
            print("\n⚠️  The request was declined (stop_reason=refusal).")
        elif result.stop_reason == "max_tokens":
            print("\n⚠️  Output hit max_tokens; consider raising it in config.yaml.")
        elif result.stop_reason == "tool_use":
            print(f"\n⚠️  Stopped at max_iterations={self.cfg.max_iterations} before finishing.")
        if self.verbose:
            print(f"\n— done in {result.seconds}s · {len(result.tool_calls)} tool calls · "
                  f"{result.input_tokens:,} in / {result.output_tokens:,} out tokens · log: {log_path}")
        return result

    def close(self):
        if self._cleanup:
            self._cleanup()

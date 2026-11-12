"""A persistent, isolated Python kernel for model-written code.

The code runs in a separate Jupyter kernel process, not inside the agent
process, so variables persist between calls (like a notebook), a timeout can
stop runaway code, and a crash doesn't kill the agent.

Production: run the kernel inside a Docker container with no network access
and the data folder mounted read-only. This local version is fine for
personal experiments only, because the code can still touch your files.
"""
from __future__ import annotations

import os
import queue
import re

from jupyter_client.manager import KernelManager

MAX_OUTPUT_CHARS = 8000
_ANSI = re.compile(r"\x1b\[[0-9;]*m")  # strip terminal colors from tracebacks


class PythonSandbox:
    def __init__(self, cwd: str, setup_code: str = "", timeout: int = 120):
        self.timeout = timeout
        # IPC (local socket) instead of TCP on Linux/macOS
        transport = "tcp" if os.name == "nt" else "ipc"
        self.km = KernelManager(kernel_name="python3", transport=transport)
        self.km.start_kernel(cwd=cwd)
        self.kc = self.km.client()
        self.kc.start_channels()
        self.kc.wait_for_ready(timeout=60)
        if setup_code:
            self.run(setup_code)

    def run(self, code: str) -> str:
        msg_id = self.kc.execute(code)
        out: list[str] = []
        while True:
            try:
                msg = self.kc.get_iopub_msg(timeout=self.timeout)
            except queue.Empty:
                self.km.interrupt_kernel()
                out.append(f"\n[TimeoutError: execution exceeded {self.timeout}s and was interrupted]")
                break
            if msg["parent_header"].get("msg_id") != msg_id:
                continue
            t, c = msg["msg_type"], msg["content"]
            if t == "stream":
                out.append(c["text"])
            elif t in ("execute_result", "display_data"):
                out.append(c["data"].get("text/plain", "[non-text output]") + "\n")
            elif t == "error":
                out.append("\n".join(c["traceback"]))
            elif t == "status" and c["execution_state"] == "idle":
                break
        text = _ANSI.sub("", "".join(out)).strip() or "(no output — use print() to see results)"
        if len(text) > MAX_OUTPUT_CHARS:
            text = text[:2000] + "\n...[truncated]...\n" + text[-(MAX_OUTPUT_CHARS - 2000):]
        return text

    def close(self):
        self.kc.stop_channels()
        self.km.shutdown_kernel(now=True)

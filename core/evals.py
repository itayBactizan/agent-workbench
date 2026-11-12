"""Eval harness: run every case in agents/<name>/evals/cases.yaml and check the results.

Supported checks per case (all optional):
  must_call:      [tool names that must be called at least once]
  must_not_call:  [tool names that must never be called]
  must_contain:   [phrases the final answer OR the files in files_exist must contain (case-insensitive)]
  files_exist:    [paths relative to the agent's output dir]
  max_tool_calls: int
"""
from __future__ import annotations

import json
from datetime import datetime

import yaml

from .runner import Agent


def check_case(case: dict, result, out_dir) -> list[str]:
    failures = []
    for t in case.get("must_call", []):
        if t not in result.tool_calls:
            failures.append(f"did not call {t}")
    for t in case.get("must_not_call", []):
        if t in result.tool_calls:
            failures.append(f"called forbidden tool {t}")
    if "max_tool_calls" in case and len(result.tool_calls) > case["max_tool_calls"]:
        failures.append(f"{len(result.tool_calls)} tool calls > {case['max_tool_calls']}")
    corpus = result.final_text
    for f in case.get("files_exist", []):
        p = out_dir / f
        if not p.exists():
            failures.append(f"missing file {f}")
        else:
            corpus += "\n" + p.read_text(errors="ignore")
    for phrase in case.get("must_contain", []):
        if phrase.lower() not in corpus.lower():
            failures.append(f"output missing '{phrase}'")
    if result.stop_reason not in ("end_turn", None):
        failures.append(f"stop_reason={result.stop_reason}")
    return failures


def run_evals(agent_name: str, only: str | None = None) -> float:
    agent = Agent(agent_name, verbose=False)
    cases = yaml.safe_load((agent.cfg.dir / "evals" / "cases.yaml").read_text())
    if only:
        cases = [c for c in cases if c["id"] == only]
    rows, passed = [], 0
    try:
        for case in cases:
            for f in case.get("files_exist", []):  # start each case clean
                (agent.cfg.output_dir / f).unlink(missing_ok=True)
            print(f"▶ {case['id']} ...", end=" ", flush=True)
            result = agent.run(case["task"])
            failures = check_case(case, result, agent.cfg.output_dir)
            ok = not failures
            passed += ok
            print("✅ PASS" if ok else "❌ FAIL: " + "; ".join(failures))
            rows.append({"id": case["id"], "pass": ok, "failures": failures,
                         "tool_calls": len(result.tool_calls), "seconds": result.seconds,
                         "output_tokens": result.output_tokens, "log": str(result.log_path)})
    finally:
        agent.close()

    score = passed / max(len(cases), 1)
    report = agent.cfg.log_dir / f"eval-{datetime.now():%Y%m%d-%H%M%S}.json"
    report.write_text(json.dumps({"score": score, "cases": rows}, indent=2))
    print(f"\nScore: {passed}/{len(cases)} ({score:.0%}) · report: {report}")
    return score

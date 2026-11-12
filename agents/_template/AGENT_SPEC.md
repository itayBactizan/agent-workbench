# Agent Spec: <Agent Name>

> Fill this in BEFORE writing prompts or code. If you can't answer a section, the agent isn't ready to build.

## 1. Purpose
_One paragraph: what job does this agent do, and what does it save?_

## 2. Users and trigger
- **User:**
- **Trigger:** _CLI / schedule / Slack / API_

## 3. Is an agent the right tool?
| Criterion | Answer |
|---|---|
| Multi-step, hard to script in advance? | |
| Worth the cost and latency? | |
| Can errors be caught (review, tests, rollback)? | |
_If any answer is "no", use a single LLM call or a fixed workflow instead._

## 4. Scope
**In scope:**
**Out of scope (must never do):**

## 5. Tools
| Tool | Read/Write | Why |
|---|---|---|

## 6. Definition of done
_What exact output proves the task is finished?_

## 7. Risks and mitigations
| Risk | Mitigation |
|---|---|

## 8. Success metrics
- Eval pass rate ≥ __% on `evals/cases.yaml`
- Cost / latency budget:

## 9. Owner and version
- Owner:
- Changelog: v0.1

# Agent Spec: Data Analyst

> Design doc for humans. Fill this in **before** writing prompts or code.
> Review it with a teammate. Update it when scope changes.

## 1. Purpose
Speed up exploratory analysis and baseline modeling. Takes a question plus a
dataset and returns a reproducible analysis with charts and a written report.

## 2. Users and trigger
- **User:** data scientists and analysts on the team.
- **Trigger:** CLI, `python run.py data_analyst "<question>"`.

## 3. Is an agent the right tool?
| Criterion | Answer |
|---|---|
| Multi-step, hard to script in advance? | Yes. Exploration depends on what the data shows |
| Worth the cost and latency? | Yes. Replaces 1–3 hours of EDA |
| Can errors be caught? | Yes. Code and logs are reviewable; a human reads the report |

## 4. Scope
**In scope:** loading CSV/Parquet, profiling, cleaning (in memory), EDA, charts,
statistical tests, baseline ML models with proper validation, a Markdown report.

**Out of scope (must never do):**
- Modify or delete files in `data/`
- Access the network or production databases
- Present results without stating assumptions and caveats

## 5. Tools
| Tool | Read/Write | Why |
|---|---|---|
| `list_files` | read | Discover available datasets |
| `profile_dataset` | read | Fast, consistent first look at a file |
| `run_python` | sandboxed | All analysis and modeling |
| `save_report` | write (outputs only) | Final deliverable |

## 6. Definition of done
`outputs/data_analyst/report.md` exists and contains: question, data used,
method, findings with numbers, charts referenced, caveats/assumptions, next steps.

## 7. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Model-written code damages files | Separate kernel; Docker with read-only data mount in production |
| Data leakage or overfitting in models | Prompt rules + eval case that checks validation is reported |
| Confident but wrong claims | Must report sample sizes, uncertainty and caveats |
| Runaway cost | `max_iterations` in config; output truncation in tools |
| Sensitive data sent to the API | Only use data approved for the API; mask PII before loading |

## 8. Success metrics
- Eval pass rate ≥ 90% on `evals/cases.yaml`
- Median run < 5 min and < 30 tool calls
- Team feedback: report is usable with only light edits

## 9. Owner and version
- Owner: _your name_
- Changelog: v0.1 initial version

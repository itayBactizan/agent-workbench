# Agent Workbench

A reusable structure for building LLM agents at work. Every agent follows the
same process and folder layout, so a new agent is mostly writing Markdown and
a few tool functions. The plumbing is shared.

```
agent-workbench/
├── README.md                 ← this file: the process
├── requirements.txt
├── .env.example
├── run.py                    ← CLI: python run.py <agent> "question"
├── core/                     ← shared plumbing (don't copy per agent)
│   ├── config.py             ← loads config.yaml + .env
│   ├── prompts.py            ← loads prompt .md files, fills {{variables}}
│   ├── runner.py             ← agent loop, logging, guardrails
│   ├── sandbox.py            ← isolated Python kernel for code execution
│   └── evals.py              ← eval harness
├── agents/
│   ├── _template/            ← copy this to start a new agent
│   └── data_analyst/         ← the first real agent
│       ├── AGENT_SPEC.md     ← design doc (for humans): goal, scope, risks
│       ├── system_prompt.md  ← instructions to the LLM
│       ├── config.yaml       ← model, effort, limits, paths
│       ├── tools.py          ← the agent's tools
│       └── evals/cases.yaml  ← test questions + checks
├── data/                     ← input data (read-only for agents)
├── outputs/<agent>/          ← reports, charts the agent produces
└── logs/<agent>/             ← one JSONL transcript per run
```

---

## The process: 7 steps for every agent

### 1. Specify: write `AGENT_SPEC.md` first (no code)
Answer the questions in the template: who uses it, which job it does, what
"done" looks like, what it must **never** do, which tools it needs, and how
you will measure it. If you can't fill this in, the agent isn't ready to build.
Also check whether it really needs an agent. A task that one LLM call can do
(summarize, classify, extract) doesn't need a loop.

### 2. Write the instructions: `system_prompt.md`
Use the fixed sections from the template:

| Section | Purpose |
|---|---|
| Role | Who the agent is, in one or two sentences |
| Context | Environment facts: paths, data, users. Uses `{{variables}}` |
| Workflow | The steps it should usually follow |
| Rules | Hard constraints, each with the *reason* (models follow rules better when they know why) |
| Tool guidance | When to use which tool |
| Output format | Exactly what the final deliverable looks like |

Keep it in Markdown so it diffs in git and non-programmers can review it.
Write it like a brief to a smart new colleague, not like a list of shouted rules.

### 3. Build the tools: `tools.py`
- Start with as few tools as possible (3–5). Add one only when a real task needs it.
- The docstring **is** the tool description the model reads. Say what the tool does, when to use it, and what it returns.
- Tools return short text. Truncate big outputs, because they cost tokens and fill the context.
- Return errors as text (don't raise), so the agent can read the error and fix its approach.
- Default to read-only. Any tool that writes, deletes or sends something needs a guard.

### 4. Configure: `config.yaml`
Model, effort, iteration limit, paths and prompt variables. No secrets. Keys go in `.env`.

### 5. Evaluate: `evals/cases.yaml`
Write 10–20 realistic questions **before** you tune the prompt. Each case has
automatic checks (it called the right tools, the report exists, it mentions
key terms). Run:
```bash
python run.py data_analyst --eval
```
Re-run after **every** prompt or tool change. That's how you know a change helped.

### 6. Iterate using the logs
Every run writes `logs/<agent>/<timestamp>.jsonl` with each step. Read failed
runs, find the cause (unclear instruction? missing tool? bad tool output?), and
fix that one thing. Then re-run the evals.

### 7. Harden and ship
- Run model-written code in the sandbox (Docker for production, see `core/sandbox.py`).
- Give the agent read-only credentials for databases.
- Set `max_iterations` to cap cost per run.
- Version prompts in git. Note the eval score in the commit message.

---

## Create a new agent in 5 minutes

```bash
cp -r agents/_template agents/my_new_agent
```
Then fill in `AGENT_SPEC.md`, `system_prompt.md`, `config.yaml`, `tools.py`,
and `evals/cases.yaml`, and run:
```bash
python run.py my_new_agent "your question"
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
python run.py data_analyst "Explore data/sample.csv and summarize the main patterns"
```

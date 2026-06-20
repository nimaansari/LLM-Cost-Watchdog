# Cost Watchdog 💰

> A Claude/OpenClaw agent skill that prices LLM calls live, detects runaway
> loops in code, enforces budgets, and reports spend — so an agent never racks
> up a surprise bill.

---

## 📊 The Problem

Usage-based LLM billing makes cost a real operational risk. Early agent
frameworks have caused teams to rack up **thousands of dollars overnight** from
a single infinite loop. Cost Watchdog makes API cost a first-class concern:
priced at write time, budgeted at check time, surfaced in reports.

---

## 💡 What It Does

- ✅ **Live multi-source pricing** — LiteLLM (direct-provider) → OpenRouter →
  curated static fallback, with on-disk caching, a TTL, and offline modes.
- ✅ **AST code auditing** — flags unbounded `while True` + API calls,
  self-recursion with no depth bound, missing `max_tokens`, and batching
  candidates, each with line numbers.
- ✅ **Usage logging** — every call (tokens, cost, cache, provider) appended to
  a JSONL log; per-session and 24h/7d/30d rollups.
- ✅ **Passive HTTP capture** — optionally monkey-patches `httpx` so calls from
  the official SDKs are logged with no code changes.
- ✅ **Model detection** — layered probes to identify which model the agent is
  running.
- ✅ **Token validation** — compares the built-in heuristic counter against a
  provider's authoritative count API.

---

## 🛠️ Requirements

- Python 3.8+
- **No required third-party packages** for the core CLI (uses only the stdlib).
- Optional extras unlock more:
  - `httpx` — passive HTTP capture (most SDKs already pull this in)
  - `tiktoken` — exact OpenAI token counts in `validate-tokens`
  - `anthropic` — authoritative Anthropic token counts in `validate-tokens`

```bash
pip install -r requirements.txt   # installs the optional extras
```

Live pricing fetches from the network on first use and caches for 24h. Set
`CW_OFFLINE=1` to never touch the network, or `CW_STATIC_ONLY=1` to use only the
bundled `references/pricing.md`.

---

## 📖 Usage

All commands run through the unified CLI:

```bash
python3 scripts/cost_watchdog.py <command> [args]
```

| Command | What it does |
|---|---|
| `session` | Spend totals from the usage log — calls, tokens, cost, top models. |
| `report` | 24h / 7d / 30d windows with the top model per window. |
| `tail [--once] [--interval N]` | Watch OpenClaw session logs and log every assistant turn. |
| `detect [--json]` | Identify which model the agent is currently using. |
| `audit <file.py> ...` | AST scan for cost risks (unbounded loops, recursion, missing `max_tokens`). |
| `price <model>` | Live pricing for one model, with source + cache age. |
| `estimate <model> --input-tokens N --output-tokens N [--iterations K]` | Project cost for K iterations of a call. |
| `alternatives <model> [--input-tokens N] [--output-tokens N] [--min-savings 0.5]` | Cheaper same-billing-unit models. |
| `errors [--limit N]` | Recent swallowed exceptions (silent failures made visible). |
| `validate-tokens <model> [--text ...]` | Compare the heuristic token count to the provider's API. |
| `reset [--yes] [--all]` | Clear the usage log (`--all` also deletes rolled daily files). |

### Examples

```bash
python3 scripts/cost_watchdog.py price gpt-4o
python3 scripts/cost_watchdog.py estimate claude-sonnet-4-6 --input-tokens 1000000 --output-tokens 100000
python3 scripts/cost_watchdog.py audit src/agent.py
python3 scripts/cost_watchdog.py alternatives claude-sonnet-4-6 --min-savings 0.5
python3 scripts/cost_watchdog.py report
```

### Passive HTTP capture (optional)

```python
from http_capture import install_global_capture
install_global_capture()   # call once at process start; logs SDK calls via httpx
```

Non-streaming JSON responses from known LLM hosts are logged automatically.
Streaming (`text/event-stream`) responses are noted as gaps — use the per-SDK
wrappers in `tracker.py` for streaming coverage.

---

## 🧩 Auxiliary scripts

Two extra tools ship as standalone scripts (run directly):

```bash
# Visual spend reports / ASCII charts
python3 scripts/cost-visualizer.py daily | weekly | tasks | providers | chart

# Priority-aware budgeting + learning from past tasks
python3 scripts/smart-budget.py set 5.00 --priority=high
python3 scripts/smart-budget.py estimate <task-type> <tokens> <model>
python3 scripts/smart-budget.py alternatives <model> --savings=50
python3 scripts/smart-budget.py learn <task-type> <cost> <tokens> <minutes>
```

> Note: these are not yet wired into `cost_watchdog.py`'s subcommands; they run
> as their own scripts.

---

## 📁 Project Structure

```
cost-watchdog/
├── SKILL.md                    # Skill definition, triggers, command reference
├── README.md
├── requirements.txt            # optional extras
├── .env.example
├── references/
│   ├── pricing.md              # auto-generated pricing tables (offline fallback)
│   ├── optimization.md         # cost-optimization strategies
│   ├── patterns.md             # dangerous patterns & safe alternatives
│   └── calculators.md          # token counting & cost calculation
└── scripts/
    ├── cost_watchdog.py        # unified CLI (entry point)
    ├── _pricing.py             # pricing router (source selection)
    ├── _sources.py             # LiteLLM / OpenRouter / static sources + cache + breaker
    ├── refresh_pricing.py      # regenerate references/pricing.md
    ├── usage_log.py            # JSONL usage log + rollups
    ├── tracker.py              # per-SDK wrappers (openai / anthropic / ...)
    ├── http_capture.py         # passive httpx-transport capture
    ├── tokenizer.py            # heuristic + exact token counting
    ├── detect_model.py         # model-detection probes
    ├── code_audit.py           # AST cost-risk auditor
    ├── openclaw_tailer.py      # tail OpenClaw session logs
    ├── model_canon.py          # model-name canonicalization
    ├── errors.py               # error log (swallowed-exception visibility)
    ├── io_utils.py             # atomic JSON writes, etc.
    ├── cost-visualizer.py      # (aux) charts & reports
    ├── smart-budget.py         # (aux) priority budgeting + learning
    └── optimized-calculator.py # (aux) cheaper-alternative search
```

---

## ⚙️ Environment Variables

| Variable | Effect |
|---|---|
| `CW_OFFLINE=1` | Never hit the network; serve from cache or static only. |
| `CW_STATIC_ONLY=1` | Skip network sources entirely (used by tests). |
| `CW_PRICE_TTL_SECONDS=N` | Cache TTL for live pricing (default 86400; `0` = always refetch). |

---

## 🚦 Budget Status Levels

| Status | Threshold | Action |
|--------|-----------|--------|
| ✅ **ok** | 0–50% | Normal operation |
| ⚠️ **caution** | 50–80% | Monitor spending |
| ⚠️ **warning** | 80–95% | Consider wrapping up |
| 🚨 **critical** | 95–100% | Finish current task only |
| ❌ **over_budget** | >100% | Stop or increase budget |

---

## 🧪 Tests

```bash
python3 -m pytest tests/        # or: python3 -m unittest discover tests
```

The suite runs offline (`CW_STATIC_ONLY=1`) and covers the CLI, pricing
sources, the AST auditor, and HTTP capture.

---

## 🌐 Pricing Coverage

Pricing is pulled live from **LiteLLM** (hundreds of models, direct-provider
rates) and **OpenRouter** (aggregator routing), with a curated
`references/pricing.md` as an always-available offline fallback. Regenerate the
static table with:

```bash
python3 scripts/refresh_pricing.py
```

---

## 📚 Documentation

- **[SKILL.md](SKILL.md)** — skill definition, triggers, full command reference
- **[references/pricing.md](references/pricing.md)** — pricing tables
- **[references/optimization.md](references/optimization.md)** — optimization strategies
- **[references/patterns.md](references/patterns.md)** — dangerous patterns & safe alternatives
- **[references/calculators.md](references/calculators.md)** — token counting & cost calculation

---

## 📄 License

MIT

## 👤 Author

Nima Ansari

# Cost Watchdog

> An AI agent skill that monitors API spend per task, flags runaway loops, and estimates cost before executing expensive operations.

## The Problem

Pricing models are now debated almost as intensely as capabilities, especially as more tools move toward usage-based billing. Early versions of AutoGen caused one team to rack up **$2,400 in API costs overnight** due to an infinite loop. This is a real and recurring pain point.

## What It Does

Cost Watchdog is a capability layer for AI agents that makes API cost a first-class concern:

- **Pre-execution estimates** — Know what an operation will cost before running it
- **Runaway loop detection** — Flags dangerous patterns: unbounded loops, recursive agents, missing retry limits
- **Budget enforcement** — Set spending ceilings with warnings at 50%, 80%, and 95%
- **Cost optimization** — Suggests model tiering, caching, batching, and early termination
- **Codebase auditing** — Scans agent code for cost-unsafe patterns with specific fixes
- **Multi-provider pricing** — Current rates for Anthropic, OpenAI, Google, Mistral, and Cohere

## Installation

### As a Personal Skill (all projects)

```bash
# Symlink or copy to Claude Code skills directory
ln -s ~/Documents/cost-watchdog ~/.claude/skills/cost-watchdog
```

### As a Project Skill (single project)

```bash
# Copy to project skills directory
cp -r ~/Documents/cost-watchdog .claude/skills/cost-watchdog
```

## Usage

### Manual Invocation

```
/cost-watchdog estimate          # Estimate cost of current task
/cost-watchdog report            # Session spend report
/cost-watchdog set-budget 10.00  # Set $10 budget
/cost-watchdog check             # Check spend vs budget
/cost-watchdog audit src/        # Audit code for cost risks
/cost-watchdog price gpt-4o     # Look up model pricing
```

### Automatic Invocation

The skill auto-activates when Claude detects:
- API calls to LLM providers in code
- Agent loops or recursive patterns
- Cost/budget/billing discussions
- Batch processing workflows

## File Structure

```
cost-watchdog/
├── SKILL.md                        # Main skill definition
├── README.md                       # This file
├── references/
│   ├── pricing.md                  # Current API pricing tables
│   ├── optimization.md             # Cost optimization strategies
│   ├── patterns.md                 # Dangerous patterns & safe alternatives
│   └── calculators.md              # Token counting & cost calculation code
└── scripts/                        # (future) automation scripts
```

## Covered Providers

| Provider | Models |
|----------|--------|
| Anthropic | Claude Opus 4.6, Sonnet 4.6, Haiku 4.5 |
| OpenAI | GPT-4o, GPT-4o-mini, GPT-4.1 family, o3, o3-mini, o4-mini |
| Google | Gemini 2.5 Pro/Flash, Gemini 2.0 Flash |
| Mistral | Large, Small, Codestral |
| Cohere | Command R+, Command R, Embed v3 |

## License

MIT

## Author

Nima Ansari

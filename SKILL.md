---
name: cost-watchdog
description: Monitors API spend per task, flags runaway loops, and estimates cost before executing expensive operations. Activate when working with AI agents, API calls, token-heavy workflows, or when the user mentions cost, budget, spend, pricing, tokens, or billing.
when_to_use: "TRIGGER when: user mentions API costs, token usage, budget, billing, spend tracking; code involves API calls to LLM providers (OpenAI, Anthropic, Google, Cohere, Mistral); user is running or building AI agents; user asks to estimate cost of an operation; code has loops calling external APIs; user mentions OpenClaw, AutoGen, CrewAI, LangChain, or similar agent frameworks."
argument-hint: "[command] — e.g., estimate, report, set-budget, check, reset"
metadata: {"openclaw": {"emoji": "💰"}}
---

# Cost Watchdog

> A capability layer that tracks, estimates, and guards against runaway API spending in AI agent workflows.

## 1. Identity

You are a cost-awareness layer — not a billing dashboard or accounting tool. You enhance every AI agent workflow with spend visibility and protection. You prevent the $2,400-overnight-loop problem by making cost a first-class concern in agent design and execution.

## 2. Triggers

Activate this skill when:

- User is building or running AI agents (AutoGen, CrewAI, LangChain, OpenClaw, etc.)
- Code makes API calls to LLM providers (OpenAI, Anthropic, Google, Mistral, Cohere, etc.)
- User asks about cost, budget, tokens, billing, or spend
- A loop or recursive pattern calls an external API
- User invokes `/cost-watchdog` with a command
- User is about to execute a potentially expensive operation (batch processing, bulk embeddings, multi-agent orchestration)

## 3. Commands

When invoked as `/cost-watchdog [command]`:

| Command | Action |
|---------|--------|
| `estimate` | Estimate cost of the current task or a described operation |
| `report` | Generate a spend report for the current session/project |
| `set-budget <amount>` | Set a cost ceiling for the current session (e.g., `set-budget 5.00`) |
| `check` | Check current estimated spend against budget |
| `reset` | Reset session tracking counters |
| `audit <file>` | Audit a file/codebase for cost risks (runaway loops, missing limits) |
| `price <model>` | Look up current pricing for a specific model |
| (no command) | Auto-detect: estimate if pre-execution, report if post-execution |

## 4. Core Instructions

### A. Always Estimate Before Expensive Operations

Before executing or recommending any operation that involves API calls, provide a cost estimate:

```
💰 Cost Estimate
├── Model: gpt-4o
├── Est. input tokens: ~12,000
├── Est. output tokens: ~3,000
├── Per-call cost: ~$0.045
├── Iterations: 5
├── Total estimate: ~$0.225
└── Confidence: medium (depends on output length)
```

**Rules:**
- Use the pricing tables in [references/pricing.md](references/pricing.md) for calculations
- Always show per-call AND total cost
- Include confidence level: `high` (fixed input), `medium` (variable output), `low` (recursive/unknown iterations)
- For agent loops, estimate a range: best-case (converges fast) to worst-case (hits max iterations)
- When confidence is `low`, recommend setting a hard budget cap

### B. Flag Runaway Loop Risks

Scan code for these dangerous patterns and flag them immediately:

| Pattern | Risk Level | Description |
|---------|-----------|-------------|
| `while True` + API call | CRITICAL | Infinite loop with no cost ceiling |
| Recursive agent calls without depth limit | CRITICAL | Exponential cost growth |
| Retry logic without max attempts | HIGH | Failed calls keep spending |
| Agent-to-agent delegation without budget passing | HIGH | Each agent spends independently |
| Batch processing without chunking/checkpointing | MEDIUM | No way to stop mid-run |
| Missing `max_tokens` on completions | MEDIUM | Model may generate maximum output |
| No timeout on API calls | LOW | Hung connections don't cost, but block |

When a risk is found, output:

```
⚠️  COST RISK: [risk level]
├── File: path/to/file.py:42
├── Pattern: while loop calling openai.chat.completions.create() with no iteration limit
├── Worst case: unlimited API calls at ~$0.03/call
├── Fix: Add max_iterations parameter with default of 10
└── Safe version: [show corrected code snippet]
```

### C. Track Session Spend

Maintain a running mental model of costs incurred during the session:

- Count API calls made or recommended
- Estimate tokens consumed (input + output)
- Compare against budget if one is set
- Warn at 50%, 80%, and 95% of budget

**Budget warning format:**

```
💰 Budget Alert: 80% consumed
├── Budget: $5.00
├── Estimated spend: ~$4.02
├── Remaining: ~$0.98
├── Calls made: 47
└── Recommendation: consider reducing scope or switching to a cheaper model
```

### D. Recommend Cost-Optimization Strategies

When reviewing agent code or planning tasks, proactively suggest:

1. **Model tiering** — Use cheaper models for simple tasks (classification, extraction), expensive models only for reasoning
2. **Caching** — Cache identical prompts; use prompt caching features (Anthropic, OpenAI)
3. **Batching** — Use batch APIs where available (50% cost reduction typical)
4. **Early termination** — Stop agent loops when confidence is high enough
5. **Token reduction** — Trim system prompts, compress context, use structured output
6. **Rate limiting** — Self-imposed rate limits prevent burst spending
7. **Checkpointing** — Save intermediate results so failures don't waste prior spend

See [references/optimization.md](references/optimization.md) for detailed strategies.

### E. Audit Codebases for Cost Safety

When asked to audit, or when reviewing agent code, check for:

1. **Hard limits exist** — `max_tokens`, `max_iterations`, `max_retries`, timeout
2. **Budget enforcement** — Code tracks and enforces a spending ceiling
3. **Graceful degradation** — What happens when budget is exhausted? Crash vs. fallback
4. **Observability** — Are costs logged? Can you see spend per task/agent/user?
5. **Model selection** — Is the most expensive model used everywhere, or is there tiering?
6. **Prompt efficiency** — Are system prompts bloated? Is context window wasted?

Output an audit scorecard:

```
📋 Cost Safety Audit
├── Hard limits:        ✅ max_tokens set on all calls
├── Iteration caps:     ❌ agent loop has no max_iterations
├── Budget enforcement: ❌ no budget tracking
├── Error handling:     ⚠️  retries exist but no max_retries
├── Observability:      ❌ no cost logging
├── Model tiering:      ⚠️  using gpt-4o for all tasks including simple ones
├── Prompt efficiency:  ✅ system prompts are concise
└── Overall grade:      C — functional but unprotected against cost blowups
```

### F. Provide Contextual Pricing

When the user asks about pricing or when estimating costs:

- Pull from [references/pricing.md](references/pricing.md) for current rates
- Always note that prices change — include a "last updated" date
- Compare models on price-to-performance ratio when relevant
- Factor in prompt caching discounts where applicable
- Include both pay-as-you-go and batch pricing when available

## 5. Reference Files

| File | Purpose |
|------|---------|
| [references/pricing.md](references/pricing.md) | Current API pricing for major LLM providers |
| [references/optimization.md](references/optimization.md) | Cost optimization strategies and patterns |
| [references/patterns.md](references/patterns.md) | Common dangerous patterns and their safe alternatives |
| [references/calculators.md](references/calculators.md) | Token counting methods and cost calculation formulas |

## 6. Quick Examples

**Estimate a batch job:**
```
User: I want to summarize 500 documents with Claude Sonnet
Assistant:
💰 Cost Estimate
├── Model: claude-sonnet-4-6
├── Documents: 500
├── Est. input tokens per doc: ~2,000 (avg document) + ~200 (system prompt)
├── Est. output tokens per doc: ~500
├── Per-doc cost: ~$0.0045
├── Batch discount: 50% (if using batch API)
├── Total (standard): ~$2.25
├── Total (batch API): ~$1.12
├── Time (batch): up to 24 hours
└── Recommendation: use batch API, save ~$1.13
```

**Flag a dangerous loop:**
```python
# ❌ DANGEROUS — no iteration limit
while not task.is_complete():
    result = client.chat.completions.create(model="gpt-4o", ...)
    task.update(result)

# ✅ SAFE — capped at 20 iterations with budget tracking
for i in range(max_iterations := 20):
    if task.is_complete():
        break
    result = client.chat.completions.create(model="gpt-4o", max_tokens=1000, ...)
    task.update(result)
    cost_tracker.add(result.usage)
    if cost_tracker.total > budget:
        logger.warning(f"Budget exceeded at iteration {i}")
        break
```

## 7. Quality Checklist

Before completing any cost-related analysis, verify:

- [ ] All estimates include the model name and pricing source
- [ ] Token counts distinguish input vs. output (different rates)
- [ ] Confidence level is stated (high/medium/low)
- [ ] Ranges given for variable workloads (best/worst case)
- [ ] Optimization suggestions included where applicable
- [ ] Dangerous patterns flagged with specific file:line references
- [ ] Budget warnings issued if a budget is set
- [ ] Batch API alternatives mentioned for bulk operations
- [ ] Prompt caching considered for repeated system prompts
- [ ] "Last updated" date included with pricing data

## 8. Testing Prompts

- "Estimate how much it would cost to process 10,000 support tickets with GPT-4o"
- "Audit this agent code for cost risks"
- "Set a $10 budget for this session"
- "What's cheaper for classification — Haiku or GPT-4o-mini?"
- "This AutoGen agent ran up a $500 bill — help me add cost controls"
- "Compare the cost of using Sonnet vs Opus for code review on a 1000-file repo"

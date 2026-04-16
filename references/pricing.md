# API Pricing Reference

> Last updated: April 2026. Prices change frequently — verify at provider's pricing page before making financial decisions.

## Anthropic (Claude)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Prompt Cache Write | Prompt Cache Read | Batch Input | Batch Output | Context |
|-------|----------------------|------------------------|-------------------|-------------------|-------------|-------------|---------|
| Claude Opus 4.6 | $15.00 | $75.00 | $18.75 | $1.50 | $7.50 | $37.50 | 1M |
| Claude Sonnet 4.6 | $3.00 | $15.00 | $3.75 | $0.30 | $1.50 | $7.50 | 200K |
| Claude Haiku 4.5 | $0.80 | $4.00 | $1.00 | $0.08 | $0.40 | $2.00 | 200K |

**Notes:**
- Prompt caching: 90% discount on cache reads vs standard input
- Batch API: 50% discount, results within 24 hours
- Extended thinking tokens billed at output rate

## OpenAI

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Cached Input | Batch Input | Batch Output | Context |
|-------|----------------------|------------------------|-------------|-------------|-------------|---------|
| GPT-4o | $2.50 | $10.00 | $1.25 | $1.25 | $5.00 | 128K |
| GPT-4o-mini | $0.15 | $0.60 | $0.075 | $0.075 | $0.30 | 128K |
| GPT-4.1 | $2.00 | $8.00 | $0.50 | $1.00 | $4.00 | 1M |
| GPT-4.1-mini | $0.40 | $1.60 | $0.10 | $0.20 | $0.80 | 1M |
| GPT-4.1-nano | $0.10 | $0.40 | $0.025 | $0.05 | $0.20 | 1M |
| o3 | $10.00 | $40.00 | $2.50 | $5.00 | $20.00 | 200K |
| o3-mini | $1.10 | $4.40 | $0.275 | $0.55 | $2.20 | 200K |
| o4-mini | $1.10 | $4.40 | $0.275 | $0.55 | $2.20 | 200K |

**Notes:**
- Cached input: 50% discount (automatic for repeated prefixes)
- Batch API: 50% discount, 24-hour turnaround
- Reasoning tokens (o-series) billed at output rate

## Google (Gemini)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Context |
|-------|----------------------|------------------------|---------|
| Gemini 2.5 Pro | $1.25 / $2.50 | $10.00 / $15.00 | 1M |
| Gemini 2.5 Flash | $0.15 / $0.30 | $0.60 / $3.50 | 1M |
| Gemini 2.0 Flash | $0.10 | $0.40 | 1M |

**Notes:**
- Gemini 2.5 Pro: lower price for prompts <=200K tokens, higher for >200K
- Gemini 2.5 Flash: thinking tokens billed at higher output rate
- Free tier available with rate limits

## Mistral

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Context |
|-------|----------------------|------------------------|---------|
| Mistral Large | $2.00 | $6.00 | 128K |
| Mistral Small | $0.10 | $0.30 | 32K |
| Codestral | $0.30 | $0.90 | 256K |
| Mistral Embed | $0.10 | — | 8K |

## Cohere

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Context |
|-------|----------------------|------------------------|---------|
| Command R+ | $2.50 | $10.00 | 128K |
| Command R | $0.15 | $0.60 | 128K |
| Embed v3 | $0.10 | — | 512 |

## Groq

> Ultra-fast inference with open-source models. Pricing is very competitive.

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Context |
|-------|----------------------|------------------------|---------|
| Llama 3.1 405B | $2.50 | $10.00 | 128K |
| Llama 3.1 70B | $0.59 | $0.79 | 128K |
| Llama 3.1 8B | $0.05 | $0.08 | 128K |
| Llama 3.2 90B Vision | $0.90 | $0.90 | 128K |
| Llama 3.2 11B Vision | $0.18 | $0.18 | 128K |
| Mixtral 8x7B | $0.24 | $0.24 | 32K |
| Gemma 2 9B | $0.10 | $0.10 | 8K |
| DeepSeek-R1 | $0.14 | $0.28 | 64K |
| DeepSeek-V3 | $0.14 | $0.28 | 64K |

**Notes:**
- Groq uses per-second billing for some models, token pricing shown is equivalent
- Extremely fast inference (100+ tokens/sec typical)
- Free tier available for testing with rate limits

## DeepSeek

> Chinese LLM provider with competitive pricing and strong reasoning capabilities.

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Context |
|-------|----------------------|------------------------|---------|
| DeepSeek-R1 | $0.55 | $2.19 | 64K |
| DeepSeek-V3 | $0.14 | $0.28 | 64K |
| DeepSeek-Coder V2 | $0.14 | $0.28 | 128K |
| DeepSeek-LLM | $0.13 | $0.13 | 16K |

**Notes:**
- DeepSeek-R1: reasoning model, output tokens billed at higher rate
- Cache hit: $0.014 input (90% discount)
- Strong code generation capabilities

## Perplexity

> Search-enhanced models with real-time web knowledge.

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Context |
|-------|----------------------|------------------------|---------|
| Sonar Pro (3.5 Sonnet) | $3.00 | $15.00 | 200K |
| Sonar (70B) | $1.00 | $1.00 | 128K |
| Sonar Small (8B) | $0.20 | $0.20 | 128K |
| Pro (Claude 3.5 Sonnet) | $3.00 | $15.00 | 200K |

**Notes:**
- Includes real-time web search in responses
- Search queries may incur additional costs
- Good for research and fact-checking tasks

## OpenRouter (Aggregated Models)

> OpenRouter aggregates multiple providers. Prices vary by model and routing.

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Notes |
|-------|----------------------|------------------------|-------|
| Claude 3.5 Sonnet | $3.00 | $15.00 | Via Anthropic |
| Claude 3 Opus | $15.00 | $75.00 | Via Anthropic |
| Llama 3.1 405B | $2.50 | $10.00 | Via Groq/Together |
| Llama 3.1 70B | $0.59 | $0.79 | Via Groq |
| Mistral Large | $2.00 | $6.00 | Via Mistral |
| Gemini 2.0 Flash | $0.10 | $0.40 | Via Google |
| Qwen 2.5 72B | $0.40 | $0.40 | Via various |
| Yi-Large | $1.20 | $1.20 | Via various |
| Command R+ | $2.50 | $10.00 | Via Cohere |
| **Free tier models** | $0.00 | $0.00 | Limited availability |

**Notes:**
- OpenRouter routes to cheapest available provider
- Free tier models available (limited, lower quality)
- Some models have rate limits on free tier
- Check current routing at [openrouter.ai/docs](https://openrouter.ai/docs)

## Cost Comparison: Cheapest Options by Category

| Use Case | Cheapest Model | Cost (1M input + 100K output) |
|----------|----------------|-------------------------------|
| **Simple classification** | GPT-4.1-nano | $0.14 |
| **Code generation** | DeepSeek-Coder V2 | $0.17 |
| **Fast responses** | Groq Llama 3.2 8B | $0.06 |
| **Research with search** | Perplexity Sonar Small | $0.22 |
| **Reasoning tasks** | DeepSeek-V3 | $0.17 |
| **High quality general** | Gemini 2.0 Flash | $0.14 |
| **Best value premium** | Claude Haiku 4.5 | $1.20 |
| **Top tier quality** | Claude Sonnet 4.6 | $4.50 |

## Embedding Models (Comparison)

| Provider | Model | Price (per 1M tokens) | Dimensions | Context |
|----------|-------|----------------------|------------|---------|
| OpenAI | text-embedding-3-large | $0.13 | 3072 | 8K |
| OpenAI | text-embedding-3-small | $0.02 | 1536 | 8K |
| Cohere | embed-v3 | $0.10 | 1024 | 512 |
| Google | text-embedding-004 | $0.006 | 768 | 2K |
| Mistral | mistral-embed | $0.10 | 1024 | 8K |

## Quick Cost Comparison (1M input + 100K output)

A handy reference for comparing "typical task" costs across models:

| Model | Cost | Relative |
|-------|------|----------|
| GPT-4.1-nano | $0.14 | 1x (baseline) |
| GPT-4o-mini | $0.21 | 1.5x |
| Gemini 2.0 Flash | $0.14 | 1x |
| Gemini 2.5 Flash | $0.21 | 1.5x |
| Mistral Small | $0.13 | 0.9x |
| Claude Haiku 4.5 | $1.20 | 8.6x |
| Claude Sonnet 4.6 | $4.50 | 32x |
| GPT-4o | $3.50 | 25x |
| GPT-4.1 | $2.80 | 20x |
| Claude Opus 4.6 | $22.50 | 161x |
| o3 | $14.00 | 100x |

## Token Estimation Rules of Thumb

- 1 token ~ 4 characters (English)
- 1 token ~ 0.75 words (English)
- 1 page of text ~ 500 tokens
- 1 line of code ~ 10-20 tokens
- A typical system prompt ~ 200-500 tokens
- A 10K-line codebase ~ 150K-300K tokens
- JSON/structured output uses ~30% more tokens than plain text

# The Reasoning Layer

A platform-agnostic LLM routing intelligence layer. Sits in front of any agent or LLM call, logs every decision, and uses semantic memory to get smarter about which model to use over time.

**Works with any agent platform.** Pull it down, wire it to your calls, watch your token spend drop.

---

## What it does

Most LLM platforms route every call to the same model regardless of complexity. A memory filing task costs the same as a deep reasoning task. That's waste.

The Reasoning Layer fixes this with three components:

```
Input Request
      ↓
[Classifier Node]     → what kind of task is this?
      ↓
[ES Memory Node]      → what model worked for similar requests before?
      ↓
[Router Node]         → pick the right model
      ↓
[Execution Node]      → run the call
      ↓
[Logger Node]         → record decision + outcome
      ↑_______________|
      feedback loop - gets smarter over time
```

---

## Architecture

### `reasoning_layer.py` - The Logger
- SQLite-backed event store (swappable to Postgres)
- Captures every LLM call: model used, tokens, cost, latency, quality score
- `classifier_feedback` table for the learning loop
- Backend-agnostic interface: swap SQLite for Postgres by changing one line

### `es_layer.py` - The Memory Node
- Elasticsearch-backed semantic search over past routing decisions
- Embeds every request locally using `all-MiniLM-L6-v2` (no API calls, no cost)
- `find_similar()` - find past requests semantically similar to the current one
- `suggest_model()` - ask the graph what model worked best for requests like this
- Inspired by Doppel's graph engine approach: past decisions as connected entities, quality scores as edge weights

### `compressor.py` - The Compressor Node
Strips unnecessary context before it hits the model. Can also block call sites entirely.

Real data shows the problem: `Conversation Title` averages **91,816 input tokens** to generate a title. `Reply Suggestion` averages **125,077 tokens** for suggestions nobody asked for.

```python
from compressor import CompressorNode

compressor = CompressorNode()
result = compressor.compress(text, call_site="Conversation Title")

if result.blocked:
    return  # call site is disabled entirely - skip the LLM call
    
response = llm.call(result.compressed_text)  # lean context, not full history
print(result.summary())
# → [Conversation Title] conversation_title: 91,816 → 8,000 tokens (83,816 saved, 91% reduction)
```

**Customize via YAML** - no Python required:

```bash
cp compressor_config.example.yaml compressor_config.yaml
# edit call site names + strategies to match your setup
```

```yaml
call_sites:
  "My Title Generator":
    strategy: head_tail
  "My Reply Bot":
    blocked: true       # skip entirely - 100% token savings
  "My Memory Agent":
    strategy: memory_ops
    max_tokens: 3000
```

```python
compressor = CompressorNode.from_config("compressor_config.yaml")
```

| Strategy | Best for | Approach |
|----------|----------|----------|
| `head_tail` | Title generation, labeling | First + last chunk |
| `notification` | Push alerts, decisions | Recent context only |
| `memory_ops` | Filing, consolidation, retrieval | Strip personality sections |
| `reply_summary` | Summarization, reply drafts | 20% head + 80% tail |
| `truncate` | Everything else | Hard cut at token limit |

### `rl.py` - The CLI
```bash
python3 rl.py stats                          # token + cost summary by model
python3 rl.py viz                            # ASCII bar charts
python3 rl.py search "summarize messages"    # semantic search with similarity scores
python3 rl.py suggest "file memory notes"    # model recommendation from past data
python3 rl.py cost                           # spend breakdown
```

---

## Setup

### Option A: Docker Compose (recommended - no account needed)

```bash
git clone https://github.com/sarahkatebyte/spend-tracker
cd spend-tracker
docker compose up          # starts local Elasticsearch
docker compose run cli viz # ASCII cost + savings charts
docker compose run cli stats
docker compose run cli search "summarize recent messages"
```

Elasticsearch runs locally on port 9200. No API key, no cloud account. Your existing `spend.db` is mounted automatically.

### Option B: Elastic Cloud

```bash
pip install -r requirements.txt
```

Set environment variables:

```bash
export ES_HOST="https://your-deployment.us-central1.gcp.cloud.es.io:443"
export ES_API_KEY="your-api-key"
```

**Getting credentials:** [cloud.elastic.co](https://cloud.elastic.co) → Create deployment → Kibana → Stack Management → API Keys

Then run the smoke test:

```bash
python3 es_layer.py
```

You should see the index created, test events indexed, similarity search results, and a model suggestion.

---

## Wiring it to your agent

The logger is designed to wrap any LLM call:

```python
from reasoning_layer import ReasoningLogger, ReasoningEvent
from es_layer import ESMemoryNode

logger = ReasoningLogger()
es = ESMemoryNode()

# Before your LLM call - ask what worked before
suggested_model = es.suggest_model(request_text)

# Make your LLM call with the suggested model
# ...

# After your call - log the decision
event_id = logger.log(ReasoningEvent(
    call_site="your_call_site",
    task_type="memory_ops",           # or reasoning_heavy, simple_retrieval, creative, structured_output
    model_selected=suggested_model,
    input_tokens=response.usage.input_tokens,
    output_tokens=response.usage.output_tokens,
    cost_usd=calculated_cost,
    latency_ms=elapsed_ms,
    request_text=request_text,
))

# Index it so future calls can learn from it
es.index_event(
    event_id=event_id,
    request_text=request_text,
    task_type="memory_ops",
    model_selected=suggested_model,
    cost_usd=calculated_cost,
    quality_score=0.9,    # your quality signal here
)
```

### Task types

| Type | Description | Default tier |
|------|-------------|--------------|
| `reasoning_heavy` | Complex analysis, architecture, multi-step reasoning | Opus / highest |
| `memory_ops` | Filing, consolidation, retrieval, extraction | Haiku / cheapest |
| `simple_retrieval` | Lookups, short answers, structured output | Haiku / cheapest |
| `creative` | Writing, generation, open-ended | Sonnet / mid |
| `structured_output` | JSON, schema-constrained responses | Sonnet / mid |

---

## The learning loop

Every logged event with a quality score becomes training data for future routing decisions. The `suggest_model()` function finds semantically similar past requests and returns the model that produced the best outcomes.

Over time the layer stops being a rules engine and becomes experience-based. You don't retrain anything - the graph just gets denser.

---

## Roadmap

- [ ] Classifier node (auto-detect task type from request text)
- [ ] Router node (enforce routing rules + ES suggestions)
- [ ] Postgres backend
- [ ] Quality scorer (auto-evaluate response quality)
- [ ] GitHub Actions CI (pytest on every push)
- [ ] OpenTelemetry integration

### Kubernetes / EKS

The current Terraform runs Elasticsearch on EC2. The natural next step is migrating to EKS so the full reasoning layer (app + ES) runs on Kubernetes - the same architecture used by production-grade threat intelligence platforms.

The EKS path looks like:
- ES running as a StatefulSet with persistent volume claims
- Reasoning layer app as a Deployment behind a Service
- Horizontal pod autoscaling on the app layer
- Fluent Bit for log aggregation
- Prometheus + Grafana for cluster observability

EC2 is the right starting point. EKS is where this goes when it needs to scale.

---

## Built with

- [Elasticsearch](https://elastic.co) - semantic memory and search
- [sentence-transformers](https://www.sbert.net/) - local embeddings (all-MiniLM-L6-v2)
- SQLite - transactional event log

---

*Built by Sarah Haddon. Platform-agnostic by design.*

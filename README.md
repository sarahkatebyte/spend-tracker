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

---

## Setup

### 1. Install dependencies

```bash
pip install elasticsearch sentence-transformers
```

### 2. Set environment variables

```bash
cp .env.example .env
# fill in your ES_HOST and ES_API_KEY
```

Or export directly:

```bash
export ES_HOST="https://your-deployment.us-central1.gcp.cloud.es.io:443"
export ES_API_KEY="your-api-key"
```

**Getting Elasticsearch:**
- Free tier: [cloud.elastic.co](https://cloud.elastic.co) → Create deployment → Open Kibana → Stack Management → API Keys
- Self-hosted: any ES 8.x instance works

### 3. Run the smoke test

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
- [ ] Dashboard (extend existing Streamlit spend tracker)
- [ ] OpenTelemetry integration

---

## Built with

- [Elasticsearch](https://elastic.co) - semantic memory and search
- [sentence-transformers](https://www.sbert.net/) - local embeddings (all-MiniLM-L6-v2)
- SQLite - transactional event log

---

*Built by Sarah Haddon. Platform-agnostic by design.*

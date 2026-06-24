# Persistent Sales Assistant Agent

A hosted conversational API where the agent remembers context across sessions, uses real tools to answer product catalog questions, and produces a self-evaluation score on every response.

---

## Live URL

> **https://sales-agent-production-b77b.up.railway.app/docs**

---

## Architecture Diagram

```
User Request (POST /chat/{user_id})
          │
          ▼
    ┌─────────────┐
    │  API Route  │  (app/api/routes.py)
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │Chat Service │  (app/services/chat_service.py)
    └──────┬──────┘
           │
           ▼
    ┌──────────────────────────────────────────┐
    │            Sales Agent Loop              │
    │          (app/agents/sales_agent.py)     │
    │                                          │
    │  1. Load prior context from memory (DB)  │
    │  2. Call LLM with tool definitions       │
    │  3. Execute tool calls:                  │
    │     ├── search_catalog(query)            │
    │     ├── get_user_memory(user_id)         │
    │     └── flag_for_human(reason) [bonus]   │
    │  4. LLM generates final answer           │
    │  5. Eval service scores the response     │
    │  6. Save message + eval to DB            │
    └──────┬───────────────────────────────────┘
           │
           ▼
    ┌─────────────┐
    │  Eval Svc   │  (app/services/eval_service.py)
    │  LLM scores │  groundedness / relevance / confidence
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │  Memory DB  │  (SQLite via SQLAlchemy)
    │  sessions   │
    │  messages   │
    │  eval_logs  │
    └─────────────┘
           │
           ▼
    ChatResponse → { response, eval, tools_called, session_id }
```

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat/{user_id}` | Send a message, get response + eval score |
| GET | `/chat/{user_id}/history` | Full conversation history across all sessions |
| DELETE | `/chat/{user_id}/memory` | Wipe user memory (GDPR reset) |
| GET | `/chat/{user_id}/evals` | Aggregated eval scores (bonus) |
| GET | `/catalog` | Product/pricing catalog |
| GET | `/health` | Service health check |

---

## Memory Design Decision

**Current implementation:** SQLite via SQLAlchemy with an abstract `BaseMemory` interface.

Each user's messages are stored in a `messages` table keyed by `user_id`. The agent queries the last 10 messages before every response, injecting them as conversation history into the LLM context.

**Why this design:**
- The `memory/` layer is a single abstraction (`BaseMemory`). Swapping to Postgres, Redis, or Mem0 requires creating one new file implementing that interface and updating `memory_factory.py`. No agent code changes.
- SQLite is zero-config for development and Railway deploys. For production at scale, the swap would be to Postgres (persistent volume or managed DB).

**At scale (10k+ users):**
- Switch to **Postgres** for concurrent writes and proper indexing on `user_id`.
- Add **pgvector** to enable semantic/embedding-based memory retrieval instead of recency-based windowing.
- Consider **Mem0** or a dedicated memory service for automatic summarization and entity extraction.
- Add Redis caching for frequent users' recent context to reduce DB reads per request.

---

## Eval Design

Every assistant response is scored by a **prompted LLM self-evaluation** (same model, separate call with a strict system prompt).

**Scores produced:**
- `groundedness` — Is the answer factually grounded in the catalog context?
- `relevance` — Does it directly address what the user asked?
- `confidence` — Overall quality signal (combination of above + coherence)
- `flagged` — `true` if confidence < 0.6 (triggers human escalation log)
- `reasoning` — One-sentence explanation

**Limitations:**
- Self-scoring by the same model that generated the answer introduces bias — the model may over-rate its own outputs.
- Scores are not calibrated against ground truth.
- Consistent scoring depends on prompt stability.

**What to replace it with in production:**
- A dedicated eval model (e.g., GPT-4o as judge over GPT-4o-mini responses).
- [RAGAS](https://github.com/explodinggradients/ragas) for RAG-specific metrics (faithfulness, answer relevancy, context precision).
- Human-in-the-loop spot checks against flagged responses.
- A/B eval logging to track score drift over time.

---

## Cross-Session Memory Demo (curl)

These two calls use the **same `user_id`**. The second call has no mention of pricing — the agent recalls it from memory stored in the DB.

**Call 1 — Set context (ask about enterprise pricing):**
```bash
curl -X POST "https://sales-agent-production-b77b.up.railway.app/chat/demo-user-01" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your enterprise pricing and does it include SSO?"}'
```

Expected response includes Enterprise plan details ($499/mo, SSO, audit logs).

**Call 2 — Use context (ask a follow-up with no pricing re-stated):**
```bash
curl -X POST "https://sales-agent-production-b77b.up.railway.app/chat/demo-user-01" \
  -H "Content-Type: application/json" \
  -d '{"message": "Does that plan also include audit logs and what is the SLA?"}'
```

The agent knows "that plan" refers to Enterprise from the previous session — **without the pricing being re-sent in the request body**.

---

## Local Setup

```bash
# 1. Clone and install
git clone https://github.com/bhadresh14/sales-agent.git
cd sales-agent
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Run
uvicorn main:app --reload

# 4. Open API docs
# http://localhost:8000/docs
```

---

## Project Structure

```
sales-agent/
├── main.py                    # FastAPI app entry point
├── catalog.json               # Mock product catalog
├── requirements.txt
├── Procfile                   # Railway start command
├── app/
│   ├── config.py              # Settings (env vars)
│   ├── api/
│   │   └── routes.py          # Route handlers only
│   ├── agents/
│   │   └── sales_agent.py     # Agent loop + tool orchestration
│   ├── memory/
│   │   ├── base.py            # Abstract memory interface
│   │   ├── sqlite_memory.py   # SQLite implementation
│   │   └── memory_factory.py  # Single swap point for backends
│   ├── tools/
│   │   ├── search_catalog.py  # Real catalog search function
│   │   ├── get_user_memory.py # Real DB memory retrieval
│   │   └── flag_for_human.py  # Escalation tool (bonus)
│   ├── services/
│   │   ├── chat_service.py    # Orchestration between routes + agent
│   │   └── eval_service.py    # LLM self-evaluation scorer
│   ├── models/
│   │   └── schemas.py         # Pydantic request/response schemas
│   └── db/
│       ├── database.py        # SQLAlchemy engine + session
│       └── models.py          # ORM table definitions
```

---

## Deployment (Railway)

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variable: `OPENAI_API_KEY=sk-...`
4. Railway auto-detects Python and runs the `Procfile` start command
5. Copy the generated URL into the curl commands above

> **Note on SQLite on Railway:** Railway's filesystem is ephemeral. For production persistence, add a Postgres plugin in Railway and update `DATABASE_URL` — the memory layer swap requires changing only `memory_factory.py`.

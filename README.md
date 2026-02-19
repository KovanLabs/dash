# Dash — Gemini Edition

A **self-learning data agent** that answers questions in plain English by querying your database — powered by **Google Gemini** instead of OpenAI.

> **Forked from** [agno-agi/dash](https://github.com/agno-agi/dash) — replaced OpenAI GPT + embeddings with Google Gemini 2.5 Flash + Gemini Embeddings, fixed Docker entrypoint line-ending issues for Windows, and documented the full local setup process below.

---

## What it does

Ask a question in English → Dash writes SQL → runs it → returns an **insight, not just rows**.

> **"Who won the most races in 2019?"**
> → *Lewis Hamilton dominated 2019 with 11 wins out of 21 races (52%), more than double Bottas's 4 wins.*

It improves itself over time — every SQL error it makes and corrects gets stored as a **learning** so the same mistake never happens twice.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A **Google Gemini API key** — get one free at [aistudio.google.com](https://aistudio.google.com/app/apikey)
- **No Python install needed** — everything runs inside Docker

> **Windows users:** If you have PostgreSQL installed locally (port 5432 already in use), see the [Port Conflict](#port-conflict-windows) section below.

---

## Quick Start

### 1. Clone

```sh
git clone https://github.com/KovanLabs/dash.git
cd dash
```

### 2. Set your API key

```sh
cp example.env .env
```

Edit `.env` and add your Google API key:

```env
GOOGLE_API_KEY=your_key_here
```

The rest of the defaults work out of the box — no DB setup needed.

### 3. Build and start

```sh
docker compose up -d --build
```

This starts two containers:
- `dash-db` — PostgreSQL + pgvector (stores data, knowledge, learnings)
- `dash-api` — the Dash agent API

Wait ~30 seconds for the DB to initialize.

### 4. Load sample data (F1 dataset)

```sh
docker exec -it dash-api python -m dash.scripts.load_data
```

Loads 27,458 rows across 5 F1 tables (races, wins, championships, fastest laps — 1950 to 2020).

### 5. Load knowledge base

```sh
docker exec -it dash-api python -m dash.scripts.load_knowledge
```

This uses **Gemini Embeddings** to vectorize the knowledge files and stores them in pgvector. This is what lets the agent understand your schema.

### 6. Verify it's running

Open [http://localhost:8000/docs](http://localhost:8000/docs) — you should see the FastAPI Swagger UI.

### 7. Try it

```sh
# Interactive CLI
docker exec -it dash-api python -m dash
```

**Sample questions with the F1 dataset:**
- Who won the most F1 World Championships?
- How many races has Lewis Hamilton won?
- Compare Ferrari vs Mercedes points from 2015 to 2020
- Which circuit has the most race wins for Ayrton Senna?

---

## Connect to the Web UI

1. Open [os.agno.com](https://os.agno.com) and log in
2. Add OS → Local → `http://localhost:8000`
3. Click **Connect**

---

## Port Conflict (Windows)

If you have PostgreSQL installed natively on Windows, it already uses port 5432. The Docker DB will conflict with it.

The `compose.yaml` is already configured to use port **5433** for the Docker DB. Connect pgAdmin or any DB client with:

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `5433` |
| Database | `ai` |
| Username | `ai` |
| Password | `ai` |

---

## How Knowledge Works

The agent uses **7 knowledge files** to understand your schema before writing SQL:

```
dash/knowledge/
├── tables/          # Column types, gotchas, use cases per table
│   ├── race_wins.json
│   ├── race_results.json
│   ├── drivers_championship.json
│   ├── constructors_championship.json
│   └── fastest_laps.json
├── business/        # Metric definitions, business rules, known pitfalls
│   └── metrics.json
└── queries/         # Proven SQL patterns as examples
    └── common_queries.sql
```

At query time:
1. User question → **Gemini embedding** → vector similarity search against `dash_knowledge`
2. Most relevant schema docs, gotchas, and SQL examples retrieved
3. Context injected into prompt → Gemini writes grounded SQL
4. SQL executed → result interpreted → insight returned

### Self-Learning

When SQL fails, the agent:
1. Diagnoses the error
2. Fixes the SQL
3. **Saves the fix** to `dash_learnings` (with Gemini embedding)
4. Next time a similar question is asked → the fix is retrieved and the mistake is not repeated

Watch it learn:
```sql
-- Connect to DB and run:
SELECT name, content, created_at FROM dash_learnings ORDER BY created_at DESC;
```

---

## Add Your Own Data

### 1. Load your tables

```sh
docker exec -it dash-db psql -U ai -d ai
```

```sql
CREATE TABLE your_table (...);
\COPY your_table FROM '/path/to/data.csv' CSV HEADER;
```

### 2. Create a knowledge file

```json
// dash/knowledge/tables/your_table.json
{
  "table_name": "your_table",
  "table_description": "What this table contains",
  "use_cases": ["Use case 1", "Use case 2"],
  "data_quality_notes": [
    "Any gotchas about data types",
    "Any known edge cases"
  ],
  "table_columns": [
    {"name": "col_name", "type": "text", "description": "What this column means"}
  ]
}
```

### 3. Reload knowledge

```sh
docker exec -it dash-api python -m dash.scripts.load_knowledge --recreate
```

---

## Useful Commands

```sh
# Start / stop
docker compose up -d
docker compose down

# Stream logs
docker compose logs -f dash-api

# Reload knowledge after changes
docker exec dash-api python -m dash.scripts.load_knowledge --recreate

# Browse DB directly
docker exec -it dash-db psql -U ai -d ai
```

---

## What Changed from the Original

| Area | Original (agno-agi/dash) | This fork |
|------|--------------------------|-----------|
| LLM | OpenAI GPT-5.2 | Google Gemini 2.5 Flash |
| Embeddings | OpenAI text-embedding-3-small | Gemini Embedder |
| API key | `OPENAI_API_KEY` | `GOOGLE_API_KEY` |
| Docker DB port | 5432 | 5433 (avoids Windows conflict) |
| Dependencies | `openai` | `google-genai` |
| Bug fix | — | `entrypoint.sh` CRLF→LF for Windows |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | **Yes** | Google Gemini API key |
| `EXA_API_KEY` | No | Web search for external knowledge |
| `DB_USER` | No | Default: `ai` |
| `DB_PASS` | No | Default: `ai` |
| `DB_DATABASE` | No | Default: `ai` |

---

## Learn More

- [Original Dash by Agno](https://github.com/agno-agi/dash) — the upstream project
- [Agno Docs](https://docs.agno.com)
- [Google Gemini API](https://aistudio.google.com)
- [OpenAI's In-House Data Agent](https://openai.com/index/inside-our-in-house-data-agent/) — the inspiration for Dash

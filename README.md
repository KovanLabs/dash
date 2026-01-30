# Data Agent

A self-learning data agent inspired by [OpenAI's internal data agent](https://openai.com/index/inside-our-in-house-data-agent/).

## The 6 Layers of Context

| Layer | Purpose | Implementation |
|-------|---------|----------------|
| **1. Table Metadata** | Schema, columns, types | `knowledge/tables/*.json` |
| **2. Human Annotations** | Business rules, gotchas | `knowledge/business/*.json` |
| **3. Query Patterns** | Validated SQL | `knowledge/queries/*.sql` |
| **4. Institutional Knowledge** | External context | MCP (optional) |
| **5. Memory** | Discovered patterns | Agno's `LearningMachine` |
| **6. Runtime Context** | Live schema inspection | `introspect_schema` tool |

Plus **agentic memory** for user preferences.

## Quick Start

```sh
# Clone and configure
git clone https://github.com/agno-agi/data-agent.git
cd data-agent
cp example.env .env  # Add OPENAI_API_KEY

# Start
docker compose up -d --build

# Load sample F1 data
docker exec -it data-agent-api python -m da.scripts.load_data
# Load knowledge
docker exec -it data-agent-api python -m da.scripts.load_knowledge
```

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Control Plane**: [os.agno.com](https://os.agno.com) → Add OS → Local → `http://localhost:8000`

## Try It

```
Who won the most F1 World Championships?
How many races has Lewis Hamilton won?
Compare Ferrari vs Mercedes points 2015-2020
```

## Deploy to Railway

```sh
railway login
./scripts/railway_up.sh
```

## Add Your Own Knowledge

Knowledge files go in `knowledge/` with three subdirectories:

```
knowledge/
├── tables/      # Table metadata (JSON)
├── queries/     # Validated SQL patterns (SQL)
└── business/    # Business rules & metrics (JSON)
```

### 1. Table Metadata (`knowledge/tables/*.json`)

Describe each table's purpose, columns, and data quirks:

```json
{
  "table_name": "users",
  "table_description": "User accounts",
  "use_cases": ["User lookup", "Activity analysis"],
  "data_quality_notes": ["Email stored lowercase", "created_at is UTC"]
}
```

### 2. Query Patterns (`knowledge/queries/*.sql`)

Add validated queries the agent can learn from. Use XML-style tags:

```sql
-- <query name>active_users_by_month</query name>
-- <query description>
-- Count active users per month.
-- Handles: timezone conversion, activity definition
-- </query description>
-- <query>
SELECT
    DATE_TRUNC('month', last_login) AS month,
    COUNT(*) AS active_users
FROM users
WHERE last_login > NOW() - INTERVAL '30 days'
GROUP BY 1
ORDER BY 1 DESC
-- </query>
```

### 3. Business Rules (`knowledge/business/*.json`)

Define metrics and document common gotchas:

```json
{
  "metrics": [{"name": "Active User", "definition": "Login in last 30 days"}],
  "common_gotchas": [{"issue": "Timezones", "solution": "All timestamps UTC"}]
}
```

### Load Knowledge

After adding or updating files, load them into the vector database:

```sh
# Docker
docker exec -it data-agent-api python -m da.scripts.load_knowledge

# Local
python -m da.scripts.load_knowledge

# Fresh start (drop and reload all)
python -m da.scripts.load_knowledge --recreate
```

Re-running without `--recreate` will upsert (update existing documents). Use `--recreate` to drop all existing knowledge and reload from scratch.

## Local Development

```sh
./scripts/venv_setup.sh
source .venv/bin/activate
docker compose up -d data-agent-db  # PostgreSQL
python -m da.scripts.load_data
python -m da  # CLI mode
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `EXA_API_KEY` | No | Exa API for web research |
| `DB_HOST/PORT/USER/PASS/DATABASE` | No | Database config (defaults to localhost) |

## Links

- [OpenAI Data Agent Article](https://openai.com/index/how-openai-built-its-data-agent/)
- [Agno Docs](https://docs.agno.com)
- [Discord](https://agno.com/discord)

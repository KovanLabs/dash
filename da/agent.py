"""
DA - A self-learning data agent
================================

Test: python -m da.agent
"""

from os import getenv

from agno.agent import Agent
from agno.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.learn import (
    LearnedKnowledgeConfig,
    LearningMachine,
    LearningMode,
    UserMemoryConfig,
    UserProfileConfig,
)
from agno.models.openai import OpenAIResponses
from agno.tools.mcp import MCPTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.sql import SQLTools
from agno.vectordb.pgvector import PgVector, SearchType

from da.context.business_rules import BUSINESS_CONTEXT
from da.context.semantic_model import SEMANTIC_MODEL_STR
from da.tools import create_introspect_schema_tool, create_save_validated_query_tool
from db import db_url, get_postgres_db

# ============================================================================
# Database & Knowledge
# ============================================================================

agent_db = get_postgres_db()

# KNOWLEDGE: Static, curated (table schemas, validated queries, business rules)
data_agent_knowledge = Knowledge(
    name="Data Agent Knowledge",
    vector_db=PgVector(
        db_url=db_url,
        table_name="data_agent_knowledge",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
    contents_db=get_postgres_db(contents_table="data_agent_knowledge_contents"),
)

# LEARNINGS: Dynamic, discovered (error patterns, gotchas, user corrections)
data_agent_learnings = Knowledge(
    name="Data Agent Learnings",
    vector_db=PgVector(
        db_url=db_url,
        table_name="data_agent_learnings",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
    contents_db=get_postgres_db(contents_table="data_agent_learnings_contents"),
)

# ============================================================================
# Tools
# ============================================================================

save_validated_query = create_save_validated_query_tool(data_agent_knowledge)
introspect_schema = create_introspect_schema_tool(db_url)

tools: list = [
    SQLTools(db_url=db_url),
    ReasoningTools(add_instructions=True),
    save_validated_query,
    introspect_schema,
    MCPTools(url=f"https://mcp.exa.ai/mcp?exaApiKey={getenv('EXA_API_KEY', '')}&tools=web_search_exa"),
]

# ============================================================================
# Instructions
# ============================================================================

INSTRUCTIONS = f"""\
You are DA, a self-learning data agent that provides **insights**, not just query results.

## Your Purpose

You are the user's data analyst — one that never forgets, never repeats mistakes,
and gets smarter with every query.

You don't just fetch data. You interpret it, contextualize it, and explain what it means.
You remember the gotchas, the type mismatches, the date formats that tripped you up before.

Your goal: make the user look like they've been working with this data for years.

## Two Knowledge Systems

**Knowledge** (static, curated):
- Table schemas, validated queries, business rules
- Searched automatically before each response
- Add successful queries here with `save_validated_query`

**Learnings** (dynamic, discovered):
- Patterns YOU discover through errors and fixes
- Type gotchas, date formats, column quirks
- Search with `search_learnings`, save with `save_learning`

## CRITICAL: Follow this

| Situation | Action |
|-----------|--------|
| Before writing SQL | `search_knowledge`, `search_learnings` for table info, similar questions, patterns and gotchas |
| Query fails | Fix it, then `save_learning` |
| Query works and is reusable | Offer to save it with `save_validated_query` |
| Need actual column types | `introspect_schema(table_name="...")` |

## When to search_knowledge and search_learnings

BEFORE writing any SQL, search for gotchas and learnings:

```
search_knowledge("race_wins date column")
search_learnings("race_wins date parsing")
search_learnings("drivers_championship position type")
search_learnings("drivers_championship position is TEXT")
```

## When to save_learning

1. **After fixing a type error**
```
save_learning(
  title="drivers_championship position is TEXT",
  learning="Use position = '1' not position = 1",
  context="Column is TEXT despite storing numbers",
  tags=["type", "drivers_championship"]
)
```

2. **After discovering a date format**
```
save_learning(
  title="race_wins date parsing",
  learning="Use TO_DATE(date, 'DD Mon YYYY') to extract year",
  context="Date stored as text like '15 Mar 2019'",
  tags=["date", "race_wins"]
)
```

3. **After a user corrects you**
```
save_learning(
  title="Constructors Championship started 1958",
  learning="No constructors data before 1958 - query will return empty",
  context="User pointed out the championship didn't exist before then",
  tags=["business", "constructors_championship"]
)
```

## Workflow: Answering a question

1. `search_knowledge` and `search_learnings` for relevant context
2. Write SQL (LIMIT 50, no SELECT *, ORDER BY using appropriate columns)
3. If error → `introspect_schema` → fix → `save_learning`
4. Provide **insights**, not just data:
   - "Hamilton won 11 of 21 races (52%)"
   - "7 more than second place Bottas"
   - "His most dominant since 2015"
5. Offer to save if query is reusable

## SQL Rules

- LIMIT 50 by default
- Never SELECT * - specify columns
- ORDER BY for top-N queries
- No DROP, DELETE, UPDATE, INSERT

## Personality

- Insightful, not just accurate
- Learns from every mistake
- Never repeats the same error twice

---

## SEMANTIC MODEL

{SEMANTIC_MODEL_STR}

---

{BUSINESS_CONTEXT}
"""

# ============================================================================
# Create Agent
# ============================================================================

data_agent = Agent(
    id="data-agent",
    name="Data Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    db=agent_db,
    instructions=INSTRUCTIONS,
    # Knowledge (static)
    knowledge=data_agent_knowledge,
    search_knowledge=True,
    # Learning (provides search_learnings, save_learning, user profile, user memory)
    learning=LearningMachine(
        knowledge=data_agent_learnings,
        user_profile=UserProfileConfig(mode=LearningMode.AGENTIC),
        user_memory=UserMemoryConfig(mode=LearningMode.AGENTIC),
        learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
    ),
    tools=tools,
    # Context
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)

if __name__ == "__main__":
    data_agent.print_response("Who won the most races in 2019?", stream=True)

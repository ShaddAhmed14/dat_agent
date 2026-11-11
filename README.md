# DAT Agent

DAT Agent is a data assistant that routes natural-language requests to a PostgreSQL question-answering workflow or an API extraction and file transformation workflow.

Version **0.1.0** is a prototype checkpoint. It is intended for development and demonstrations with trusted data and requests.

## Features

- **Automatic routing:** Cloudflare Clef selects the SQL or ETL agent.
- **Natural-language SQL:** Inspect PostgreSQL schema and sample rows, generate a query, check it with Clef, execute on a read-only connection, and summarize the result.
- **API extraction:** Flatten a JSON response's `results` array into CSV, newline-delimited JSON, or Parquet.
- **File transformations:** Generate and execute Pandas code from a natural-language request.
- **Interactive terminal:** Submit requests through the LangGraph router until you enter `q`.
- **Sample database:** Ride-sharing CSVs and a PostgreSQL setup script covering users, vehicles, rides, payments, and ratings.
- **Evaluation starter:** A LangSmith SQL evaluation script with answer-fact and rejection checks; no measured quality score is claimed.

## Requirements and setup

Tested on Python 3.13+, uv, and a PostgreSQL database for SQL requests. Run commands from the `dat_agent` directory:

```powershell
uv sync --locked
```

Configure these environment variables in your shell or a local dotenv configuration. Keep credentials out of Git.

| Variable | Purpose |
| --- | --- |
| `provider` | Router model provider: `google`, `openai`, `anthropic`, or `ollama` |
| `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_AUTH_TOKEN` | Clef routing and SQL checks |
| `GOOGLE_API_KEY` | Google credentials when selecting `google` |
| `OPENAI_API_KEY` | OpenAI credentials when selecting `openai` |
| `ANTHROPIC_API_KEY` | Anthropic credentials when selecting `anthropic` |
| `host`, `port`, `user`, `password`, `dbname` | PostgreSQL connection; typically port `5432` |
| `schema_name` | Schema inspected by SQL; use `public` for the sample dataset |
| `sample_data_dir` | Absolute path to this project's `sample_data` directory for database setup |

Model names are configured in `src/pick_model.py`; use models available to your account. Ollama requires a running local service and the configured model downloaded. Response parsing currently assumes text content blocks.

To populate with a sample database, set the PostgreSQL variables and `sample_data_dir`, then run:

```powershell
uv run python -m src.create_db
```

This creates tables in `public` and loads the five sample CSVs. Use an empty development database: the script does not clear existing rows and reruns can fail on duplicate keys. Database setup requires table-creation and insert permissions; use a separately restricted read-only account for agent queries.

## Run the assistant

```powershell
uv run python -m src.orchestrator
```

Enter one request at the prompt; enter `q` to quit. Try:

```text
- What are the unique vehicle makes?
- How many rides have each status?
- Extract data from https://pokeapi.co/api/v2/pokemon and save it as CSV in output/extract.
- Read output/extract/data.csv, keep only rows where name is bulbasaur, and save a CSV in output/transform.
```

Run extraction before the transformation example. Extraction saves `data.csv`, `data.json`, or `data.parquet` under the requested folder; repeated extraction to the same path overwrites the file. JSON output is newline-delimited records. API extraction reads one response and does not follow pagination.

You can also run each agent directly:

```powershell
uv run python -m src.agents.sql_agent
uv run python -m src.agents.etl_agent
```

These two modules use hard-coded examples with `provider = "google"`; edit their `__main__` sections to change the request or provider.

## Evaluation

`eval/sql_agent_eval.py` invokes the SQL agent against the LangSmith dataset `dat_agent_sql_v1`. Configure LangSmith credentials and tracing in your own environment, and create that dataset before running:

```powershell
uv run python -m eval.sql_agent_eval
```

Each example needs `user_query` and `provider` inputs. Reference outputs use `expected: "rejected"` for unsafe requests, or `expected: "answered"` with a `required_facts` list for answer checks. Evaluations call external services and may incur costs. Evaluation results are not included in this checkpoint.

## Project map

| Path | Purpose |
| --- | --- |
| `src/orchestrator.py` | Interactive request router |
| `src/agents/sql_agent.py` | SQL generation, validation, execution, and answers |
| `src/agents/etl_agent.py` | API extraction and generated Pandas transformations |
| `src/database.py` | Schema inspection and read-only SQL execution |
| `src/create_db.py` | Sample database setup |
| `src/models/clef.py` | Cloudflare routing and safety calls |
| `src/pick_model.py` | Provider and model selection |
| `sample_data/` | Ride-sharing input CSVs |
| `eval/sql_agent_eval.py` | LangSmith SQL evaluation starter |

See `CHANGELOG.md` for checkpoint notes. Generated output and graph images are Git-ignored.

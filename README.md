# lakehouse-agent-kit

Model-agnostic data agent answering questions over Iceberg and Delta tables through read-only SQL tools exposed over MCP. One adapter layer swaps Claude, OpenAI and Gemini per client (`MODEL=mock|claude|openai|gemini`). Runs fully offline on a laptop: the lakehouse is emulated with Iceberg/Delta-style table metadata (format, S3 location, snapshot/version, schema) over a seeded local SQLite store, so the agent, guard and MCP plumbing are real while the warehouse is mocked.

## Design

```
                 +----------------------+
  question ----> | Agent                |
                 |  plan -> SQL -> say  |
                 +---+--------------+---+
                     |              |
              +------v-----+  +-----v------------------+
              | Model      |  | Tools (MCP surface)    |
              | adapter:   |  | list_tables            |
              | mock|claude|  | describe_table         |
              | openai|    |  | run_sql --+            |
              | gemini     |  +-----------|------------+
              +------------+              v
                               +----------------------+
                               | SQL guard (read-only)|
                               | SELECT-only, allow-  |
                               | list, LIMIT, row cap |
                               +----------+-----------+
                                          v
                               +----------------------+
                               | Catalog              |
                               | orders   [iceberg]   |
                               | products [iceberg]   |
                               | customers[delta]     |
                               | s3://lakehouse/...   |
                               +----------------------+

  MCP clients --JSON-RPC/stdio--> mcp_server --> Tools (same path)
  Every run_sql --> audit.jsonl (ts, sql, rows)
```

| Piece | File | Notes |
|---|---|---|
| Model adapter | `lakehouse_agent/models.py` | Same `plan(question, schema) -> SQL` interface for Claude/OpenAI/Gemini (stdlib HTTP, no SDK lock-in) + deterministic offline `MockModel` |
| SQL guard | `lakehouse_agent/sql_guard.py` | SELECT/WITH only, write/DDL keyword block, table allowlist, multi-statement block, forced `LIMIT 1000` |
| Tools + audit | `lakehouse_agent/tools.py` | Result row cost-cap, JSONL audit log per query |
| MCP server | `lakehouse_agent/mcp_server.py` | JSON-RPC 2.0 over stdio: `initialize`, `tools/list`, `tools/call`, `ping` |
| Catalog | `lakehouse_agent/catalog.py` | Iceberg/Delta metadata shape over seeded SQLite (1,000 orders); swap backend for DuckDB/Spark + S3 without touching tools |
| Eval | `lakehouse_agent/eval.py` | 250 held-out template/paraphrase questions; gold SQL executed directly, exact result match |
| Production gate | `CHECKLIST.md`, `Dockerfile` | Auth, cost caps, audit logs, Docker deployment checklist |

## Run

```bash
python3 -m lakehouse_agent.cli ask "revenue by region?"
python3 -m lakehouse_agent.cli ask "top 5 products?" --model mock
MODEL=claude ANTHROPIC_API_KEY=... python3 -m lakehouse_agent.cli ask "total revenue in APAC?" --model claude
python3 -m lakehouse_agent.cli tables
python3 -m lakehouse_agent.cli serve-mcp   # MCP over stdio
docker build -t lakehouse-agent-kit . && docker run -i lakehouse-agent-kit
```

## Test

```bash
python3 -m venv .venv && .venv/bin/python -m pip install pytest
.venv/bin/python -m pytest tests -q
```
Result (laptop): `6 passed`.

## Bench / Eval (laptop sanity runs, actually measured)

`python3 -m lakehouse_agent.cli eval`:
```json
{ "n": 250, "correct": 250, "accuracy": 1.0, "model": "mock", "failures": [] }
```
`python3 -m lakehouse_agent.cli bench` (40 questions, local, will vary):
```json
{ "queries": 40, "seconds": 0.005, "qps": 7707.9 }
```

**Honest reading of the eval number:** the 91% target is *not* what was measured — the measured figure is 100%, but with the deterministic rule-based `MockModel` over template-generated held-out questions, so it is a plumbing/regression ceiling, not an LLM accuracy claim. Real Claude/OpenAI/Gemini accuracy requires API keys and a human-labelled question set; that run is not done (see limitations). The suite's job today is regression: any planner change that breaks a template drops the score and fails `tests/test_agent.py` (gate: ≥90%).

## Limitations / unfinished

- **No real S3/Iceberg/Delta engine yet.** Metadata mirrors the real formats, but storage is local SQLite. Production path (DuckDB `iceberg`/`delta` extensions or Spark against a REST catalog) is described in `CHECKLIST.md`, not implemented.
- **LLM adapters are implemented but not live-tested** (no API keys in this environment); only the mock model is measured.
- Guard is regex-based defense-in-depth — the real boundary must be a SELECT-only warehouse role (see checklist).
- Eval questions are template/paraphrase generated, not human-labelled; paraphrases share planner cues, inflating the mock score.
- MCP is stdio only; no HTTP transport, auth, or rate limiting yet.

## License
MIT — see `LICENSE`.

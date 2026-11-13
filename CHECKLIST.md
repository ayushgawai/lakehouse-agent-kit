# PoC → Production Checklist
- [ ] Auth: API key/OIDC in front of MCP server; per-user table ACLs beyond the static allowlist; secrets from a vault, never env files in the image.
- [ ] Cost caps: row cap (implemented, `Tools.cost_cap_rows`), statement timeout, per-user daily token/query budget, LIMIT injection (implemented).
- [ ] Audit logs: JSONL audit of every SQL + caller identity (implemented, `AUDIT_LOG`); ship to immutable storage; alert on blocked-write attempts.
- [ ] Read-only: warehouse role with SELECT-only grants (guard is defense-in-depth, not the boundary); block egress except catalog/S3.
- [ ] Data: point Catalog at real Iceberg REST catalog / Delta log on S3 (DuckDB `iceberg`/`delta` extensions or Spark); add partition-pruning checks.
- [ ] Eval gate: `eval` in CI, fail if accuracy drops >2pts; add human-labelled questions (mock-planner score is a ceiling, not an LLM score).
- [ ] Docker: build, run as non-root, healthcheck on MCP initialize, pin base image digest.
- [ ] Observability/privacy: redact PII columns, log retention, rate limiting.

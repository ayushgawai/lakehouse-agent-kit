FROM python:3.12-slim
WORKDIR /app
COPY lakehouse_agent ./lakehouse_agent
ENV MODEL=mock AUDIT_LOG=/app/audit.jsonl
RUN useradd -m agent
USER agent
HEALTHCHECK CMD python3 -c "from lakehouse_agent.catalog import Catalog; Catalog()"
ENTRYPOINT ["python3","-m","lakehouse_agent.cli"]
CMD ["serve-mcp"]

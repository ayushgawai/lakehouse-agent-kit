import pytest, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__),".."))
from lakehouse_agent.sql_guard import guard
from lakehouse_agent.agent import Agent
from lakehouse_agent.mcp_server import handle
from lakehouse_agent.tools import Tools
from lakehouse_agent.catalog import Catalog
from lakehouse_agent.eval import questions, run
def test_guard_blocks_writes():
    for bad in ["DELETE FROM orders","DROP TABLE orders","SELECT * FROM orders; DROP TABLE orders","INSERT INTO orders VALUES (1)"]:
        with pytest.raises(ValueError): guard(bad)
def test_guard_adds_limit_and_allows_select():
    assert "LIMIT" in guard("SELECT * FROM orders")
    with pytest.raises(ValueError): guard("SELECT * FROM secrets")
def test_agent_answers():
    r=Agent().ask("total revenue in APAC?"); assert r["row_count"]==1 and r["rows"][0]["revenue"]>0
def test_mcp_tools():
    t=Tools(Catalog())
    assert handle({"id":1,"method":"tools/list"},t)["result"]["tools"]
    out=handle({"id":2,"method":"tools/call","params":{"name":"run_sql","arguments":{"sql":"SELECT COUNT(*) AS n FROM orders"}}},t)
    assert "1000" in out["result"]["content"][0]["text"]
def test_eval_set_size_and_accuracy():
    assert len(questions())==250
    r=run(); assert r["accuracy"]>=0.9, r
def test_model_swap():
    from lakehouse_agent.models import get_model
    assert [get_model(m).name for m in ["mock","claude","openai","gemini"]]==["mock","claude","openai","gemini"]

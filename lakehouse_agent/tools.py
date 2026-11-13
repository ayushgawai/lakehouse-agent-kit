import json, time, os, pathlib
from .sql_guard import guard
def audit(event):
    p=pathlib.Path(os.environ.get("AUDIT_LOG","audit.jsonl")); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a") as f: f.write(json.dumps({"ts":time.time(),**event})+"\n")
class Tools:
    def __init__(self,catalog,cost_cap_rows=1000): self.c=catalog; self.cap=cost_cap_rows
    def list_tables(self): return self.c.list_tables()
    def describe_table(self,table): return self.c.describe(table)
    def run_sql(self,sql):
        safe=guard(sql); rows=self.c.query(safe)
        if len(rows)>self.cap: raise ValueError("cost cap: result exceeds row cap")
        audit({"tool":"run_sql","sql":safe,"rows":len(rows)}); return {"sql":safe,"rows":rows,"row_count":len(rows)}
TOOLS={"list_tables":("List Iceberg/Delta tables",{}),"describe_table":("Describe a table",{"table":"string"}),"run_sql":("Run read-only SQL",{"sql":"string"})}

"""One adapter interface; swap per client via MODEL env. Real providers use stdlib urllib (no SDK lock-in); MockModel is deterministic rule-based planner for offline eval."""
import json, os, re, urllib.request
class MockModel:
    name="mock"
    def plan(self,q,schema):
        ql=q.lower()
        m=re.search(r'(?:in|for|region)\s+(apac|emea|latam|na)\b',ql)
        region=m.group(1).upper() if m else None
        m=re.search(r'category\s+(\w+)',ql); cat=m.group(1) if m else None
        where_r=f" WHERE region='{region}'" if region else ""
        if "revenue by region" in ql or "sales by region" in ql:
            return "SELECT region, ROUND(SUM(amount),2) AS revenue FROM orders WHERE status='completed' GROUP BY region ORDER BY revenue DESC"
        if "revenue by category" in ql or "sales by category" in ql:
            return "SELECT p.category, ROUND(SUM(o.amount),2) AS revenue FROM orders o JOIN products p ON p.id=o.product_id WHERE o.status='completed' GROUP BY p.category ORDER BY revenue DESC"
        if "top" in ql and "product" in ql:
            n=(re.search(r'top\s+(\d+)',ql) or [None,5])[1]
            return f"SELECT p.name, ROUND(SUM(o.amount),2) AS revenue FROM orders o JOIN products p ON p.id=o.product_id WHERE o.status='completed' GROUP BY p.name ORDER BY revenue DESC LIMIT {n}"
        if "average order" in ql or "avg order" in ql:
            return f"SELECT ROUND(AVG(amount),2) AS avg_amount FROM orders{where_r if not region else ' WHERE region=' + chr(39)+region+chr(39)}"
        if "how many orders" in ql or "count orders" in ql or "number of orders" in ql:
            w=f" WHERE region='{region}'" if region else ""
            if cat: w=(w+" AND " if w else " WHERE ")+f"product_id IN (SELECT id FROM products WHERE category='{cat}')"
            return f"SELECT COUNT(*) AS n FROM orders{w}"
        if "how many customers" in ql or "count customers" in ql:
            return f"SELECT COUNT(*) AS n FROM customers{where_r}"
        if "total revenue" in ql or "total sales" in ql:
            return f"SELECT ROUND(SUM(amount),2) AS revenue FROM orders WHERE status='completed'"+(f" AND region='{region}'" if region else "")
        if "refunded" in ql:
            return "SELECT COUNT(*) AS n FROM orders WHERE status='refunded'"
        return "SELECT COUNT(*) AS n FROM orders"
class _HTTPModel:
    name="http"; url=""; key_env=""; model_env=""
    def plan(self,q,schema):
        key=os.environ.get(self.key_env)
        if not key: raise RuntimeError(f"{self.key_env} not set; use MODEL=mock offline")
        prompt=f"Schema:\n{schema}\nWrite ONE read-only SQLite SELECT for: {q}\nSQL only."
        body=self._body(prompt)
        req=urllib.request.Request(self.url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json",**self._headers(key)})
        with urllib.request.urlopen(req,timeout=30) as r: data=json.load(r)
        return self._extract(data).strip().strip('`').removeprefix("sql").strip()
class ClaudeModel(_HTTPModel):
    name="claude"; url="https://api.anthropic.com/v1/messages"; key_env="ANTHROPIC_API_KEY"
    def _headers(self,k): return {"x-api-key":k,"anthropic-version":"2023-06-01"}
    def _body(self,p): return {"model":os.environ.get("CLAUDE_MODEL","claude-sonnet-5-5"),"max_tokens":512,"messages":[{"role":"user","content":p}]}
    def _extract(self,d): return d["content"][0]["text"]
class OpenAIModel(_HTTPModel):
    name="openai"; url="https://api.openai.com/v1/chat/completions"; key_env="OPENAI_API_KEY"
    def _headers(self,k): return {"Authorization":f"Bearer {k}"}
    def _body(self,p): return {"model":os.environ.get("OPENAI_MODEL","gpt-4o-mini"),"messages":[{"role":"user","content":p}]}
    def _extract(self,d): return d["choices"][0]["message"]["content"]
class GeminiModel(_HTTPModel):
    name="gemini"; key_env="GEMINI_API_KEY"
    def _headers(self,k): return {}
    def _body(self,p): return {"contents":[{"parts":[{"text":p}]}]}
    def _extract(self,d): return d["candidates"][0]["content"]["parts"][0]["text"]
    def plan(self,q,schema):
        self.url=f"https://generativelanguage.googleapis.com/v1beta/models/{os.environ.get('GEMINI_MODEL','gemini-2.0-flash')}:generateContent?key={os.environ.get(self.key_env,'')}"
        return super().plan(q,schema)
MODELS={"mock":MockModel,"claude":ClaudeModel,"openai":OpenAIModel,"gemini":GeminiModel}
def get_model(name=None):
    n=(name or os.environ.get("MODEL","mock")).lower()
    if n not in MODELS: raise ValueError(f"unknown model {n}, choose {list(MODELS)}")
    return MODELS[n]()

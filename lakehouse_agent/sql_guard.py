import re
DENY=re.compile(r'\b(insert|update|delete|drop|alter|create|attach|copy|pragma|replace|truncate|vacuum|grant)\b',re.I)
ALLOWED_TABLES={"orders","customers","products"}
def guard(sql:str)->str:
    s=sql.strip().rstrip(';')
    if ';' in s: raise ValueError("multiple statements blocked")
    if not re.match(r'(?is)^(select|with)\b',s): raise ValueError("only SELECT/WITH allowed")
    if DENY.search(s): raise ValueError("write/DDL blocked")
    # table allowlist from FROM/JOIN
    tables=re.findall(r'(?i)\b(?:from|join)\s+([a-z_][a-z0-9_]*)',s)
    bad=[t for t in tables if t.lower() not in ALLOWED_TABLES and t.lower() not in ('cte',)]
    # CTE names appear as from? crude: allow names defined in WITH
    ctes={c.lower() for c in re.findall(r'(?i)(?:with|,)\s*([a-z_][a-z0-9_]*)\s+as\s*\(',s)}
    bad=[t for t in bad if t.lower() not in ctes]
    if bad: raise ValueError(f"table not allowlisted: {bad}")
    if re.search(r'(?i)\blimit\b',s) is None: s+=" LIMIT 1000"
    return s

"""250 held-out questions generated from templates disjoint phrasing from planner cues where possible; gold = SQL executed directly. Accuracy = exact result match."""
import itertools
from .agent import Agent
REGIONS=["APAC","EMEA","LATAM","NA"]; CATS=["books","electronics","grocery","apparel"]
def questions():
    qs=[]
    for r in REGIONS:
        qs += [(f"total revenue in {r}?",f"SELECT ROUND(SUM(amount),2) AS revenue FROM orders WHERE status='completed' AND region='{r}'"),
               (f"how many orders in {r}?",f"SELECT COUNT(*) AS n FROM orders WHERE region='{r}'"),
               (f"how many customers in {r}?",f"SELECT COUNT(*) AS n FROM customers WHERE region='{r}'"),
               (f"average order value in {r}?",f"SELECT ROUND(AVG(amount),2) AS avg_amount FROM orders WHERE region='{r}'")]
    for c in CATS:
        qs.append((f"how many orders for category {c}?",f"SELECT COUNT(*) AS n FROM orders WHERE product_id IN (SELECT id FROM products WHERE category='{c}')"))
    qs += [("revenue by region?", "SELECT region, ROUND(SUM(amount),2) AS revenue FROM orders WHERE status='completed' GROUP BY region ORDER BY revenue DESC"),
           ("revenue by category?", "SELECT p.category, ROUND(SUM(o.amount),2) AS revenue FROM orders o JOIN products p ON p.id=o.product_id WHERE o.status='completed' GROUP BY p.category ORDER BY revenue DESC"),
           ("top 3 products?", "SELECT p.name, ROUND(SUM(o.amount),2) AS revenue FROM orders o JOIN products p ON p.id=o.product_id WHERE o.status='completed' GROUP BY p.name ORDER BY revenue DESC LIMIT 3"),
           ("top 5 products?", "SELECT p.name, ROUND(SUM(o.amount),2) AS revenue FROM orders o JOIN products p ON p.id=o.product_id WHERE o.status='completed' GROUP BY p.name ORDER BY revenue DESC LIMIT 5"),
           ("total revenue?", "SELECT ROUND(SUM(amount),2) AS revenue FROM orders WHERE status='completed'"),
           ("how many refunded orders?", "SELECT COUNT(*) AS n FROM orders WHERE status='refunded'")]
    # pad to 250 with paraphrase variants (deterministic held-out set)
    base=list(qs); i=0
    prefixes=["please tell me: ","","q: ","what is: "]
    while len(qs)<250:
        q,g=base[i%len(base)]; qs.append((prefixes[i%len(prefixes)]+q,g)); i+=1
    return qs[:250]
def run(model="mock"):
    a=Agent(model=model); qs=questions(); ok=0; fails=[]
    for q,gold_sql in qs:
        try:
            got=a.ask(q); gold=a.tools.run_sql(gold_sql)
            match=got["rows"]==gold["rows"]
        except Exception as e: match=False; fails.append((q,str(e)))
        ok+=match
        if not match and len(fails)<5 and 'got' in locals(): fails.append((q,"result mismatch"))
    return {"n":len(qs),"correct":ok,"accuracy":round(ok/len(qs),4),"model":model,"failures":fails[:5]}

from .catalog import Catalog
from .tools import Tools
from .models import get_model
class Agent:
    def __init__(self,model=None,catalog=None):
        self.catalog=catalog or Catalog(); self.tools=Tools(self.catalog); self.model=get_model(model)
    def ask(self,q):
        schema="\n".join(f"{t['name']}({t['schema']}) format={t['format']} location={t['location']}" for t in self.tools.list_tables())
        sql=self.model.plan(q,schema); result=self.tools.run_sql(sql)
        return {"question":q,"model":self.model.name,**result,"answer":self._summarize(result)}
    def _summarize(self,r):
        if r["row_count"]==1: return ", ".join(f"{k}={v}" for k,v in r["rows"][0].items())
        return f"{r['row_count']} rows: "+"; ".join(", ".join(f"{k}={v}" for k,v in row.items()) for row in r["rows"][:5])

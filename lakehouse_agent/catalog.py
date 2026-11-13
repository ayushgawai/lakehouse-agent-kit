"""Local lakehouse emulation: Iceberg/Delta metadata over SQLite storage.
Real deployment swaps Catalog.backend to DuckDB/Spark + S3; metadata shape mirrors
Iceberg (format, location, snapshot) / Delta (_delta_log) so tools don't change."""
import json, random, sqlite3, pathlib
REGIONS=["APAC","EMEA","LATAM","NA"]; CATS=["books","electronics","grocery","apparel"]
PRODUCTS=[(i,f"product_{i}",CATS[i%4],round(10+(i*37)%190,2)) for i in range(1,21)]
class Catalog:
    def __init__(self,path=":memory:",seed=7):
        self.db=sqlite3.connect(path); self.db.row_factory=sqlite3.Row; self.meta={}
        self._build(seed)
    def _build(self,seed):
        c=self.db
        c.executescript("""CREATE TABLE orders(id INTEGER, customer_id INT, region TEXT, product_id INT, qty INT, amount REAL, order_date TEXT, status TEXT);
        CREATE TABLE customers(id INTEGER, name TEXT, region TEXT, segment TEXT);
        CREATE TABLE products(id INTEGER, name TEXT, category TEXT, price REAL);""")
        c.executemany("INSERT INTO products VALUES (?,?,?,?)",PRODUCTS)
        c.executemany("INSERT INTO customers VALUES (?,?,?,?)",[(i,f"customer_{i}",REGIONS[i%4],["retail","enterprise"][i%2]) for i in range(1,51)])
        r=random.Random(seed); rows=[]
        for i in range(1,1001):
            p=r.choice(PRODUCTS); q=r.randint(1,5)
            rows.append((i,r.randint(1,50),r.choice(REGIONS),p[0],q,round(p[3]*q,2),f"2024-{r.randint(1,12):02d}-{r.randint(1,28):02d}",r.choice(["completed","completed","completed","refunded"])))
        c.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)",rows); c.commit()
        self.meta={
         "orders":{"format":"iceberg","location":"s3://lakehouse/iceberg/orders","snapshot_id":1042,"schema":"id,customer_id,region,product_id,qty,amount,order_date,status"},
         "customers":{"format":"delta","location":"s3://lakehouse/delta/customers","version":18,"schema":"id,name,region,segment"},
         "products":{"format":"iceberg","location":"s3://lakehouse/iceberg/products","snapshot_id":77,"schema":"id,name,category,price"}}
    def list_tables(self): return [{"name":k,**v} for k,v in self.meta.items()]
    def describe(self,t):
        if t not in self.meta: raise ValueError(f"unknown table {t}")
        return self.meta[t]
    def query(self,sql): return [dict(r) for r in self.db.execute(sql)]

import argparse, json, time
from .agent import Agent
from .eval import run as eval_run
from .mcp_server import serve
def main():
    p=argparse.ArgumentParser(prog="lakehouse-agent"); sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("ask"); a.add_argument("question"); a.add_argument("--model",default="mock")
    e=sub.add_parser("eval"); e.add_argument("--model",default="mock")
    sub.add_parser("bench"); sub.add_parser("serve-mcp"); sub.add_parser("tables")
    args=p.parse_args()
    if args.cmd=="ask": print(json.dumps(Agent(model=args.model).ask(args.question),indent=2))
    elif args.cmd=="eval": print(json.dumps(eval_run(args.model),indent=2))
    elif args.cmd=="serve-mcp": serve()
    elif args.cmd=="tables": print(json.dumps(Agent().tools.list_tables(),indent=2))
    elif args.cmd=="bench":
        ag=Agent(); qs=["total revenue?","revenue by region?","top 5 products?","how many orders in APAC?"]*10
        t=time.perf_counter(); [ag.ask(q) for q in qs]; dt=time.perf_counter()-t
        print(json.dumps({"queries":len(qs),"seconds":round(dt,3),"qps":round(len(qs)/dt,1)},indent=2))
if __name__=="__main__": main()

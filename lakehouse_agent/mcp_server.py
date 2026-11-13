"""MCP server over stdio: JSON-RPC 2.0, initialize/tools/list/tools/call. No SDK needed."""
import sys, json
from .catalog import Catalog
from .tools import Tools, TOOLS
def handle(req,tools):
    m=req.get("method"); rid=req.get("id")
    try:
        if m=="initialize": result={"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"lakehouse-agent-kit","version":"0.1.0"}}
        elif m=="tools/list": result={"tools":[{"name":k,"description":d,"inputSchema":{"type":"object","properties":{p:{"type":t} for p,t in s.items()}}} for k,(d,s) in TOOLS.items()]}
        elif m=="tools/call":
            name=req["params"]["name"]; args=req["params"].get("arguments",{}); fn=getattr(tools,name); out=fn(**args)
            result={"content":[{"type":"text","text":json.dumps(out)}]}
        elif m=="ping": result={}
        else: return {"jsonrpc":"2.0","id":rid,"error":{"code":-32601,"message":f"unknown {m}"}}
        return {"jsonrpc":"2.0","id":rid,"result":result}
    except Exception as e: return {"jsonrpc":"2.0","id":rid,"error":{"code":-32000,"message":str(e)}}
def serve():
    tools=Tools(Catalog())
    for line in sys.stdin:
        if line.strip(): print(json.dumps(handle(json.loads(line),tools)),flush=True)
if __name__=="__main__": serve()

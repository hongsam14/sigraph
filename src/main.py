import os
from fastapi import FastAPI
from dotenv import load_dotenv
from model import SyscallNode, SysLogObject
from graph_client import GraphClient
from db_client import DBClient

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI application
app = FastAPI()
# Initialize the GraphClient with Neo4j connection details
graph_client = GraphClient(
    uri=os.getenv("NEO4J_URI", "localhost"),
    user=os.getenv("NEO4J_USER", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "")
)

db_client = DBClient(
    uri=os.getenv("OPENSEARCH_URI", "localhost"),
    index_name=os.getenv("OPENSEARCH_INDEX", "syslog_index")
)

@app.post("/syscall")
async def post_syscall(event: SyscallNode):
    try:
        graph_client.upsert_syscall_object(event)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.post("/syslog")
async def post_syslog(syslog_object: SysLogObject):
    try:
        db_client.save_syslog_object(syslog_object)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
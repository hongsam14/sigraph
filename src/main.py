from fastapi import FastAPI
from dotenv import load_dotenv
import os
from model import SyscallNode
from graph_client import GraphClient

app = FastAPI()
# Initialize the GraphClient with Neo4j connection details
graph_client = GraphClient(
    uri=os.getenv("NEO4J_URI", "localhost"),
    user=os.getenv("NEO4J_USER", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "")
)

@app.post("/syscall")
async def post_syscall(event: SyscallNode):
    try:
        graph_client.upsert_syscall_object(event)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
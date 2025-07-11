from fastapi import FastAPI
from model import SyscallNode
from graph_client import GraphClient

app = FastAPI()
# Initialize the GraphClient with Neo4j connection details
graph_client = GraphClient(
    uri="localhost",
    user="neo4j",
    password=""
)

@app.post("/syscall")
async def post_syscall(event: SyscallNode):
    graph_client.upsert_syscall_object(event)
    return {"status": "ok"}
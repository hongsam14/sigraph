import os
from fastapi import FastAPI
from dotenv import load_dotenv
from loguru import logger
from graph.graph_model import GraphNode
from graph.graph_session import GraphSession
from db.db_session import DBSession
from db.db_model import SyslogModel

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI application
app = FastAPI()

logger.add("logs/app.log",
           rotation="10 MB",
           retention="7 days",
           compression="zip",
           level="INFO")

# Initialize the GraphSession with Neo4j connection details
graph_session = GraphSession(
    logger,
    uri=os.getenv("NEO4J_URI", "localhost"),
    user=os.getenv("NEO4J_USER", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "")
)

db_session = DBSession(
    logger,
    uri=os.getenv("OPENSEARCH_URI", "localhost"),
    index_name=os.getenv("OPENSEARCH_INDEX", "syslog_index")
)

@app.post("/syscall")
async def post_syscall(event: GraphNode):
    try:
        graph_session.upsert_system_provenance(event)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.post("/syslog")
async def post_syslog(syslog_object: SyslogModel):
    try:
        db_session.store_syslog_object(syslog_object)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
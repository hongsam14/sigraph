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
from fastapi import APIRouter

app = FastAPI()

# Create an API router with the /api prefix
api_router = APIRouter(prefix="/api")

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

@api_router.post("/v1/syscall")
async def post_syscall(event: GraphNode):
    try:
        graph_session.upsert_system_provenance(event)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@api_router.post("/v1/syslog")
async def post_syslog(syslog_object: SyslogModel):
    try:
        db_session.store_syslog_object(syslog_object)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Include the router in the FastAPI app
app.include_router(api_router)
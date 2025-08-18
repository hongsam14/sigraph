from typing import Any
from fastapi import APIRouter
from app.config import AppConfig
from db.db_session import DBSession
from db.db_model import SyslogModel
from graph.graph_model import GraphNode
from graph.graph_session import GraphSession

# Initialize FastAPI application
from fastapi import APIRouter


class DBAPI:
    graph_session: GraphSession
    db_session: DBSession
    api_router: APIRouter = APIRouter(prefix="/v1")

    def __init__(self, logger: Any, config: AppConfig):
        # Initialize the GraphSession with Neo4j connection details
        self.graph_session = GraphSession(
            logger,
            uri=config.neo4j_uri,
            user=config.neo4j_user,
            password=config.neo4j_password
        )
        self.db_session = DBSession(
            logger,
            uri=config.opensearch_uri,
            index_name=config.opensearch_index
        )

    @api_router.post("/syscall")
    async def post_syscall(self, event: GraphNode):
        try:
            await self.graph_session.upsert_system_provenance(event)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @api_router.post("/syslog")
    async def post_syslog(self, syslog_object: SyslogModel):
        try:
            await self.db_session.store_syslog_object(syslog_object)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

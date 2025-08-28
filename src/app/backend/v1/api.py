"""_summary_
This module defines the API endpoints for interacting with the AI agent and the knowledge graph.
Also includes API endpoints for System Provenance Graph and Syslog database interactions.
It includes endpoints for posting reports and queries to the AI agent.
"""
from typing import Any
from pydantic import BaseModel
from fastapi import APIRouter, Body
from fastapi.responses import PlainTextResponse
from app.config import AppConfig
from db.db_session import DBSession
from db.db_model import SyslogModel
from graph.graph_model import GraphNode
from graph.graph_session import GraphSession
from ai.ai_agent import GraphAIAgent

class DBAPI:
    """Database API for interacting with the System Provenance database."""
    graph_session: GraphSession
    db_session: DBSession
    api_router: APIRouter = APIRouter(prefix="/v1/db")

    def __init__(self, logger: Any, config: AppConfig):
        # Initialize the GraphSession with Neo4j connection details
        self.graph_session = GraphSession(
            logger,
            uri=config.neo4j_uri,
            user=config.neo4j_user,
            password=config.neo4j_password.get_secret_value()
        )
        self.db_session = DBSession(
            logger,
            uri=config.opensearch_uri,
            index_name=config.opensearch_index
        )

        self.api_router.add_api_route(
            "/syscall",
            self.post_syscall,
            methods=["POST"],
            summary="Post syscall event",
            description="Store a system call event in the graph database."
        )

        self.api_router.add_api_route(
            "/syslog",
            self.post_syslog,
            methods=["POST"],
            summary="Post syslog object",
            description="Store a syslog object in the database."
        )

    async def post_syscall(self, event: GraphNode):
        """Post a system call event to the graph database."""
        try:
            await self.graph_session.upsert_system_provenance(event)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def post_syslog(self, syslog_object: SyslogModel):
        """Post a syslog object to the database."""
        try:
            await self.db_session.store_syslog_object(syslog_object)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class ReportRequest(BaseModel):
    """
    Request schema for posting a system provenance
    to the system provenance graph.
    """
    report: str


class QueryRequest(BaseModel):
    """Request schema for querying the AI agent."""
    question: str

class AIAPI:
    """AI API for interacting with the AI agent."""
    ai_agent: GraphAIAgent
    api_router: APIRouter = APIRouter(prefix="/v1/ai")
    __logger: Any

    def __init__(self, logger: Any, config: AppConfig):
        """Initialize the AI API with the provided logger and configuration."""
        self.__logger = logger

        self.ai_agent = GraphAIAgent(
            logger=logger,
            app_config=config
        )

        self.api_router.add_api_route(
            "/report",
            self.post_report_to_ai,
            methods=["POST"],
            response_class=PlainTextResponse,
            summary="Post report to AI",
            description="Send a report to the AI agent for processing."
        )

        self.api_router.add_api_route(
            "/analyze",
            self.post_behavior_to_analyze_with_ai,
            methods=["POST"],
            summary="Post behavior to AI",
            description="Send a behavior query to the AI agent for analysis."
        )
        
        self.api_router.add_api_route(
            "/chat",
            self.post_chat_with_ai,
            methods=["POST"],
            summary="Chat with AI",
            description="Chat with the AI model using the provided question."
        )
        
    async def post_report_to_ai(self, report: str = Body(..., media_type="text/plain")):
        """Post a report to the knowledge graph."""
        try:
            val = await self.ai_agent.post_report_to_graph(report)
            return val
        except ValueError as ve:
            return str(ve)
        except Exception as e:
            # Log the error because except value error, sould be logged.
            self.__logger.warning(f"Error processing report: {str(e)}")
            return str(e)

    async def post_behavior_to_analyze_with_ai(self, query: QueryRequest = Body(...)):
        """Post a query to the Knowledge Graph."""
        try:
            response = await self.ai_agent.analyze_behavior_with_ai(query.question)
            return {"status": "ok", "response": response}
        except ValueError as ve:
            return {"status": "error", "message": str(ve)}
        except Exception as e:
            self.__logger.warning(f"Error processing query: {str(e)}")
            return {"status": "error", "message": str(e)}
        
    async def post_chat_with_ai(self, question: QueryRequest = Body(...)):
        """Chat with the AI model using the provided question."""
        try:
            response = await self.ai_agent.chat_with_ai(question.question)
            return {"status": "ok", "response": response}
        except ValueError as ve:
            return {"status": "error", "message": str(ve)}
        except Exception as e:
            self.__logger.warning(f"Error processing chat: {str(e)}")
            return {"status": "error", "message": str(e)}
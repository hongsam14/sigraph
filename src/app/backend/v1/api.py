"""_summary_
This module defines the API endpoints for interacting with the AI agent and the knowledge graph.
Also includes API endpoints for System Provenance Graph and Syslog database interactions.
It includes endpoints for posting reports and queries to the AI agent.
"""
from typing import Any
from uuid import UUID
from pydantic import BaseModel
from fastapi import APIRouter, Body
from fastapi.responses import PlainTextResponse
from app.config import AppConfig
from db.db_session import DBSession
from db.db_model import SyslogModel
from graph.graph_model import GraphNode
from graph.graph_session import GraphSession
from ai.ai_agent import GraphAIAgent

import traceback



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

        self.api_router.add_api_route(
            "/syslog/sequence/{unit_id}/{trace_id}",
            self.get_syslog_sequence,
            methods=["GET"],
            summary="Get syslog sequence",
            description="Retrieve a sequence of syslog objects associated with a specific trace ID and unit ID."
        )

        self.api_router.add_api_route(
            "/syslog/sequences/{unit_id}",
            self.get_syslog_sequences,
            methods=["POST"],
            summary="Get syslog sequences",
            description="Retrieve sequences of syslog objects based on a Lucene query."
        )

    async def post_syscall(self, event: GraphNode):
        """Post a system call event to the graph database."""
        try:
            await self.graph_session.upsert_system_provenance(event)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def post_syslog(self, syslog_object: list[SyslogModel]):
        """Post a syslog object to the database."""
        try:
            for obj in syslog_object:
                await self.db_session.store_syslog_object(obj)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
    async def get_syslog_sequence(self, unit_id: str, trace_id: str):
        """Get a sequence of syslog objects from the database."""
        try:
            uuid_obj = UUID(unit_id)
            syslog_sequence = await self.db_session.get_syslog_sequence_with_trace(
                unit_id=uuid_obj,
                trace_id=trace_id,
            )
            return {"status": "ok", "data": syslog_sequence}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_syslog_sequences(self, unit_id: str, lucene_query: dict):
        """Get sequences of syslog objects from the database based on a Lucene query."""
        try:
            uuid_obj = UUID(unit_id)
            syslog_sequences = await self.db_session.get_syslog_sequences_with_lucene_query(
                unit_id=uuid_obj,
                lucene_query=lucene_query
            )
            return {"status": "ok", "data": syslog_sequences}
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
            self.__logger.warning(f"Error processing report: {traceback.format_exc()}")
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
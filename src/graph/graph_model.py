"""_summary_
This module contains the GraphNode class, which represents a node in the graph.
It includes methods for converting from py2neo nodes and retrieving SigraphNode instances.
"""

from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from graph.provenance.type import SystemProvenance
import pydantic
from datetime import datetime

if pydantic.VERSION.startswith("2."):
    class GraphNode(BaseModel):
        """_summary_
        GraphNode is a Pydantic model that represents a node in the graph.
        It includes methods for converting from py2neo nodes and retrieving SigraphNode instances.

        Args:
            BaseModel (_type_): BaseModel is a Pydantic model that provides data validation
            and serialization.

        Attributes:
            span_id (str): Unique identifier for the span.
            system_provenance (SystemProvenance): System provenance information associated with the node.
            parent_span_id (Optional[str]): Unique identifier for the parent span, if any.
        """

        trace_id: str
        span_id: str
        unit_id: UUID
        system_provenance: str
        ## relationship attributes
        timestamp: datetime
        weight: int
        ## node attributes
        process_name: Optional[str] = None
        related_rule_ids: Optional[list[str]] = []
        ## parent attributes
        parent_span_id: Optional[str] = None
        parent_system_provenance: Optional[str] = None

        model_config = {
            "title": "GraphNode",
            "arbitrary_types_allowed": True,
        }

    class GraphTraceNode(BaseModel):
        """_summary_
        GraphTraceNode is a Pydantic model that represents a trace node in the graph.
        It includes methods for converting from py2neo nodes and retrieving SigraphTraceNode instances.

        Args:
            BaseModel (_type_): BaseModel is a Pydantic model that provides data validation and serialization.
        """
        
        trace_id: str
        timestamp: datetime
        image_name: Optional[str] = None
        span_count: Optional[int] = 0

        model_config = {
            "title": "GraphTraceNode",
            "arbitrary_types_allowed": True,
        }

else:
    class GraphNode(BaseModel):
        """_summary_
        GraphNode is a Pydantic model that represents a node in the graph.
        It includes methods for converting from py2neo nodes and retrieving SigraphNode instances.

        Args:
            BaseModel (_type_): BaseModel is a Pydantic model that provides data validation
            and serialization.

        Attributes:
            span_id (str): Unique identifier for the span.
            system_provenance (SystemProvenance): System provenance information associated with the node.
            parent_span_id (Optional[str]): Unique identifier for the parent span, if any.
        """

        trace_id: str
        span_id: str
        unit_id: UUID
        system_provenance: SystemProvenance
        ## relationship attributes
        timestamp: datetime
        weight: int
        ## node attributes
        process_name: Optional[str] = None
        related_rule_ids: Optional[list[str]] = []
        ## parent attributes
        parent_span_id: Optional[str] = None
        parent_system_provenance: Optional[SystemProvenance] = None

        class Config:
            """_summary_
            Configuration for the GraphNode model.
            """
            title = "GraphNode"
            arbitrary_types_allowed = True

    class GraphTraceNode(BaseModel):
        """_summary_
        GraphTraceNode is a Pydantic model that represents a trace node in the graph.
        It includes methods for converting from py2neo nodes and retrieving SigraphTraceNode instances.

        Args:
            BaseModel (_type_): BaseModel is a Pydantic model that provides data validation and serialization.
        """
        
        trace_id: str
        timestamp: datetime
        image_name: Optional[str] = None
        span_count: Optional[int] = 0

        class Config:
            """_summary_
            Configuration for the GraphTraceNode model.
            """
            title = "GraphTraceNode"
            arbitrary_types_allowed = True
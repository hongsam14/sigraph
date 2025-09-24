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
        timestamp: datetime
        weight: int
        system_provenance: str
        process_name: Optional[str] = None
        parent_span_id: Optional[str] = None
        parent_system_provenance: Optional[str] = None

        model_config = {
            "title": "GraphNode",
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
        timestamp: datetime
        weight: int
        system_provenance: SystemProvenance
        process_name: Optional[str] = None
        parent_span_id: Optional[str] = None
        parent_system_provenance: Optional[SystemProvenance] = None

        class Config:
            """_summary_
            Configuration for the GraphNode model.
            """
            title = "GraphNode"
            arbitrary_types_allowed = True

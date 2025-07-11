from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class SyscallObject(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_):
        BaseModel is a Pydantic model that provides data validation and serialization.

    Attributes:
        syscall (str): Primary key for the graph object.
        analysis_id (UUID): Unique identifier for the analysis.
        parent (Optional[List[str]]): List of parent syscalls.
        tactics (Optional[List[str]]): List of tactics associated with the syscall.
        matched_ids (Optional[List[str]]): List of matched sigma rule IDs.
        start_at (datetime): Timestamp when the object was created.
        end_at (datetime): Timestamp when the object was last updated.
    """

    syscall: str
    analysis_id: UUID
    parent: Optional[List[str]] = None
    tactics: Optional[List[str]] = None
    matched_ids: Optional[List[str]] = None
    start_at: datetime
    end_at: datetime


class SysLogObject(BaseModel):
    """_summary_
    Args:
        BaseModel (_type_):
        BaseModel is a Pydantic model that provides data validation and serialization.
    Attributes:
        analysis_id (UUID): Unique identifier for the analysis.
        span_id (str): Unique identifier for the span.
        trace_id (str): Unique identifier for the trace.
        raw_data (str): Raw log data.
    """

    analysis_id: UUID
    span_id: str
    trace_id: str
    raw_data: str

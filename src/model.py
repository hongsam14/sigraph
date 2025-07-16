"""_summary_
This module defines Pydantic models for Sigraph.
These models are used to represent the content data of syscalls
in a structured way.
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel


class SyscallOP(str, Enum):
    """_summary_
    Args:
        Enum (_type_):
    Attributes:
        EXECVE (str): Represents the execve syscall operation.
        FILE (str): Represents file-related operations.
        NETWORK (str): Represents network-related operations.
    """

    EXECVE = "execve"
    FILE = "file"
    NETWORK = "network"


class Syscall(BaseModel):
    """_summary_
    Args:
        BaseModel (_type_):
        BaseModel is a Pydantic model that provides data validation and serialization.
    Attributes:
        id (str): Unique identifier for the syscall.
        type (SyscallOP): Type of the syscall operation.
    """

    id: str
    type: SyscallOP
    def __str__(self) -> str:
        """Return a string representation of the syscall."""
        return f"{self.id}@{self.type.value}"

    def __ref__(self) -> str:
        return str(self)


class SyscallNode(BaseModel):
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

    syscall: Syscall
    analysis_id: UUID
    parent: Optional[List[Syscall]] = None
    tactics: Optional[List[str]] = None
    matched_ids: Optional[List[UUID]] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class SysLogObject(BaseModel):
    """_summary_
    Args:
        BaseModel (_type_):
        BaseModel is a Pydantic model that provides data validation and serialization.
    Attributes:
        analysis_id (UUID): Unique identifier for the analysis.
        span_id (str): Unique identifier for the span.
        trace_id (str): Unique identifier for the trace.
        timestamp (datetime): Timestamp of the log entry.
        raw_data (str): Raw log data.
    """

    analysis_id: UUID
    span_id: str
    trace_id: str
    timestamp: datetime
    raw_data: str


class SigraphObject(BaseModel):
    """_summary_
    Args:
        BaseModel (_type_):
        BaseModel is a Pydantic model that provides data validation and serialization.
    Attributes:
        syscall_object (SyscallObject): The syscall object associated with the span contect data.
        syslog_list (Optional[List[SysLogObject]]): List of syslog objects associated with the span.
    """

    syscall_object: SyscallNode
    syslog_list: Optional[List[SysLogObject]]

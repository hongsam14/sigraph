"""_summary_
This module defines various actions involved in system calls and operations.
Each action represents a specific role or action in the context of system calls,
"""

from enum import Enum
from typing import Literal, Optional, List

class ActionType(str, Enum):
    """_summary_
    Args:
        Enum (_type_):
    Attributes:
        LAUNCH (str): Represents the launch action.
        REMOTE_THREAD (str): Represents the remote thread action.
        ACCESS (str): Represents the access action.
        TAMPERING (str): Represents the tampering action.
        CONNECT (str): Represents the connect action in network operations.
        ACCEPT (str): Represents the accept action in network operations.
        CREATE (str): Represents the create action in file operations.
        RENAME (str): Represents the rename action in file operations.
        DELETE (str): Represents the delete action in file operations.
        MODIFY (str): Represents the modify action in file operations.
        RAW_ACCESS_READ (str): Represents raw access read in file operations.
        CREATE_STREAM_HASH (str): Represents creating a stream hash in file operations.
        REG_ADD (str): Represents adding a registry entry.
        REG_DELETE (str): Represents deleting a registry entry.
        REG_SET (str): Represents setting a registry entry value.
        REG_RENAME (str): Represents renaming a registry entry.
        REG_QUERY (str): Represents querying a registry entry.
    This enum defines various actions involved in system calls and operations.
    Each action represents a specific role or action in the context of system calls,
    """

    # process actions
    LAUNCH = "LAUNCH"
    REMOTE_THREAD = "REMOTE_THREAD"
    ACCESS = "ACCESS"
    TAMPERING = "TAMPERING"
    # network actions
    CONNECT = "CONNECT"
    ACCEPT = "ACCEPT"
    # file actions
    CREATE = "CREATE"
    RENAME = "RENAME"
    DELETE = "DELETE"
    MODIFY = "MODIFY"
    RAW_ACCESS_READ = "RAW_ACCESS_READ"
    CREATE_STREAM_HASH = "CREATE_STREAM_HASH"
    # registry actions
    REG_ADD = "REG_ADD"
    REG_DELETE = "REG_DELETE"
    REG_SET = "REG_SET"
    REG_RENAME = "REG_RENAME"
    REG_QUERY = "REG_QUERY"


class ActorType(str, Enum):
    """_summary_
    Args:
        Enum (_type_):
    Attributes:
        READ_RECV (str): Represents the read/receive action.
        WRITE_SEND (str): Represents the write/send action.
        LAUNCH (str): Represents the launch action.
    This enum defines various types of actors involved in system calls and operations.
    Each actor represents a specific entity or component in the context of system calls.
    """

    READ_RECV = "READ_RECV"
    WRITE_SEND = "WRITE_SEND"
    LAUNCH = "LAUNCH"


class ArtifactType(str, Enum):
    """_summary_
    Args:
        Enum (_type_):
    Attributes:
        FILE (str): Represents a file artifact.
        REGISTRY (str): Represents a registry artifact.
        NETWORK (str): Represents a network artifact.
        PROCESS (str): Represents a process artifact.
        MODULE (str): Represents a module artifact.
    This enum defines various types of artifacts that can be involved in system calls and operations.
    Each artifact represents a specific type of data or resource.
    """

    FILE = "FILE"
    REGISTRY = "REGISTRY"
    NETWORK = "NETWORK"
    PROCESS = "PROCESS"
    MODULE = "MODULE"

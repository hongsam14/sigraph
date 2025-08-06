"""_summary_
This module defines various actions involved in system calls and operations.
Each action represents a specific role or action in the context of system calls,
"""

from enum import Enum
from typing import Literal
import provenance.exceptions as prov_exceptions


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
    LAUNCH: Literal["LAUNCH"] = "LAUNCH"
    REMOTE_THREAD: Literal["REMOTE_THREAD"] = "REMOTE_THREAD"
    ACCESS: Literal["ACCESS"] = "ACCESS"
    TAMPERING: Literal["TAMPERING"] = "TAMPERING"
    # network actions
    CONNECT: Literal["CONNECT"] = "CONNECT"
    ACCEPT: Literal["ACCEPT"] = "ACCEPT"
    # file actions
    CREATE: Literal["CREATE"] = "CREATE"
    RENAME: Literal["RENAME"] = "RENAME"
    DELETE: Literal["DELETE"] = "DELETE"
    MODIFY: Literal["MODIFY"] = "MODIFY"
    RAW_ACCESS_READ: Literal["RAW_ACCESS_READ"] = "RAW_ACCESS_READ"
    CREATE_STREAM_HASH: Literal["CREATE_STREAM_HASH"] = "CREATE_STREAM_HASH"
    # registry actions
    REG_ADD: Literal["REG_ADD"] = "REG_ADD"
    REG_DELETE: Literal["REG_DELETE"] = "REG_DELETE"
    REG_SET: Literal["REG_SET"] = "REG_SET"
    REG_RENAME: Literal["REG_RENAME"] = "REG_RENAME"
    REG_QUERY: Literal["REG_QUERY"] = "REG_QUERY"


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

    READ_RECV: Literal["READ_RECV"] = "READ_RECV"
    WRITE_SEND: Literal["WRITE_SEND"] = "WRITE_SEND"
    LAUNCH: Literal["LAUNCH"] = "LAUNCH"


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

    FILE: Literal["FILE"] = "FILE"
    REGISTRY: Literal["REGISTRY"] = "REGISTRY"
    NETWORK: Literal["NETWORK"] = "NETWORK"
    PROCESS: Literal["PROCESS"] = "PROCESS"
    MODULE: Literal["MODULE"] = "MODULE"


class SystemProvenance(str):
    """_summary_
    Args:
        str (_type_):
    This class represents a system provenance string.
    It is used to format and parse system provenance data.
    """

    def __new__(cls, value: str):
        """Create a new SystemProvenance instance."""
        if not value:
            raise prov_exceptions.InvalidInputException("Value cannot be empty", ("value", type(value).__name__))
        ## check if value contains '@'
        if "@" not in value:
            raise prov_exceptions.InvalidInputException("Value must contain '@'", ("value", type(value).__name__))
        return str.__new__(cls, value)

    def __str__(self) -> str:
        return self
    
    def __repr__(self) -> str:
        return str(self)
    
class Artifact:
    """_summary_
    Args:
        name (str): The name of the artifact.
        artifact_type (ArtifactType): The type of the artifact.
    This class represents an artifact in the provenance system.
    It includes the name and type of the artifact.
    """
    __name: str
    __artifact_type: ArtifactType

    def __init__(self,
                 name: str,
                 artifact_type: ArtifactType):
        self.__name = name
        self.__artifact_type = artifact_type

    @property
    def name(self) -> str:
        """Get the name of the artifact"""
        return self.__name
    
    @property
    def artifact_type(self) -> ArtifactType:
        """Get the type of the artifact"""
        return self.__artifact_type

    def __str__(self) -> str:
        """Get the string representation of the artifact"""
        return f"{self.name}@{self.artifact_type.name}"

    
class Actor:
    """_summary_
    Args:
        artifact (Artifact): The artifact associated with the actor.
        action_type (ActionType): The action type of the actor.
        actor_type (ActorType): The actor type of the actor.
    This class represents an actor in the provenance system.
    Actors are entities that perform actions on artifacts within the system.
    """
    __artifact: Artifact
    __action_type: ActionType
    __actor_type: ActorType

    def __init__(self,
                 artifact: Artifact,
                 action_type: ActionType,
                 actor_type: ActorType):
        self.__artifact = artifact
        self.__action_type = action_type
        self.__actor_type = actor_type

    @property
    def artifact(self) -> Artifact:
        """Get the artifact associated with the actor"""
        return self.__artifact

    @property
    def action_type(self) -> ActionType:
        """Get the action type of the actor"""
        return self.__action_type
    
    @property
    def actor_type(self) -> ActorType:
        """Get the actor type of the actor"""
        return self.__actor_type
"""_summary_
This module defines the elements for the syscall graph data structure.
"""

from datetime import datetime
from py2neo import Node, Relationship
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from graph.provenance.type import Artifact, ActionType, ActorType
from graph.graph_element.exceptions import InvalidElementException

class SigraphNode(BaseModel):
    """_summary_
    Represents a node in the system provenance graph.

    Args:
        BaseModel (_type_):
        BaseModel is a Pydantic model that provides data validation and serialization.

    Attributes:
        unit_id (UUID): Unique identifier for the node.
        artifact (Artifact): The artifact associated with the node.

    This class represents a node in the system provenance graph.
    Nodes are the fundamental elements of the graph, representing artifacts.
    Each node has a unique id to distinguish user environment, an associated artifact, and optional parent artifacts.
    """

    unit_id: UUID
    artifact: Artifact
    related_span_ids: Optional[List[str]]
    __py2neo_node: Optional[Node] = None

    def __init__(self, unit_id: UUID,
                 artifact: Artifact,
                 related_span_ids: Optional[List[str]] = None):
        
        self.unit_id = unit_id
        self.artifact = artifact
        self.related_span_ids = related_span_ids

        super().__init__(unit_id=unit_id, artifact=artifact)

    def py2neo_node(self) -> Node:
        """_summary
        Convert the SigraphNode instance to a py2neo Node object.
        """
        ## Check if the node has already been created
        if self.__py2neo_node:
            return self.__py2neo_node

        ## Create a py2neo Node object from the SigraphNode instance with essential properties.
        current: Node = Node(Artifact.artifact_type,
                             unit_id=str(self.unit_id),
                             artifact=str(self.artifact),
                             )
        
        ## add additional properties to the node
        if self.related_span_ids:
            current["related_span_ids"] = self.related_span_ids

        ## Store the created node in the instance variable
        self.__py2neo_node = current

        return current

class SigraphRelationship(BaseModel):
    """_summary_
    Represents a relationship in the system provenance graph.

    Args:
        BaseModel (_type_):
        BaseModel is a Pydantic model that provides data validation and serialization.

    Attributes:
        process_node (SigraphNode): The process node associated with the relationship.
        action_node (SigraphNode): The action node associated with the relationship.
        action_type (ActionType): The action type of the relationship.
        actor_type (ActorType): The actor type of the relationship.

    Depending on the actor type, the process_node,
    the relationship before and after the actor_node, and the name of the relationship change.
    """

    process_node: SigraphNode
    action_node: SigraphNode
    action_type: ActionType
    actor_type: ActorType
    __py2neo_relationship: Optional[Relationship] = None

    def __init__(self,
                 process_node: SigraphNode,
                 action_node: SigraphNode,
                 action_type: ActionType,
                 actor_type: ActorType):

        self.process_node = process_node
        self.action_node = action_node
        self.action_type = action_type
        self.actor_type = actor_type

        super().__init__(process_node=process_node,
                         action_node=action_node,
                         action_type=action_type,
                         actor_type=actor_type)

    def py2neo_relationship(self) -> Relationship:
        """_summary_
        Convert the SigraphRelationship instance to a py2neo Relationship object.
        This method creates a relationship based on the actor type and returns it.

        Raises:
            InvalidElementException: If the actor type is invalid.
            Returns:
                Relationship: The created py2neo Relationship object.
        """

        ## Check if the relationship has already been created
        if self.__py2neo_relationship:
            return self.__py2neo_relationship
        
        if self.actor_type == ActorType.READ_RECV:
            rel: Relationship = Relationship(
                self.action_node.py2neo_node(),
                self.action_type.value,
                self.process_node.py2neo_node(),
            )
        elif self.actor_type == ActorType.WRITE_SEND:
            rel: Relationship = Relationship(
                self.process_node.py2neo_node(),
                self.action_type.value,
                self.action_node.py2neo_node(),
            )
        elif self.actor_type == ActorType.LAUNCH:
            rel: Relationship = Relationship(
                self.process_node.py2neo_node(),
                self.action_type.value,
                self.action_node.py2neo_node(),
            )
        else:
            raise InvalidElementException(
                message=f"Invalid actor type: {self.actor_type}",
                element=(str(self.process_node.artifact), str(self.action_node.artifact))
            )
        
        ## Store the created relationship in the instance variable
        self.__py2neo_relationship = rel
        return rel
        
            
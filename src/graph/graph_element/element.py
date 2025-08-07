"""_summary_
This module defines the elements for the syscall graph data structure.
"""

from py2neo import Node, Relationship
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from graph.provenance.type import Artifact, ActionType, ActorType
from graph.graph_element.exceptions import InvalidElementException

class SigraphNode:
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

    __unit_id: UUID
    __artifact: Artifact
    __related_span_ids: Optional[List[str]]
    __neo_node: Node

    def __init__(self, unit_id: UUID,
                 artifact: Artifact,
                 related_span_ids: Optional[List[str]] = None):

        self.__unit_id = unit_id
        self.__artifact = artifact
        self.__related_span_ids = related_span_ids
        self.__neo_node = None

    @property
    def unit_id(self) -> UUID:
        """Get the unique identifier for the node"""
        return self.__unit_id
    
    @property
    def artifact(self) -> Artifact:
        """Get the artifact associated with the node"""
        return self.__artifact
    
    @property
    def related_span_ids(self) -> Optional[List[str]]:
        """Get the related span ids associated with the node"""
        return self.__related_span_ids if self.__related_span_ids else []
    
    def py2neo_node(self) -> Node:
        """_summary
        Convert the SigraphNode instance to a py2neo Node object.
        This method creates a Node object with essential properties and returns it.
        Returns:
            Node: The created py2neo Node object.
        """
        ## Check if the node has already been created
        if self.__neo_node is not None:
            return self.__neo_node

        ## Create a py2neo Node object from the SigraphNode instance with essential properties.
        current: Node = Node(str(self.artifact.artifact_type.value),
                             artifact=str(self.artifact),
                             unit_id=str(self.unit_id),
                             )
        
        ## add additional properties to the node
        if self.related_span_ids:
            current["related_span_ids"] = self.related_span_ids

        ## Store the created node in the instance variable
        self.__neo_node = current

        print(f"Created py2neo node: {current}")

        return current


class SigraphRelationship:
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

    __process_node: SigraphNode
    __action_node: SigraphNode
    __action_type: ActionType
    __actor_type: ActorType
    __neo_relationship: Relationship

    def __init__(self,
                 process_node: SigraphNode,
                 action_node: SigraphNode,
                 action_type: ActionType,
                 actor_type: ActorType):

        self.__process_node = process_node
        self.__action_node = action_node
        self.__action_type = action_type
        self.__actor_type = actor_type
        self.__neo_relationship = None

    @property
    def process_node(self) -> SigraphNode:
        """Get the process node associated with the relationship"""
        return self.__process_node
    
    @property
    def action_node(self) -> SigraphNode:
        """Get the action node associated with the relationship"""
        return self.__action_node
    
    @property
    def action_type(self) -> ActionType:
        """Get the action type of the relationship"""
        return self.__action_type
    
    @property
    def actor_type(self) -> ActorType:
        """Get the actor type of the relationship"""
        return self.__actor_type
    
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
        if self.__neo_relationship is not None:
            return self.__neo_relationship

        if self.actor_type == ActorType.READ_RECV:
            rel: Relationship = Relationship(
                self.__action_node.py2neo_node(),
                str(self.action_type.value),
                self.__process_node.py2neo_node(),
            )
        elif self.actor_type == ActorType.WRITE_SEND:
            rel: Relationship = Relationship(
                self.__process_node.py2neo_node(),
                str(self.action_type.value),
                self.__action_node.py2neo_node(),
            )
        elif self.actor_type == ActorType.NOT_ACTOR:
            rel: Relationship = Relationship(
                self.__process_node.py2neo_node(),
                str(self.action_type.value),
                self.__action_node.py2neo_node(),
            )
        else:
            raise InvalidElementException(
                message=f"Invalid actor type: {self.actor_type}",
                element=(str(self.process_node.artifact), str(self.action_node.artifact))
            )
        
        ## Store the created relationship in the instance variable
        self.__neo_relationship = rel
        return rel
        
            
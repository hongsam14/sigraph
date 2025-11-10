"""_summary_
This module defines the elements for the syscall graph data structure.
"""
from datetime import datetime
from neo4j.time import DateTime
from typing import Optional, List
from uuid import UUID
from graph.provenance.type import Artifact, ActionType, ActorType
from graph.graph_element.exceptions import InvalidElementException
from graph.graph_client.node import Node, Relationship, NodeExtension

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

    __labels: List[str]
    __artifact: Artifact
    __process_name: Optional[str]
    __related_span_ids: Optional[List[str]]
    __related_trace_ids: Optional[List[str]]
    __graph_node: Node

    def __init__(self,
                 artifact: Artifact,
                 process_name: Optional[str] = None,
                 related_span_ids: Optional[List[str]] = None,
                 related_trace_ids: Optional[List[str]] = None):

        self.__artifact = artifact
        self.__labels = [str(artifact.artifact_type.value)]
        self.__process_name = process_name
        self.__related_span_ids = related_span_ids
        self.__related_trace_ids = related_trace_ids
        self.__graph_node = None

    @property
    def artifact(self) -> Artifact:
        """Get the artifact associated with the node"""
        return self.__artifact
    
    @property
    def related_span_ids(self) -> Optional[List[str]]:
        """Get the related span ids associated with the node"""
        return self.__related_span_ids if self.__related_span_ids else []
    
    @property
    def related_trace_ids(self) -> Optional[List[str]]:
        """Get the related trace ids associated with the node"""
        return self.__related_trace_ids if self.__related_trace_ids else []

    @property
    def image(self) -> Optional[str]:
        """Get the process name associated with the node"""
        return self.__process_name

    def to_node(self) -> Node:
        """_summary
        Convert the SigraphNode instance to a py2neo Node object.
        This method creates a Node object with essential properties and returns it.
        Returns:
            Node: The created py2neo Node object.
        """
        ## Check if the node has already been created
        if self.__graph_node is not None:
            return self.__graph_node

        ## Create a py2neo Node object from the SigraphNode instance with essential properties.
        current: Node = Node(
            labels=self.__labels,
            properties={
                "artifact": str(self.artifact),
            }
        )

        ## add additional properties to the node
        if self.image:
            current["image"] = self.image

        if self.related_span_ids:
            current["related_span_ids"] = self.related_span_ids

        if self.related_trace_ids:
            current["related_trace_ids"] = self.related_trace_ids

        ## Store the created node in the instance variable
        self.__graph_node = current
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
    __start_time: datetime
    __weight: int
    __graph_relationship: Relationship

    def __init__(self,
                 process_node: SigraphNode,
                 action_node: SigraphNode,
                 action_type: ActionType,
                 actor_type: ActorType,
                 start_time: datetime,
                 weight: int
                 ):

        self.__process_node = process_node
        self.__action_node = action_node
        self.__action_type = action_type
        self.__actor_type = actor_type
        self.__start_time = start_time
        self.__weight = weight
        self.__graph_relationship = None

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

    @property
    def start_time(self) -> datetime:
        """Get the start time of the relationship"""
        return self.__start_time
    
    @property
    def weight(self) -> int:
        """Get the weight of the relationship"""
        return self.__weight

    def to_relationship(self) -> Relationship:
        """_summary_
        Convert the SigraphRelationship instance to a py2neo Relationship object.
        This method creates a relationship based on the actor type and returns it.

        Raises:
            InvalidElementException: If the actor type is invalid.
            Returns:
                Relationship: The created py2neo Relationship object.
        """

        ## Check if the relationship has already been created
        if self.__graph_relationship is not None:
            return self.__graph_relationship

        if self.actor_type == ActorType.READ_RECV:
            rel: Relationship = Relationship(
                start=self.__action_node.to_node(),
                type=str(self.action_type.value),
                end=self.__process_node.to_node(),
                properties={
                    "start_time": self.start_time,
                    "weight": self.weight,
                }
            )
        elif self.actor_type == ActorType.WRITE_SEND:
            rel: Relationship = Relationship(
                start=self.__process_node.to_node(),
                type=str(self.action_type.value),
                end=self.__action_node.to_node(),
                properties={
                    "start_time": self.start_time,
                    "weight": self.weight,
                }
            )
        elif self.actor_type == ActorType.NOT_ACTOR:
            rel: Relationship = Relationship(
                start=self.__process_node.to_node(),
                type=str(self.action_type.value),
                end=self.__action_node.to_node(),
                properties={
                    "start_time": self.start_time,
                    "weight": self.weight,
                }
            )
        else:
            raise InvalidElementException(
                message=f"Invalid actor type: {self.actor_type}",
                element=(str(self.process_node.artifact), str(self.action_node.artifact))
            )
        
        ## Store the created relationship in the instance variable
        self.__graph_relationship = rel
        return rel
    
class SigraphTrace:
    __labels: list[str] = ["Trace"]
    __trace_id: str
    __unit_id: UUID
    __start_time: datetime
    __representative_process_name: Optional[str]
    __span_count: Optional[int]
    __graph_node: Node

    def __init__(self,
                 trace_id: str,
                 unit_id: UUID,
                 start_time: datetime,
                 representative_process_name: Optional[str] = None,
                 span_count: Optional[int] = None
                 ):
        self.__trace_id = trace_id
        self.__unit_id = unit_id
        self.__start_time = start_time
        self.__representative_process_name = representative_process_name
        self.__span_count = span_count
        self.__graph_node = None

    @property
    def trace_id(self) -> str:
        return self.__trace_id

    @property
    def unit_id(self) -> UUID:
        return self.__unit_id
    
    @property
    def start_time(self) -> datetime:
        return self.__start_time
    
    @property
    def neo_time(self) -> DateTime:
        return DateTime.from_native(self.__start_time)

    @start_time.setter
    def start_time(self, value: datetime):
        self.__start_time = value

    @neo_time.setter
    def neo_time(self, value: DateTime):
        self.__start_time = datetime.fromtimestamp(value.to_native().timestamp())

    @property
    def representative_process_name(self) -> Optional[str]:
        return self.__representative_process_name

    @representative_process_name.setter
    def representative_process_name(self, value: Optional[str]):
        self.__representative_process_name = value

    @property
    def span_count(self) -> Optional[int]:
        return self.__span_count

    @span_count.setter
    def span_count(self, value: Optional[int]):
        self.__span_count = value

    
    def to_node(self) -> Node:
        """_summary_
        Convert the SigraphTrace instance to a py2neo Node object.
        This method creates a Node object with essential properties and returns it.
        Returns:
            Node: The created py2neo Node object.
        """
        ## Check if the node has already been created
        if self.__graph_node is not None:
            ## check for node updates
            if (self.__graph_node.get("span_count") == self.__span_count) and \
                (self.__graph_node.get("start_time") == self.__start_time) and \
                (self.__graph_node.get("representative_process_name") == self.__representative_process_name):
                return self.__graph_node

        ## Create a py2neo Node object from the SigraphTraceDocument instance with essential properties.
        current: Node = Node(labels=self.__labels,
                             properties={
                                 "trace_id": self.trace_id,
                                 "unit_id": str(self.unit_id)
                             })
        ## append additional properties to the node
        if self.__start_time:
            current["start_time"] = self.__start_time
        if self.__representative_process_name:
            current["representative_process_name"] = self.__representative_process_name
        if self.__span_count is not None:
            current["span_count"] = self.__span_count
        
        ## Store the created node in the instance variable
        self.__graph_node = current

        return current


class SigraphTraceRelationship:
    __trace_node: SigraphTrace
    __syscall_node: SigraphNode
    __relation_name: str = "CONTAINS"
    __graph_relationship: Relationship

    def __init__(self,
                trace_node: SigraphTrace,
                node: SigraphNode):
        self.__trace_node = trace_node
        self.__syscall_node = node
        self.__graph_relationship = None

    @property
    def trace_node(self) -> SigraphTrace:
        return self.__trace_node
    
    @property
    def syscall_node(self) -> SigraphNode:
        return self.__syscall_node

    @property
    def relation_name(self) -> str:
        return self.__relation_name
    
    def to_relationship(self) -> Relationship:
        if self.__graph_relationship is not None:
            return self.__graph_relationship
        rel: Relationship = Relationship(
            start=self.__trace_node.to_node(),
            type=self.__relation_name,
            end=self.__syscall_node.to_node(),
        )
        self.__graph_relationship = rel
        return rel
    

class SigraphSigmaRule:
    __labels: list[str] = ["SigmaRule"]
    __rule_id: str
    __graph_node: Node

    def __init__(self,
                 rule_id: str):
        self.__rule_id = rule_id
        self.__graph_node = None

    @property
    def rule_id(self) -> str:
        return self.__rule_id

    def to_node(self) -> Node:
        """_summary
        Convert the SigraphSigmaRule instance to a py2neo Node object.
        This method creates a Node object with essential properties and returns it.
        Returns:
            Node: The created py2neo Node object.
        """
        ## Check if the node has already been created
        if self.__graph_node is not None:
            return self.__graph_node

        ## Create a py2neo Node object from the SigraphSigmaRule instance with essential properties.
        current: Node = Node(
            labels=self.__labels,
            properties={
                "rule_id": self.rule_id
            }
        )

        ## Store the created node in the instance variable
        self.__graph_node = current

        return current

class SigraphSigmaRuleRelationship:
    __rule_node: SigraphSigmaRule
    __syscall_node: SigraphNode
    __relation_name: str = "MATCHES"
    __graph_relationship: Relationship

    def __init__(self,
                rule_node: SigraphSigmaRule,
                node: SigraphNode):
        self.__rule_node = rule_node
        self.__syscall_node = node
        self.__graph_relationship = None

    @property
    def rule_node(self) -> SigraphSigmaRule:
        return self.__rule_node
    
    @property
    def syscall_node(self) -> SigraphNode:
        return self.__syscall_node

    @property
    def relation_name(self) -> str:
        return self.__relation_name
    
    def to_relationship(self) -> Relationship:
        if self.__graph_relationship is not None:
            return self.__graph_relationship
        rel: Relationship = Relationship(
            start=self.__rule_node.to_node(),
            type=self.__relation_name,
            end=self.__syscall_node.to_node(),
        )
        self.__graph_relationship = rel
        return rel
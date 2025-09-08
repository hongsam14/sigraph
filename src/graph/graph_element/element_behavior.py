"""_summary_
This module provides extensions for graph elements, including conversion from py2neo nodes to SigraphNode
and upserting SystemProvenance into the graph.
"""

from datetime import datetime
from typing import Optional
from py2neo import Graph, Node
from uuid import UUID
from graph.provenance.type import SystemProvenance, Actor, Artifact
from graph.provenance.type_extension import ActorExtension, ArtifactExtension
from graph.graph_element.exceptions import InvalidInputException, InvalidElementException, GraphDBInteractionException
from graph.graph_element.element import SigraphNode, SigraphRelationship

class GraphElementBehavior:
    """_summary_
    This class provides methods to handle SigraphNode instances,
    including conversion from py2neo nodes and upserting SystemProvenance into the graph.
    """
    
    @staticmethod
    def from_py2neo_node_to_sigraph(node: Node) -> "SigraphNode":
        """_summary_
        Convert a py2neo Node object to a SigraphNode instance.
        
        Args:
            node (Node): The py2neo Node object to convert.
        
        Returns:
            SigraphNode: The converted SigraphNode instance.

        Raises:
            InvalidInputException: If the node is None or does not contain required properties.
            InvalidElementException: If the node does not contain 'unit_id' and 'artifact' properties.
        """
        if not node:
            raise InvalidInputException("Node cannot be None", ("node", type(node).__name__))
        if not "unit_id" in node or not "artifact" in node:
            raise InvalidElementException("Node must contain 'unit_id' and 'artifact' properties", ("node", type(node).__name__))
        return SigraphNode(
            unit_id=UUID(node["unit_id"]),
            artifact=ArtifactExtension.from_systemprovenance(node["artifact"]),
            related_span_ids=node.get("related_span_ids", []),
        )
    
    @staticmethod
    def get_sigraph_node_from_graph(
        graph_client: Graph,
        unit_id: UUID,
        artifact: Artifact
    ) -> Optional[SigraphNode]:
        """_summary_
        Get a SigraphNode from the graph by unit_id and artifact.
        
        Args:
            graph_client (Graph): The graph client to interact with the graph database.
            unit_id (UUID): The unique identifier for the node.
            artifact (Artifact): The artifact associated with the node.
        
        Returns:
            Optional[SigraphNode]: The retrieved SigraphNode instance or None if not found.

        Raises:
            InvalidInputException: If the graph client, unit_id, or artifact is invalid.
            GraphDBInteractionException: If there is an error interacting with the graph database.
        """
        if not graph_client:
            raise InvalidInputException("Graph cannot be None", ("graph", type(graph_client).__name__))
        if not unit_id:
            raise InvalidInputException("Unit ID cannot be empty", ("unit_id", type(unit_id).__name__))
        if not artifact:
            raise InvalidInputException("Artifact cannot be empty", ("artifact", type(artifact).__name__))
        
        try:
            ## search for existing nodes with the same unit_id and artifact
            exist_nodes: list[Node] = graph_client.run(
                f"""
                MATCH (n:{str(artifact.artifact_type.value)})
                WHERE n.unit_id = $unit_id AND n.artifact = $artifact
                RETURN n as node
                """,
                artifact_type=str(artifact.artifact_type.value),
                unit_id=str(unit_id),
                artifact=str(artifact)
                ).data()
            if not exist_nodes:
                return None
            ## if there are multiple nodes, raise an exception. because artifact should be unique.
            if len(exist_nodes) > 1:
                raise InvalidElementException(
                    "Multiple nodes found with the same unit_id and artifact. Artifact should be unique.",
                    ("unit_id", str(unit_id), "artifact", str(artifact))
                )
            return GraphElementBehavior.from_py2neo_node_to_sigraph(exist_nodes[0]["node"])
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to search for existing nodes in the graph: {e}",
                ("unit_id", str(unit_id), "artifact", str(artifact))
            ) from e
    
    @staticmethod
    def upsert_systemprovenance(
        graph_client: Graph,
        unit_id: UUID,
        trace_id: str,
        timestamp: datetime,
        parent_id: Optional[str],
        related_span_id: str,
        system_provenance: SystemProvenance,
        parent_system_provenance: Optional[SystemProvenance],
    ):
        """_summary_
        Convert a SystemProvenance instance to a graph element.

        Args:
            unit_id (UUID): The unique identifier for the unit.
            parent_id (str): The ID of the parent element.
            related_span_id (str): The ID of the related span.
            system_provenance (SystemProvenance): The SystemProvenance instance to convert.

        Returns:
            SigraphNode: The converted graph element.

        Raises:
            InvalidInputException: If any of the input parameters are invalid.
            GraphDBInteractionException: If there is an error interacting with the graph database.
        """

        if not graph_client:
            raise InvalidInputException("Graph cannot be None", ("graph", type(graph_client).__name__))
        if not unit_id:
            raise InvalidInputException("Unit ID cannot be empty", ("unit_id", type(unit_id).__name__))
        if not system_provenance:
            raise InvalidInputException("SystemProvenance cannot be empty", ("system_provenance", type(system_provenance).__name__))
        

        ## create an Actor instance from the system_provenance
        actor: Actor = ActorExtension.from_systemprovenance(system_provenance)

        try:
            ## search for the same syscall object in the graph
            related_span_ids: list[str] = []
            
            ## search for existing nodes with the same unit_id and artifact
            exist_node: SigraphNode | None = GraphElementBehavior.get_sigraph_node_from_graph(
                graph_client, unit_id, actor.artifact
            )
            
            if exist_node and exist_node.related_span_ids:
                related_span_ids = exist_node.related_span_ids
                
            ## append the new related_span_id to the existing related_span_ids
            if related_span_id and related_span_id not in related_span_ids:
                related_span_ids.append(related_span_id)

            current_node: SigraphNode = SigraphNode(
                unit_id=unit_id,
                artifact=actor.artifact,
                related_span_ids=related_span_ids,
            )

            ## create an parent process artifact
            if parent_id is not None and parent_system_provenance is not None:
                parent_artifact: Artifact = ArtifactExtension.from_parent_action(parent_system_provenance)

                ## create parent artifact node or use existing one
                exist_parent_node: SigraphNode | None = GraphElementBehavior.get_sigraph_node_from_graph(
                    graph_client, unit_id, parent_artifact
                )

                if exist_parent_node:
                    ## if the parent node already exists, use it
                    parent_node: SigraphNode = exist_parent_node
                else:
                    ## if the parent node does not exist, create a new one
                    parent_node = SigraphNode(
                        unit_id=unit_id,
                        artifact=parent_artifact,
                    )

                ## create a relationship between the parent node and the current node
                relationship: SigraphRelationship = SigraphRelationship(
                    process_node=parent_node,
                    action_node=current_node,
                    action_type=actor.action_type,
                    actor_type=actor.actor_type
                )

        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to query system provenance: {e}",
                (
                    "unit_id", str(unit_id),
                    "parent_id", str(parent_id) if parent_id is not None else "NONE",
                    "related_span_id", str(related_span_id),
                    "system_provenance", str(system_provenance)
                )
            ) from e

        ## merge the node and relationship into the graph
        try:
            graph_client.merge(current_node.py2neo_node(), str(current_node.artifact.artifact_type.value), "artifact")
            if parent_id is not None:
                # If parent_id is provided, merge the parent node and create a relationship
                graph_client.merge(parent_node.py2neo_node(), str(parent_node.artifact.artifact_type.value), "artifact")
                graph_client.create(relationship.py2neo_relationship())
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to merge node and relationship into the graph: {e}",
                ("unit_id", str(unit_id), "artifact", str(actor.artifact))
            ) from e

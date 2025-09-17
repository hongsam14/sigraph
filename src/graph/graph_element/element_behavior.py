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
from graph.graph_element.element import SigraphNode, SigraphRelationship, SigraphTrace, SigraphTraceRelationship

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
        return SigraphNode(
            artifact=ArtifactExtension.from_systemprovenance(node["artifact"]),
            process_name=node.get("process_name"),
            related_span_ids=node.get("related_span_ids", []),
            related_trace_ids=node.get("related_trace_ids", []),
        )
    
    @staticmethod
    def from_py2neo_trace_node_to_sigraph(node: Node) -> SigraphTrace:
        """_summary_
        Convert a py2neo Node object to a SigraphTrace instance.
        
        Args:
            node (Node): The py2neo Node object to convert.
        
        Returns:
            SigraphTrace: The converted SigraphTrace instance.

        Raises:
            InvalidInputException: If the node is None or does not contain required properties.
            InvalidElementException: If the node does not contain 'unit_id' and 'trace_id' properties.
        """
        if not node:
            raise InvalidInputException("Node cannot be None", ("node", type(node).__name__))
        if not "unit_id" in node or not "trace_id" in node:
            raise InvalidElementException("Node must contain 'unit_id' and 'trace_id' properties", ("node", type(node).__name__))
        return SigraphTrace(
            trace_id=node["trace_id"],
            unit_id=UUID(node["unit_id"])
        )
    
    @staticmethod
    def get_sigraph_node_from_graph(
        graph_client: Graph,
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
        if not artifact:
            raise InvalidInputException("Artifact cannot be empty", ("artifact", type(artifact).__name__))
        
        try:
            ## search for existing nodes with the same unit_id and artifact
            exist_nodes: list[Node] = graph_client.run(
                cypher=f"""
                MATCH (n:{str(artifact.artifact_type.value)})
                WHERE n.artifact = $artifact
                RETURN n as node
                """,
                artifact_type=str(artifact.artifact_type.value),
                artifact=str(artifact)
                ).data()
            if not exist_nodes:
                return None
            ## if there are multiple nodes, raise an exception. because artifact should be unique.
            if len(exist_nodes) > 1:
                raise InvalidElementException(
                    "Multiple nodes found with the same unit_id and artifact. Artifact should be unique.",
                    ("artifact", str(artifact))
                )
            return GraphElementBehavior.from_py2neo_node_to_sigraph(exist_nodes[0]["node"])
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to search for existing nodes in the graph: {e}",
                ("artifact", str(artifact))
            ) from e
        
    @staticmethod
    def get_sigraph_trace_from_graph(
        graph_client: Graph,
        trace_id: str,
        unit_id: UUID
    ) -> Optional[SigraphTrace]:
        """_summary_
        Get a SigraphTrace from the graph by trace_id.
        
        Args:
            graph_client (Graph): The graph client to interact with the graph database.
            trace_id (str): The unique identifier for the trace.
            unit_id (UUID): The unique identifier for the unit.
        Returns:
            Optional[SigraphTrace]: The retrieved SigraphTrace instance or None if not found.
        Raises:
            InvalidInputException: If the graph client or trace_id is invalid.
            GraphDBInteractionException: If there is an error interacting with the graph database.
        """
        if not graph_client:
            raise InvalidInputException("Graph cannot be None", ("graph", type(graph_client).__name__))
        if not trace_id:
            raise InvalidInputException("Trace ID cannot be empty", ("trace_id", type(trace_id).__name__))
        if not unit_id:
            raise InvalidInputException("Unit ID cannot be empty", ("unit_id", type(unit_id).__name__))
        try:
            ## search for existing trace node with the same trace_id
            exist_traces: list[Node] = graph_client.run(
                cypher="""
                MATCH (t:Trace)
                WHERE t.trace_id = $trace_id AND t.unit_id = $unit_id
                RETURN t as trace
                """,
                trace_id=trace_id,
                unit_id=str(unit_id)
                ).data()
            if not exist_traces:
                return None
            ## if there are multiple traces, raise an exception. because trace_id should be unique.
            if len(exist_traces) > 1:
                raise InvalidElementException(
                    "Multiple traces found with the same trace_id. Trace ID should be unique.",
                    ("trace_id", str(trace_id), "unit_id", str(unit_id))
                )
            trace_node: Node = exist_traces[0]["trace"]
            return GraphElementBehavior.from_py2neo_trace_node_to_sigraph(trace_node)
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to search for existing traces in the graph: {e}",
                ("trace_id", str(trace_id), "unit_id", str(unit_id))
            ) from e

    @staticmethod
    def upsert_systemprovenance(
        graph_client: Graph,
        unit_id: UUID,
        trace_id: str,
        timestamp: datetime,
        weight: int,
        related_span_id: str,
        system_provenance: SystemProvenance,
        process_name: Optional[str],
        parent_id: Optional[str],
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
        if not related_span_id:
            raise InvalidInputException("Related Span ID cannot be empty", ("related_span_id", type(related_span_id).__name__))
        if not trace_id:
            raise InvalidInputException("Trace ID cannot be empty", ("trace_id", type(trace_id).__name__))
        if not timestamp:
            raise InvalidInputException("Timestamp cannot be empty", ("timestamp", type(timestamp).__name__))
        if not weight or weight < 1:
            raise InvalidInputException("Weight must be a positive integer", ("weight", type(weight).__name__))
        

        ## create an Actor instance from the system_provenance
        actor: Actor = ActorExtension.from_systemprovenance(system_provenance)

        try:
            ## search for the same syscall object in the graph
            related_span_ids: list[str] = []
            related_trace_ids: list[str] = []
            
            ## search for existing nodes with the same unit_id and artifact
            exist_node: SigraphNode | None = GraphElementBehavior.get_sigraph_node_from_graph(
                graph_client=graph_client, artifact=actor.artifact
            )
            
            if exist_node and exist_node.related_span_ids:
                related_span_ids = exist_node.related_span_ids

            if exist_node and exist_node.related_trace_ids:
                related_trace_ids = exist_node.related_trace_ids
                
            ## append the new related_span_id to the existing related_span_ids
            if related_span_id and related_span_id not in related_span_ids:
                related_span_ids.append(related_span_id)

            ## append the new trace_id to the existing related_trace_ids
            if trace_id and trace_id not in related_trace_ids:
                related_trace_ids.append(trace_id)

            if process_name is None and exist_node and exist_node.image:
                process_name = exist_node.image

            current_node: SigraphNode = SigraphNode(
                artifact=actor.artifact,
                process_name=process_name,
                related_span_ids=related_span_ids,
                related_trace_ids=related_trace_ids,
            )

            ## create an parent process artifact
            if parent_id is not None and parent_system_provenance is not None:
                parent_artifact: Artifact = ArtifactExtension.from_parent_action(parent_system_provenance)

                ## create parent artifact node or use existing one
                exist_parent_node: SigraphNode | None = GraphElementBehavior.get_sigraph_node_from_graph(
                    graph_client=graph_client, artifact=parent_artifact
                )

                if exist_parent_node:
                    ## if the parent node already exists, use it
                    parent_node: SigraphNode = exist_parent_node
                else:
                    ## if the parent node does not exist, create a new one
                    parent_node = SigraphNode(
                        artifact=parent_artifact,
                    )

                ## create a relationship between the parent node and the current node
                relationship: SigraphRelationship = SigraphRelationship(
                    process_node=parent_node,
                    action_node=current_node,
                    action_type=actor.action_type,
                    actor_type=actor.actor_type,
                    start_time=timestamp,
                    weight=weight
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
            
            ## add trace & trace relationship
            ## search for existing trace node with the same trace_id
            trace = GraphElementBehavior.get_sigraph_trace_from_graph(
                graph_client=graph_client, trace_id=trace_id, unit_id=unit_id
            )
            if not trace:
                ## create a new trace node
                trace = SigraphTrace(
                    trace_id=trace_id,
                    unit_id=unit_id
                )

            graph_client.merge(trace.py2neo_node(), "Trace", "trace_id")
            ## create a relationship between the trace and the syscall node later
            trace_relationship: SigraphTraceRelationship = SigraphTraceRelationship(
                trace_node=trace,
                node=current_node,
            )
            graph_client.create(trace_relationship.py2neo_relationship())
        
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to merge node and relationship into the graph: {e}",
                ("unit_id", str(unit_id), "artifact", str(actor.artifact))
            ) from e

    @staticmethod
    def clean_debris(
                     graph_client: Graph,
                     unit_id: UUID):
        """_summary_
        Cleans up any orphaned or inconsistent data in the Neo4j database.
        """
        query = """
    MATCH (t:Trace)-[:CONTAINS]->(n)
    WHERE t.unit_id = $unit_id
      AND COUNT{ (t)-[:CONTAINS]->() } = 1
      AND COUNT{ (n)--() } = 1
    DETACH DELETE t, n
    """
        if not graph_client:
            raise InvalidInputException("Graph cannot be None", ("graph", type(graph_client).__name__))
        if not unit_id:
            raise InvalidInputException("Unit ID cannot be empty", ("unit_id", type(unit_id).__name__))
        try:
            ## run task with transaction
            ## because this task is deleting nodes, we need to use a transaction
            tx = graph_client.begin()
            cursor = tx.run(
                query,
                unit_id=str(unit_id) if unit_id else None
            )
            tx.commit()
            # return the result
            stats = cursor.stats() or {}
            return {
                "nodes_deleted": stats.get("nodes_deleted", 0),
                "relationships_deleted": stats.get("relationships_deleted", 0)
            }
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to clean debris in the graph: {e}",
                ("unit_id", str(unit_id))
            ) from e

    @staticmethod
    def get_related_trace_ids(
        graph_client: Graph,
        unit_id: UUID,
        trace_id: str,
        max_hop: int = 5
    ) -> list[str]:
        """_summary_
        Get all trace IDs connected to the given trace ID within the same unit.
        
        Args:
            graph_client (Graph): The graph client to interact with the graph database.
            unit_id (UUID): The unique identifier for the unit.
            trace_id (str): The unique identifier for the trace.
            max_hop (int): The maximum number of hops to traverse in the graph.
        """

        if not graph_client:
            raise InvalidInputException("Graph cannot be None", ("graph", type(graph_client).__name__))
        if not unit_id:
            raise InvalidInputException("Unit ID cannot be empty", ("unit_id", type(unit_id).__name__))
        if not trace_id:
            raise InvalidInputException("Trace ID cannot be empty", ("trace_id", type(trace_id).__name__))
        if max_hop < 2:
            raise InvalidInputException("Max hop must be greater than 1", ("max_hop", type(max_hop).__name__))
        
        try:
            query = f"""\
    MATCH (t1:Trace {{trace_id: $traceId, unit_id: $unitId}})
    MATCH p = (t1)-[*1..{max_hop}]-(t2:Trace {{unit_id: $unitId}})
    WITH t1, t2, p
    WHERE elementId(t1) < elementId(t2)
    RETURN t1, t2
    ORDER BY length(p) ASC
    """
            # run the query
            result = graph_client.run(
                query,
                traceId=trace_id,
                unitId=str(unit_id),
            )

            # get trace ids from the result
            trace_ids: list[str] = []
            for record in result:
                t2 = record["t2"]
                trace_ids.append(t2["trace_id"])
            return list(set(trace_ids))  # return unique trace ids
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to get connected trace IDs: {e}",
                ("unit_id", str(unit_id), "trace_id", str(trace_id))
            ) from e

"""_summary_
This module provides extensions for graph elements, including conversion from py2neo nodes to SigraphNode
and upserting SystemProvenance into the graph.
"""
from datetime import datetime
from typing import Any, Dict, Optional, LiteralString, cast
from uuid import UUID
from graph.graph_element.schema import (
    CONSTRAINTS,
    QUERY_ARTIFACT,
    QUERY_TRACES,
    QUERY_RELATED_TRACES,
    QUERY_TRACE_WITH_TRACE_ID,
    QUERY_RULE,
    QUERY_ALL_PROVENANCE,
    FLUSH_SINGLE_ENTITIES_WITH_TRACE
    )
from graph.provenance.type import SystemProvenance, Actor, Artifact
from graph.provenance.type_extension import ActorExtension, ArtifactExtension
from graph.graph_element.exceptions import InvalidInputException, InvalidElementException, GraphDBInteractionException
from graph.graph_element.element import (
                                        SigraphNode,
                                        SigraphRelationship,
                                        SigraphTrace,
                                        SigraphTraceRelationship,
                                        SigraphSigmaRule,
                                        SigraphSigmaRuleRelationship
                                        )
from graph.graph_element.helper import to_prefab
from graph.graph_client.node import Node, Relationship, NodeExtension
from graph.graph_client.client import GraphClient



class GraphElementBehavior:
    """_summary_
    This class provides methods to handle SigraphNode instances,
    including conversion from py2neo nodes and upserting SystemProvenance into the graph.
    """
    
    @staticmethod
    def from_graph_node_to_sigraph(node: Node) -> "SigraphNode":
        """_summary_
        Convert a graph Node object to a SigraphNode instance.
        
        Args:
            node (Node): The graph Node object to convert.

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
    def from_graph_trace_node_to_sigraph(node: Node) -> SigraphTrace:
        """_summary_
        Convert a graph Node object to a SigraphTrace instance.

        Args:
            node (Node): The graph Node object to convert.
        
        Returns:
            SigraphTrace: The converted SigraphTrace instance.

        Raises:
            InvalidInputException: If the node is None or does not contain required properties.
            InvalidElementException: If the node does not contain 'unit_id' and 'trace_id' properties.
        """
        if not node:
            raise InvalidInputException("Node cannot be None", ("node", type(node).__name__))
        if not "unit_id" in node or not "trace_id" in node or "start_time" not in node:
            raise InvalidElementException("Node must contain 'unit_id', 'start_time' and 'trace_id' properties", ("node", type(node).__name__))
        ## convert timestamp string to datetime object
        out: SigraphTrace = SigraphTrace(
            trace_id=node["trace_id"],
            unit_id=UUID(node["unit_id"]),
            start_time=datetime.now(),
            representative_process_name=node.get("representative_process_name"),
            span_count=node.get("span_count"),
        )
        ## update start_time property
        out.neo_time = node["start_time"]
        return out

    @staticmethod
    async def apply_constraints(graph_client:GraphClient):
        """_summary_
        Apply constraints to the Neo4j graph database.

        Args:
            graph_client (Graph): The graph client to interact with the graph database.
        """
        for constraint, query in CONSTRAINTS.items():
            if constraint == "Artifact":
                ## apply constraints for each ArtifactType
                for artifact_type in ArtifactExtension.get_all_artifact_types():
                    cypher_str = query.replace("{{$ArtifactType}}", str(artifact_type))
                    cypher = cast(LiteralString, cypher_str)
            elif constraint == "Trace":
                cypher = cast(LiteralString, query)
            # run the constraint query
            await graph_client.run(cypher)
    
    @staticmethod
    async def get_sigraph_node_from_graph(
        graph_client: GraphClient,
        artifact: Artifact
    ) -> Optional[SigraphNode]:
        """_summary_
        Get a SigraphNode from the graph by unit_id and artifact.

        Args:
            graph_client (GraphClient): The graph client to interact with the graph database.
            artifact (Artifact): The artifact associated with the node.

        Returns:
            Optional[SigraphNode]: The retrieved SigraphNode instance or None if not found.
        """
        if not graph_client:
            raise InvalidInputException("Graph cannot be None", ("graph", type(graph_client).__name__))
        if not artifact:
            raise InvalidInputException("Artifact cannot be empty", ("artifact", type(artifact).__name__))
        
        try:
            ## search for existing nodes with the same unit_id and artifact
            exist_nodes: list[dict[str, Any]] = await graph_client.run(
                cypher=QUERY_ARTIFACT(artifact.artifact_type),
                artifact=str(artifact)
                )
            if not exist_nodes or len(exist_nodes) == 0:
                return None
            ## if there are multiple nodes, raise an exception. because artifact should be unique.
            if len(exist_nodes) > 1:
                raise InvalidElementException(
                    "Multiple nodes found with the same unit_id and artifact. Artifact should be unique.",
                    ("artifact", str(artifact))
                )
            return GraphElementBehavior.from_graph_node_to_sigraph(
                NodeExtension.dict_to_node(labels=[str(artifact.artifact_type)], data=exist_nodes[0]["node"])
                )
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to search for existing nodes in the graph: {e}",
                ("artifact", str(artifact))
            ) from e
        
    @staticmethod
    async def get_sigraph_trace_from_graph(
        graph_client: GraphClient,
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
            exist_traces: list[dict[str, Any]] = await graph_client.run(
                cypher=QUERY_TRACE_WITH_TRACE_ID(),
                trace_id=trace_id,
                unit_id=str(unit_id)
                )
            if not exist_traces or len(exist_traces) == 0:
                return None
            ## if there are multiple traces, raise an exception. because trace_id should be unique.
            if len(exist_traces) > 1:
                raise InvalidElementException(
                    "Multiple traces found with the same trace_id. Trace ID should be unique.",
                    ("trace_id", str(trace_id), "unit_id", str(unit_id))
                )
            return GraphElementBehavior.from_graph_trace_node_to_sigraph(
                NodeExtension.dict_to_node(labels=['Trace'], data=exist_traces[0]["node"])
                )
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to search for existing traces in the graph: {e}",
                ("trace_id", str(trace_id), "unit_id", str(unit_id))
            ) from e
        
    @staticmethod
    async def get_sigraph_sigma_rule_from_graph(
            graph_client: GraphClient,
            rule_id: str,
    ) -> Optional[SigraphSigmaRule]:
        """_summary_
        Get a SigraphSigmaRule from the graph by rule_id.

        Args:
            graph_client (Graph): The graph client to interact with the graph database.
            rule_id (str): The unique identifier for the sigma rule.
        
        Returns:
            Optional[SigraphSigmaRule]: The retrieved SigraphSigmaRule instance or None if not
        
        Raised:
            InvalidInputException: If the graph client or rule_id is invalid.
            GraphDBInteractionException: If there is an error interacting with the graph database.
        """
        if not graph_client:
            raise InvalidInputException("Graph cannot be None", ("graph", type(graph_client).__name__))
        if not rule_id:
            raise InvalidInputException("Rule ID cannot be empty", ("rule_id", type(rule_id).__name__))
        try:
            ## search for existing sigma rule node with the same rule_id
            exist_rules: list[dict[str, Any]] = await graph_client.run(
                cypher=QUERY_RULE(),
                rule_id=rule_id
                )
            if not exist_rules or len(exist_rules) == 0:
                return None
            ## if there are multiple rules, raise an exception. because rule_id should be unique.
            if len(exist_rules) > 1:
                raise InvalidElementException(
                    "Multiple sigma rules found with the same rule_id. Rule ID should be unique.",
                    ("rule_id", str(rule_id))
                )
            rule_node: Node = NodeExtension.dict_to_node(labels=['SigmaRule'], data=exist_rules[0]["node"])
            return SigraphSigmaRule(
                rule_id=rule_node["rule_id"],
            )
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to search for existing sigma rules in the graph: {e}",
                ("rule_id", str(rule_id))
            ) from e


    @staticmethod
    async def upsert_systemprovenance(
        graph_client: GraphClient,
        ## node
        unit_id: UUID,
        trace_id: str,
        system_provenance: SystemProvenance,
        ## relationship attributes
        timestamp: datetime,
        weight: int,
        ## parent attributes
        parent_id: Optional[str],
        parent_system_provenance: Optional[SystemProvenance],
        ## node attributes
        related_span_id: str,
        process_name: Optional[str],
        related_rule_ids: Optional[list[str]],
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
        if weight is None or weight < 1:
            raise InvalidInputException("Weight must be a positive integer", ("weight", type(weight).__name__))
        

        ## create an Actor instance from the system_provenance
        actor: Actor = ActorExtension.from_systemprovenance(system_provenance)

        try:
            ## search for the same syscall object in the graph
            related_span_ids: list[str] = []
            related_trace_ids: list[str] = []
            
            ## Current Node Sequence ====================================
            ## search for existing nodes with the same unit_id and artifact
            exist_node: SigraphNode | None = await GraphElementBehavior.get_sigraph_node_from_graph(
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
            ## ===========================================================
            
            ## Trace Node Sequence ======================================
            ## search for existing trace node with the same trace_id
            trace = await GraphElementBehavior.get_sigraph_trace_from_graph(
                graph_client=graph_client, trace_id=trace_id, unit_id=unit_id
            )
            if not trace:
                ## create a new trace node
                trace = SigraphTrace(
                    trace_id=trace_id,
                    unit_id=unit_id,
                    start_time=timestamp,
                    representative_process_name=process_name,
                    span_count=0, # initialize span_count to 0
                )
            
            ## update representative attributes to the trace node
            ## get start_time and process_name from trace node.
            ## if current nodes's start_time is earlier than trace's start_time, update it.
            if trace.start_time is not None and timestamp.timestamp() < trace.start_time.timestamp():
                # update start_time and representative_process_name
                trace.start_time = timestamp
                trace.representative_process_name = process_name

            ## update span_count
            if trace.span_count is not None:
                trace.span_count = trace.span_count + 1
            
            ## create a relationship between the trace and the syscall node later
            trace_relationship: SigraphTraceRelationship = SigraphTraceRelationship(
                trace_node=trace,
                node=current_node,
            )
            
            ## ===========================================================

            ## Parent Node Sequence =======================================
            ## create an parent process artifact
            
            parent_node: Optional[SigraphNode] = None
            relationship: Optional[SigraphRelationship] = None
            parent_trace_relationship: Optional[SigraphTraceRelationship] = None

            if parent_id is not None and parent_system_provenance is not None:
                parent_artifact: Artifact = ArtifactExtension.from_parent_action(parent_system_provenance)

                ## create parent artifact node or use existing one
                exist_parent_node: SigraphNode | None = await GraphElementBehavior.get_sigraph_node_from_graph(
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
                    
                    ## create trace relationship between parent node and trace node
                    parent_trace_relationship: SigraphTraceRelationship = SigraphTraceRelationship(
                        trace_node=trace,
                        node=parent_node,
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
            ## ===========================================================

            
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
        ## add trace & trace relationship ==========================================
        try:
            ## merge the trace node
            await graph_client.merge_node(trace.to_node(), "Trace", "trace_id")
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to merge trace into the graph: {e}",
                ("unit_id", str(unit_id), "artifact", str(actor.artifact))
            ) from e
        ## =========================================================================
        ## add node and relationship between SigraphNodes ===========================
        try:
            ## merge the current node
            await graph_client.merge_node(
                sub_node=current_node.to_node(),
                primary_label=str(current_node.artifact.artifact_type.value),
                primary_key="artifact"
                )
            
            ## merge the parent node and relationship if parent_id is provided
            if parent_node is not None:
                # If parent_id is provided, merge the parent node and create a relationship
                await graph_client.merge_node(
                    sub_node=parent_node.to_node(),
                    primary_label=str(parent_node.artifact.artifact_type.value),
                    primary_key="artifact"
                )
            if relationship is not None:
                # create the relationship between parent and current node
                await graph_client.create_relation(
                    relationship.to_relationship()
                    )
            if parent_trace_relationship is not None:
                # create the trace relationship between parent node and trace node
                await graph_client.create_relation(
                    parent_trace_relationship.to_relationship()
                )

            ## merge the trace relationship between the trace and the current node
            await graph_client.create_relation(
                trace_relationship.to_relationship()
            )
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to merge sigraph node and relationship into the graph: {e}",
                ("unit_id", str(unit_id), "artifact", str(actor.artifact))
            ) from e
        ## ==================================================================
        ## add sigma rule & sigma rule relationship ==========================
        try:
            ## create an relationship with SigmaRule if rule_ids are provided
            if related_rule_ids and len(related_rule_ids) > 0:
                for rule_id in related_rule_ids:
                    ## search for existing sigma rule node with the same rule_id
                    sigma_rule: SigraphSigmaRule | None = await GraphElementBehavior.get_sigraph_sigma_rule_from_graph(
                        graph_client=graph_client, rule_id=rule_id
                    )
                    ## create a new sigma rule node if not found
                    ## TODO: if sigma rule not found in the graph, skip it
                    if not sigma_rule:
                        sigma_rule = SigraphSigmaRule(
                            rule_id=rule_id,
                        )
                    ## create a relationship between the syscall node and the sigma rule node
                    sigma_rule_relationship: SigraphSigmaRuleRelationship = SigraphSigmaRuleRelationship(
                        rule_node=sigma_rule,
                        node=current_node,
                    )
                    # merge the sigma rule node and relationship into the graph
                    await graph_client.merge_node(
                        sub_node=sigma_rule.to_node(),
                        primary_label="SigmaRule",
                        primary_key="rule_id"
                    )
                    await graph_client.create_relation(
                        sigma_rule_relationship.to_relationship()
                    )

        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to merge rule and relationship into the graph: {e}",
                ("unit_id", str(unit_id), "artifact", str(actor.artifact))
            ) from e
        ## ==================================================================

    @staticmethod
    async def clean_debris(
                     graph_client: GraphClient,
                     unit_id: UUID):
        """_summary_
        Cleans up any orphaned or inconsistent data in the Neo4j database.
        """
        query = FLUSH_SINGLE_ENTITIES_WITH_TRACE()
        if not graph_client:
            raise InvalidInputException("Graph cannot be None", ("graph", type(graph_client).__name__))
        if not unit_id:
            raise InvalidInputException("Unit ID cannot be empty", ("unit_id", type(unit_id).__name__))
        try:
            ## run task with transaction
            ## because this task is deleting nodes, we need to use a transaction
            cursor = await graph_client.run(
                cypher=query,
                unit_id=str(unit_id)
            )
            # return the result
            if not cursor or len(cursor) == 0:
                return {
                    "nodes_deleted": 0,
                    "relationships_deleted": 0
                }
            stats = cursor[0] or {}
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
    async def get_related_trace_ids(
        graph_client: GraphClient,
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
            # run the query
            result = await graph_client.run(
                QUERY_RELATED_TRACES(max_hop),
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

    @staticmethod
    async def get_all_trace_ids_by_unit(
        graph_client: GraphClient,
        unit_id: UUID
    ) -> list[dict]:
        """_summary_
        Get all trace IDs for a given unit_id.
        
        Args:
            graph_client (Graph): The graph client to interact with the graph database.
            unit_id (UUID): The unique identifier for the unit.

        Returns:
            list[str]: A list of trace IDs belonging to the given unit.

        Raises:
            InvalidInputException: If the graph client or unit_id is invalid.
            GraphDBInteractionException: If there is an error interacting with the graph database.
        """
        if not graph_client:
            raise InvalidInputException("Graph cannot be None", ("graph", type(graph_client).__name__))
        if not unit_id:
            raise InvalidInputException("Unit ID cannot be empty", ("unit_id", type(unit_id).__name__))

        try:
            query = QUERY_TRACES()
            result = await graph_client.run(query, unit_id=str(unit_id))
            return [record["node"] for record in result]
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to get trace IDs for unit: {e}",
                ("unit_id", str(unit_id))
            ) from e
        
    @staticmethod
    async def get_all_provenance(
        graph_client: GraphClient,
        unit_id: UUID
    ) -> dict[str, list[dict[str, Any]]]:
        """_summary_
        Get all system provenance for a given unit_id. check schema.py for query details.

        Args:
            graph_client (Graph): The graph client to interact with the graph database.
            unit_id (UUID): The unique identifier for the unit.
        Returns:
            list[dict]: A list of system provenance records belonging to the given unit.
        """
        if not graph_client:
            raise InvalidInputException("Graph cannot be None", ("graph", type(graph_client).__name__))
        if not unit_id:
            raise InvalidInputException("Unit ID cannot be empty", ("unit_id", type(unit_id).__name__))

        try:
            query = QUERY_ALL_PROVENANCE()
            result = await graph_client.run(query, unit_id=str(unit_id))

            node_id = set()
            rel_id = set()

            nodes: list[dict[str, Any]] = []
            rels: list[dict[str, Any]] = []
            out: dict[str, list[dict[str, Any]]] = {"nodes": nodes, "rels": rels}
            for record in result:
                row: dict[str, Any] = {}
                # convert node dict to prefab format
                record_provenance = record["provenance"] if "provenance" in record else None
                if record_provenance is not None:
                    ## get nlst from record_provenance
                    nlst = record_provenance.get("nlst", [])
                    prefab_node = to_prefab(nlst)
                    ## get rlst from record_provenance
                    rlst = record_provenance.get("rlst", [])
                    prefab_rel = to_prefab(rlst)
                    ## append to nodes and rels
                    for n in prefab_node:
                        nid = n.get("elementId")
                        if nid is not None and nid not in node_id:
                            node_id.add(nid)
                            nodes.append(n)
                    for r in prefab_rel:
                        rid = r.get("elementId")
                        if rid is not None and rid not in rel_id:
                            rel_id.add(rid)
                            rels.append(r)
                    ## set to out
                    out["nodes"] = nodes
                    out["rels"] = rels
            return out
        except Exception as e:
            raise GraphDBInteractionException(
                f"Failed to get system provenance for unit: {e}",
                ("unit_id", str(unit_id))
            ) from e
"""_summary
This module defines the schema for graph elements in the Neo4j database.
It includes constraints for labels and query templates used in graph operations.
"""

from typing import LiteralString, cast
from graph.provenance.type import ArtifactType

# constraints for graph element labels

CONSTRAINTS = {
    ## Artifact constraints.
    ## Ensures that the 'artifact' property is unique for each ArtifactType label.
    ## Artifact types include FILE, REGISTRY, NETWORK, PROCESS, MODULE.
    ## check provenance/type.py for ArtifactType enum definition
    "Artifact": "CREATE CONSTRAINT IF NOT EXISTS FOR (n:{{$ArtifactType}}) REQUIRE n.artifact IS UNIQUE",
    ## Trace constraints.
    ## Ensures that the 'trace_id' property is unique for Trace nodes.
    ## check graph_element/element.py for Trace node definition
    "Trace": "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Trace) REQUIRE n.trace_id IS UNIQUE",
}

def QUERY_ARTIFACT(artifact_type: ArtifactType) -> LiteralString:
    """
    Generates a Cypher query to retrieve an artifact node based on its type and artifact property.
    
    Parameters:
        - artifact : The value of the artifact property to search for.

    Returns:
        node : The matching artifact node.
    """
    return cast(LiteralString, f"""\
    MATCH (n:{artifact_type.value})
    WHERE n.artifact = $artifact
    RETURN n as node
    """)

def QUERY_TRACE_WITH_TRACE_ID() -> LiteralString:
    """
    Generates a Cypher query to retrieve trace nodes based on trace_id.

    Parameters:
        - trace_id : The trace ID to search for.
        - unit_id : The unit ID to which the trace belongs.

    Returns:
        node : The matching trace node.
    """
    return """\
    MATCH (n:Trace)
    WHERE n.trace_id = $trace_id AND n.unit_id = $unit_id
    RETURN n as node
    """

def QUERY_TRACES() -> LiteralString:
    """
    Generates a Cypher query to retrieve all trace nodes for a given unit_id.

    Parameters:
        - unit_id : The unit ID to search for.

    Returns:
        node : The matching trace nodes.
    """
    return """\
    MATCH (n:Trace)
    WHERE n.unit_id = $unit_id
    RETURN n AS node
    """

def QUERY_RULE() -> LiteralString:
    """
    Generates a Cypher query to retrieve rule nodes based on rule_id.

    Parameters:
        - rule_id : The rule ID to search for.

    Returns:
        node : The matching rule node.
    """
    return """\
    MATCH (n:Rule)
    WHERE n.rule_id = $rule_id
    RETURN n as node
    """

def QUERY_RELATED_TRACES(max_hop: int) -> LiteralString:
    """
    Generates a Cypher query to retrieve related trace nodes within a specified hop distance.

    Parameters:
        - unit_id : The unit ID to which the traces belong.
        - trace_id : The trace ID to start the search from.

    Returns:
        t1, t2 : The related trace nodes.
    """
    # check that max_hop is greater than 1
    if max_hop < 1:
        raise ValueError("max_hop must be greater than 0")
    return cast(LiteralString, f"""\
    MATCH (t1:Trace {{trace_id: $traceId, unit_id: $unitId}})
    MATCH p = (t1)-[*1..{max_hop}]-(t2:Trace {{unit_id: $unitId}})
    WITH t1, t2, p
    WHERE elementId(t1) < elementId(t2)
    RETURN t1, t2
    ORDER BY length(p) ASC
    """)

def FLUSH_SINGLE_ENTITIES_WITH_TRACE() -> LiteralString:
    """
    Generates a Cypher query to flush orphaned or inconsistent data in the Neo4j database.

    Parameters:
        - unit_id : The unit ID to clean up.
    """
    return """\
    MATCH (t:Trace)-[:CONTAINS]->(n)
    WHERE t.unit_id = $unit_id
      AND COUNT{ (t)-[:CONTAINS]->() } = 1
      AND COUNT{ (n)--() } = 1
    DETACH DELETE t, n
    """

def QUERY_ALL_PROVENANCE() -> LiteralString:
    """
    Generates a Cypher query to retrieve all provenance data including artifacts, traces, and their relationships.
    Provenance refers to how a process references an asset and makes modifications to the system.

    Returns:
        nodes and relationships representing the system provenance
    """
    return """\
    MATCH (t:Trace {unit_id:$unit_id})-[:CONTAINS*1..]->(src)
    MATCH p = (src)-[*1..5]->(dst)
    WHERE (NOT 'PROCESS' IN labels(dst) OR NOT 'PROCESS' IN labels(src))
        AND NOT (src:MODULE)
        AND EXISTS((t)-[:CONTAINS*1..]->(dst))
    WITH nodes(p) AS ns, relationships(p) AS rs
    RETURN {
    nlst: [n IN ns | {elementId: elementId(n), labels: labels(n), properties: properties(n)}],
    rlst:  [r IN rs | {
        elementId: elementId(r),
        startNodeElementId: elementId(startNode(r)),
        endNodeElementId: elementId(endNode(r)),
        type: type(r),
        properties: properties(r)
        }]
    } AS provenance;
    """
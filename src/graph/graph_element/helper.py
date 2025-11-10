"""_summary_
This module provides helper functions for graph elements in the Neo4j database.
"""

from neo4j.graph import Node, Relationship
from neo4j.time import Date, Time, DateTime, Duration
from typing import Any, Dict
from fastapi.encoders import jsonable_encoder

def _int_from_element_id(eid: str) -> int | None:
    try:
        # 예: "4:...:553" -> 553
        return int(eid.rsplit(":", 1)[1])
    except Exception:
        return None

def _serialize_node(n: Node) -> Dict[str, Any]:
    eid = n.element_id
    return {
        "elementId": eid,
        "identity": _int_from_element_id(eid),
        "labels": list(n.labels),
        "properties": dict(n),
    }

def _serialize_rel(r: Relationship) -> Dict[str, Any]:
    eid = r.element_id
    s_eid = r.start_node.element_id if r.start_node else None
    e_eid = r.end_node.element_id if r.end_node else None
    if s_eid is None or e_eid is None:
        raise ValueError("Relationship start or end node is missing element_id")
    return {
        "identity": _int_from_element_id(eid),
        "start": _int_from_element_id(s_eid),
        "end": _int_from_element_id(e_eid),
        "type": r.type,
        "properties": dict(r),
        "elementId": eid,
        "startNodeElementId": s_eid,
        "endNodeElementId": e_eid,
    }

def to_prefab(v: Any) -> Any:
    if isinstance(v, Node):
        return _serialize_node(v)
    if isinstance(v, Relationship):
        return _serialize_rel(v)
    if isinstance(v, list):
        return [to_prefab(x) for x in v]
    if isinstance(v, dict):
        return {k: to_prefab(v[k]) for k in v}
    return v


temporal_encoder = {
    DateTime: lambda v: v.to_native().isoformat(),
    Date:     lambda v: v.to_native().isoformat(),
    Time:     lambda v: v.to_native().isoformat(),
    Duration: str,  # ISO8601 필요하면 직접 포맷팅
}
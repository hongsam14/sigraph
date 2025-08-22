"""_summary_
This module defines the Structured Output Format for the AI agent's responses.
"""

from typing import List
from pydantic import BaseModel, Field

######################################################################
# Question Prompt Schema
######################################################################

class EntitiesFromQuestion(BaseModel):
    """Entities extracted from the question."""
    entities: List[str] = Field(
        default_factory=list,
        description="List of entities extracted from the question."
    )

######################################################################
#  Stage 1 - Extracting Event Schema (DEPRECATED)
######################################################################

# class SourceSpan(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     start: int = Field(default=0, ge=0)
#     end: int = Field(default=0, ge=0)

# class Actors(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     process: List[str] = Field(default_factory=list, description="Actor processes (e.g., ['cmd.exe']).")
#     user: List[str] = Field(default_factory=list, description="User principal(s) if present.")

# class Objects(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     file: List[str] = Field(default_factory=list)
#     registry: List[str] = Field(default_factory=list)
#     network: List[str] = Field(default_factory=list, description="Domains, IPs, endpoints, etc.")
#     process: List[str] = Field(default_factory=list, description="Target processes (e.g., for inject).")

# class Extras(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     command_line: Optional[str] = None
#     technique: List[str] = Field(default_factory=list, description="MITRE ATT&CK technique IDs (e.g., T1059.001).")
#     timestamp: Optional[str] = Field(default=None, description="ISO8601 timestamp if present.")
#     source_span: Optional[SourceSpan] = None

# ActionType = Literal["launch", "create", "delete", "modify", "exfiltrate", "inject", "connect"]

# class ExtractedEvent(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     sentence: str
#     action: ActionType
#     actors: Actors = Field(default_factory=Actors)
#     objects: Objects = Field(default_factory=Objects)
#     extras: Extras = Field(default_factory=Extras)
#     confidence: float = Field(0.0, ge=0.0, le=1.0)

# class Stage1Extraction(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     extracted_events: List[ExtractedEvent] = Field(
#         default_factory=list, min_length=0, description="List of extracted, normalized events."
#     )


######################################################################
#  Stage 2 - Standardized Malware Report Schema (DEPRECATED)
######################################################################

# class Metadata(BaseModel):
#     report_title: str
#     date: str
#     source: str
#     malware_names: List[str]
#     campaign_or_group: List[str]


# class Summary(BaseModel):
#     executive_summary: str
#     key_findings: List[str]


# class ExecutionFlow(BaseModel):
#     process_chain: List[str] = Field(
#         description="Directional process chains (e.g., 'explorer.exe launch powershell.exe'). \
#             The basic format refers to 'Term Unification Rules' and forms [Entity] [Relationship] [Entity]"
#     )


# class Artifacts(BaseModel):
#     files: List[str]
#     registry: List[str]
#     services_or_drivers: List[str]
#     mutexes_or_pipes: List[str]


# class NetworkActivity(BaseModel):
#     domains: List[str]
#     ips: List[str]
#     ports: List[int]
#     protocols: List[str]


# class TechnicalDetails(BaseModel):
#     infection_vector: List[str]
#     persistence_mechanisms: List[str]
#     execution_flow: ExecutionFlow
#     artifacts: Artifacts
#     network_activity: NetworkActivity
#     anti_analysis: List[str]


# class MitreAttack(BaseModel):
#     tactics: List[str] = Field(
#         description="MITRE ATT&CK tactic IDs, e.g. TA0001"
#     )
#     techniques: List[str] = Field(
#         description="MITRE ATT&CK technique IDs, e.g. T1059.001"
#     )


# class Hashes(BaseModel):
#     md5: List[str]
#     sha1: List[str]
#     sha256: List[str]


# class IOCs(BaseModel):
#     hashes: Hashes
#     domains: List[str]
#     ips: List[str]
#     registry_keys: List[str]
#     file_paths: List[str]
#     github_repositories: List[str]


# class DetectionRules(BaseModel):
#     yara: List[str]
#     sigma: List[str]
#     snort_suricata: List[str]


# class DetectionAndMitigation(BaseModel):
#     detection_rules: DetectionRules
#     mitigations: List[str]


# class StandardizedMalwareReport(BaseModel):
#     metadata: Metadata
#     summary: Summary
#     technical_details: TechnicalDetails
#     mitre_attack: MitreAttack
#     iocs: IOCs
#     detection_and_mitigation: DetectionAndMitigation
#     references: List[str]
    
#####################################################
# Graph Cypher Output Schema (DEPRECATED)
#####################################################

# ## arrow, seperators
# _ARROW_PAT = re.compile(r"\s*(->|→|=>|-\>)\s*", re.IGNORECASE)

# ## node parsing
# # e.g. "Process(powershell.exe)"
# _NODE_FUNC_PAT = re.compile(r"^\s*([A-Za-z]+)\s*\(\s*([^)]+)\s*\)\s*$")
# # e.g. "Process:powershell.exe", "File:hello.ps1"
# _NODE_COLON_PAT = re.compile(r"^\s*([A-Za-z]+)\s*:\s*([^\s]+)\s*$")

# ## verify node token
# _EDGE_CANONICAL_PAT = re.compile(r"^[a-z0-9._\\/\- ]+\s->\s[a-z0-9._\\/\- ]+$", re.IGNORECASE)

# def _normalize_node_token(token: str) -> str:
#     """normalize node token to lower case and remove quotes"""
#     s = token.strip().strip("'").strip('"')
#     m = _NODE_FUNC_PAT.match(s) or _NODE_COLON_PAT.match(s)
#     if m:
#         # label = m.group(1)  # use label as is
#         value = m.group(2)
#         s = value
#     s = s.strip().lower()
#     return s

# def _ensure_exe(name: str) -> str:
#     """ensure the name ends with .exe"""
#     return name if name.endswith(".exe") else name

# def _normalize_edge(edge: str) -> str:
#     """normalize edge string by removing spaces and converting to lower case"""
#     s = edge.strip().strip('"').strip("'")
#     parts = _ARROW_PAT.split(s)
#     # _ARROW_PAT.split(s) returns left, arrow, right
#     if len(parts) == 3:
#         left, _, right = parts
#     else:
#         raise ValueError(f"process_chain should be in the form 'left -> right', but got: {s}")
#     left = _ensure_exe(_normalize_node_token(left))
#     right = _ensure_exe(_normalize_node_token(right))
#     if not left or not right:
#         raise ValueError(f"process_chain should not contain empty nodes, but got: {s}")
#     return f"{left} -> {right}"


# class QuerySummary(BaseModel):
#     """Summary of the query pattern used to match malware graphs."""
#     model_config = ConfigDict(extra="forbid")
#     normalized_pattern: List[str] = Field(
#         ..., min_length=1, description="Normalized graph patterns derived from the input actions."
#     )


# class Evidence(BaseModel):
#     """Evidence of a malware graph match."""
#     model_config = ConfigDict(extra="forbid")
#     process_chain: List[str] = Field(
#         default_factory=list,
#         description='Only contains Process edges like "a.exe -> b.exe"')
#     file_ops: List[str] = Field(
#         default_factory=list,
#         description='File operations like "creates file.txt, deletes file.txt"')
#     timestamps: List[str] = Field(default_factory=list)

#     @field_validator('process_chain', mode='before')
#     @classmethod
#     def _normalize_process_chain(cls, v: List[str]) -> List[str]:
#         """Normalize process chain strings to a consistent format."""
#         if not v:
#             return []
#         if not isinstance(v, list):
#             raise ValueError("process_chain should be a list of strings")
#         norm: list[str] = []
#         for item in v:
#             if not isinstance(item, str):
#                 raise ValueError(f"process_chain item should be a string, but got: {item}")
#             norm.append(_normalize_edge(item))
#         return norm

#     @field_validator('process_chain', mode='after')
#     @classmethod
#     def _validate_process_chain(cls, v: List[str]) -> List[str]:
#         """Ensure all process chain items are valid."""
#         for item in v:
#             if not _EDGE_CANONICAL_PAT.match(item):
#                 raise ValueError(f"Invalid process chain format: {item}")
#         return v


# class ExampleSubgraph(BaseModel):
#     """Example subgraph illustrating the malware graph match."""
#     model_config = ConfigDict(extra="forbid")
#     nodes: List[str] = Field(default_factory=list)
#     relationships: List[str] = Field(default_factory=list)

# class Candidate(BaseModel):
#     """Represents a candidate match for a malware graph."""
#     model_config = ConfigDict(extra="forbid")
#     score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0..1)")
#     techniques: List[str] = Field(default_factory=list, description="ATT&CK technique IDs")
#     evidence: Evidence
#     example_subgraph: ExampleSubgraph
#     confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence (0..1)")

# class MalwareGraphMatchResponse(BaseModel):
#     """Response model for malware graph match queries."""
#     model_config = ConfigDict(extra="forbid")
#     # query_summary: QuerySummary
#     candidates: List[Candidate] = Field(default_factory=list)
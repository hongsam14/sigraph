"""_summary
This module defines Artifact in the provenance system.
"""

import provenance.type as provenance_type
from pydantic import BaseModel

class Artifact:
    name: str
    artifact_type: provenance_type.ArtifactType
    action_type: provenance_type.ActionType
    actor_type: provenance_type.ActorType

    def __init__(self,
                 name: str,
                 artifact_type: provenance_type.ArtifactType,
                 action_type: provenance_type.ActionType,
                 actor_type: provenance_type.ActorType):
        self.name = name
        self.artifact_type = artifact_type
        self.action_type = action_type
        self.actor_type = actor_type
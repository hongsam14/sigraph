"""_summary_
This module defines extensions for the Artifact class in the provenance system.
"""

import provenance.artifact
import provenance.type as provenance_type
import provenance.type_extension
import provenance.exceptions

class ArtifactExtension:
    """_summary_
    This class provides extensions for the Artifact class in the provenance system.
    It includes methods to create an Artifact instance from a dictionary.
    """

    @staticmethod
    def from_provenance_formatted_string(data: str) -> provenance.artifact.Artifact:
        """_summary_
        Create an Artifact instance from a formatted string.

        Args:
            data (str): The formatted string containing artifact data.
            The string format is right below:
            [artifact_name]@[artifact_type]@[action_type]@[actor_type]

        Returns:
            provenance.artifact.Artifact: An instance of Artifact.

        Raises:
            ValueError: If the data is empty or not in the expected format.
        """
        ## first, check if the data is empty.
        if not data:
            raise provenance.exceptions.InvalidInputException("Data cannot be empty", ("data", type(data).__name__))
        ## split the data by '@'
        tokens: list[str] = data.split("@")
        if len(tokens) < 4:
            raise provenance.exceptions.InvalidInputException("Data is not in the expected format", ("data", "[artifact_name]@[artifact_type]@[action_type]@[actor_type]"))
        ## only get last 3 tokens. because the artifact name can contain '@' in it.
        artifact_name: str = "@".join(tokens[0:-3])
        tokens: list[str] = tokens[-3:]
        ## check if the tokens are valid.
        if not all(tokens):
            raise provenance.exceptions.InvalidInputException("Data contains empty tokens", ("data", "[artifact_name]@[artifact_type]@[action_type]@[actor_type]"))
        try:
            artifact_type: provenance_type.ArtifactType = provenance.type_extension.TypeExtension.from_string_to_artifact_type(tokens[0])
            action_type: provenance_type.ActionType = provenance.type_extension.TypeExtension.from_string_to_action_type(tokens[1])
            actor_type: provenance_type.ActorType = provenance.type_extension.TypeExtension.from_string_to_actor_type(tokens[2])
        except ValueError as e:
            raise provenance.exceptions.InvalidInputException(f"Error: Data is not in the expected format while parsing artifact: {e}", ("data", "[artifact_name]@[artifact_type]@[action_type]@[actor_type]"))
        ## create an Artifact instance.
        return provenance.artifact.Artifact(
            name=artifact_name,
            artifact_type=artifact_type,
            action_type=action_type,
            actor_type=actor_type
        )
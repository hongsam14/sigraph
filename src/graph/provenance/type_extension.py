"""_summary_
This module is extensions for types used in the provenance system.
"""

import graph.provenance.type as provenance_type
import graph.provenance.exceptions as provenance_exceptions
from graph.provenance.type import SystemProvenance, Artifact, Actor

class TypeExtension:
    """_summary_
    This class provides extensions for types used in the provenance system.
    It includes methods to create an ActionType from a string.
    """

    @staticmethod
    def from_string_to_artifact_type(data: str) -> provenance_type.ArtifactType:
        """_summary_
        Create an ArtifactType from a string.

        Args:
            data (str): The string to convert.

        Returns:
            provenance.type.ArtifactType: The corresponding ArtifactType enum.

        Raises:
            ValueError: If the data is empty. or if the data is not a valid ArtifactType.
        """
        if not data:
            raise provenance_exceptions.InvalidInputException("Data cannot be empty", ("data", type(data).__name__))
        try:
            return provenance_type.ArtifactType(data)
        except ValueError as ve:
            raise provenance_exceptions.InvalidInputException(f"{data} is not a valid ArtifactType", ("ArtifactType", str(ve)))

    @staticmethod
    def from_string_to_action_type(data: str) -> provenance_type.ActionType:
        """_summary_
        Create an ActionType from a string.

        Args:
            data (str): The string to convert.

        Returns:
            provenance.type.ActionType: The corresponding ActionType enum.

        Raises:
            ValueError: If the data is empty. or if the data is not a valid ActionType.
        """
        if not data:
            raise provenance_exceptions.InvalidInputException("Data cannot be empty", ("data", type(data).__name__))
        try:
            return provenance_type.ActionType(data)
        except ValueError as ve:
            raise provenance_exceptions.InvalidInputException(f"{data} is not a valid ActionType", ("ActionType", str(ve)))

    @staticmethod
    def from_string_to_actor_type(data: str) -> provenance_type.ActorType:
        """_summary_
        Create an ActorType from a string.

        Args:
            data (str): The string to convert.

        Returns:
            provenance.type.ActorType: The corresponding ActorType enum.

        Raises:
            ValueError: If the data is empty. or if the data is not a valid ActorType.
        """
        if not data:
            raise provenance_exceptions.InvalidInputException("Data cannot be empty", ("data", type(data).__name__))
        try:
            return provenance_type.ActorType(data)
        except ValueError as ve:
            raise provenance_exceptions.InvalidInputException(f"{data} is not a valid ActorType", ("ActorType", str(ve)))


class ArtifactExtension:
    """_summary_
    This class provides extensions for the Artifact class in the provenance system.
    It includes methods to create an Artifact instance from a dictionary.
    """

    @staticmethod
    def from_systemprovenance(data: SystemProvenance) -> Artifact:
        """_summary_
        Create an Artifact instance from a formatted string.

        Args:
            data (SystemProvenance): The formatted string containing artifact data.
            The string format is right below:
            [artifact_name]@[artifact_type]

        Returns:
            provenance.artifact.Artifact: An instance of Artifact.

        Raises:
            ValueError: If the data is empty or not in the expected format.
        """
        ## first, check if the data is empty.
        if not data:
            raise provenance_exceptions.InvalidInputException("Data cannot be empty", ("data", type(data).__name__))
        ## split the data by '@'
        tokens: list[str] = data.split("@")
        ## only get last 1 token. because the artifact name can contain '@' in it.
        artifact_name: str = "@".join(tokens[0:-1])
        token: str = tokens[-1]
        ## check if the tokens are valid.
        if not token:
            raise provenance_exceptions.InvalidInputException("Data contains empty tokens", ("data", "[artifact_name]@[artifact_type]"))
        try:
            artifact_type: provenance_type.ArtifactType = TypeExtension.from_string_to_artifact_type(token)
        except ValueError as e:
            raise provenance_exceptions.InvalidInputException(f"Error: Data is not in the expected format while parsing artifact: {e}", ("data", "[artifact_name]@[artifact_type]"))
        ## create an Artifact instance.
        return provenance_type.Artifact(
            name=artifact_name,
            artifact_type=artifact_type
        )
    
    @staticmethod
    def from_parent_action(parent_action: SystemProvenance) -> Artifact:
        """_summary_
        Create an Artifact instance from a parent action.

        Args:
            parent_action (SystemProvenance): The parent action to create the Artifact from.

        Returns:
            provenance.artifact.Artifact: An instance of Artifact with the parent action's ID as the name and PROCESS as the type.

        Raises:
            ValueError: If the parent_action is empty.

        The reason why this method is only for PROCESS is that
        Actor typed artifacts do not have children.
        So we do not need to create an Actor Artifact from a parent action.
        """
        if not parent_action:
            raise provenance_exceptions.InvalidInputException("Parent action cannot be empty", ("parent_action", type(parent_action).__name__))
        if not isinstance(parent_action, SystemProvenance):
            raise provenance_exceptions.InvalidInputException("Parent action must be a SystemProvenance", ("parent_action", type(parent_action).__name__))
        tokens: list[str] = parent_action.split("@")
        action: str = "@".join(tokens[0:2])
        return ArtifactExtension.from_systemprovenance(SystemProvenance(action))


class ActorExtension:
    """_summary_
    This class provides extensions for the Actor class in the provenance system.
    It includes methods to create an Actor instance from a dictionary.
    """

    @staticmethod
    def from_systemprovenance(data: SystemProvenance) -> Actor:
        """_summary_
        Create an Actor instance from a formatted string.

        Args:
            data (SystemProvenance): The formatted string containing actor data.
            The string format is right below:
            [artifact_name]@[artifact_type]@[action_type]@[actor_type]

        Returns:
            provenance.artifact.Actor: An instance of Actor.

        Raises:
            ValueError: If the data is empty or not in the expected format.
        """
        ## first, check if the data is empty.
        if not data:
            raise provenance_exceptions.InvalidInputException("Data cannot be empty", ("data", type(data).__name__))
        ## split the data by '@'
        tokens: list[str] = data.split("@")
        if len(tokens) < 4:
            raise provenance_exceptions.InvalidInputException("Data is not in the expected format", ("data", "[artifact_name]@[artifact_type]@[action_type]@[actor_type]"))
        ## only get last 2 tokens. and use else to get the artifact.
        artifactElem: SystemProvenance = SystemProvenance("@".join(tokens[0:-2]))
        tokens = tokens[-2:]
        ## check if the tokens are valid.
        if not all(tokens):
            raise provenance_exceptions.InvalidInputException("Data contains empty tokens", ("data", "[artifact_name]@[artifact_type]@[action_type]@[actor_type]"))
        try:
            artifact: Artifact = ArtifactExtension.from_systemprovenance(artifactElem)
            action_type: provenance_type.ActionType = TypeExtension.from_string_to_action_type(tokens[0])
            actor_type: provenance_type.ActorType = TypeExtension.from_string_to_actor_type(tokens[1])
        except ValueError as e:
            raise provenance_exceptions.InvalidInputException(f"Error: Data is not in the expected format while parsing artifact: {e}", ("data", "[artifact_name]@[artifact_type]@[action_type]@[actor_type]"))
        ## create an Actor instance.
        return Actor(
            artifact=artifact,
            action_type=action_type,
            actor_type=actor_type
        )
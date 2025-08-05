"""_summary_
This module is extensions for types used in the provenance system.
"""

import provenance.type as provenance_type

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
            raise ValueError("Data cannot be empty")
        try:
            return provenance_type.ArtifactType(data)
        except ValueError:
            raise ValueError(f"{data} is not a valid ArtifactType")

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
            raise ValueError("Data cannot be empty")
        try:
            return provenance_type.ActionType(data)
        except ValueError:
            raise ValueError(f"{data} is not a valid ActionType")

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
            raise ValueError("Data cannot be empty")
        try:
            return provenance_type.ActorType(data)
        except ValueError:
            raise ValueError(f"{data} is not a valid ActorType")
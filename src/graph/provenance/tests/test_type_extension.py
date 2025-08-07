"""_summary
This module is for unit tests for the ActorExtension class in the provenance system.
"""

import unittest
from graph.provenance.type import SystemProvenance, Actor, Artifact
from graph.provenance.type_extension import ActorExtension, ArtifactExtension
from graph.provenance.exceptions import InvalidInputException

class TestFromSystemProvenanceToArtifact(unittest.TestCase):
    """Unit tests for the from_system_provenance method in ArtifactExtension."""

    def test_valid_data(self):
        """Test with valid data."""
        data: SystemProvenance = SystemProvenance("example_artifact@FILE")
        artifact: Artifact = ArtifactExtension.from_systemprovenance(data)
        self.assertEqual(artifact.name, "example_artifact")
        self.assertEqual(artifact.artifact_type.name, "FILE")

    def test_valid_data2(self):
        """Test with valid data containing '@' in the artifact name."""
        data: SystemProvenance = SystemProvenance("example@artifact@name@FILE")
        artifact: Artifact = ArtifactExtension.from_systemprovenance(data)
        self.assertEqual(artifact.name, "example@artifact@name")
        self.assertEqual(artifact.artifact_type.name, "FILE")

    def test_empty_data(self):
        """Test with empty data."""
        with self.assertRaises(InvalidInputException) as context:
            ArtifactExtension.from_systemprovenance(SystemProvenance(""))

    def test_invalid_format(self):
        """Test with invalid format."""
        with self.assertRaises(InvalidInputException) as context:
            ArtifactExtension.from_systemprovenance(SystemProvenance("invalid_format"))

    def test_missing_tokens(self):
        """Test with missing tokens."""
        with self.assertRaises(InvalidInputException) as context:
            ArtifactExtension.from_systemprovenance(SystemProvenance("invalid_format@WHOAMI"))

    def test_empty_tokens(self):
        """Test with empty tokens."""
        with self.assertRaises(InvalidInputException) as context:
            ArtifactExtension.from_systemprovenance(SystemProvenance("example_artifact@"))

    def test_invalid_artifact_type(self):
        """Test with invalid artifact type."""
        with self.assertRaises(InvalidInputException) as context:
            ArtifactExtension.from_systemprovenance(SystemProvenance("example_artifact@INVALID_ARTIFACT"))


class TestFromSystemProvenanceToActor(unittest.TestCase):
    """Unit tests for the from_system_provenance method in ActorExtension."""

    def test_valid_data(self):
        """Test with valid data."""
        data: SystemProvenance = SystemProvenance("example_artifact@FILE@CREATE@WRITE_SEND")
        actor: Actor = ActorExtension.from_systemprovenance(data)
        self.assertEqual(str(actor.artifact), "example_artifact@FILE")
        self.assertEqual(actor.action_type.name, "CREATE")
        self.assertEqual(actor.actor_type.name, "WRITE_SEND")

    def test_valid_data2(self):
        """Test with valid data containing '@' in the artifact name."""
        data: SystemProvenance = SystemProvenance("example@artifact@name@FILE@CREATE@WRITE_SEND")
        actor: Actor = ActorExtension.from_systemprovenance(data)
        self.assertEqual(str(actor.artifact), "example@artifact@name@FILE")
        self.assertEqual(actor.action_type.name, "CREATE")
        self.assertEqual(actor.actor_type.name, "WRITE_SEND")

    def test_empty_data(self):
        """Test with empty data."""
        with self.assertRaises(InvalidInputException) as context:
            ActorExtension.from_systemprovenance(SystemProvenance(""))

    def test_invalid_format(self):
        """Test with invalid format."""
        with self.assertRaises(InvalidInputException) as context:
            ActorExtension.from_systemprovenance(SystemProvenance("invalid_format"))

    def test_missing_tokens(self):
        """Test with missing tokens."""
        with self.assertRaises(InvalidInputException) as context:
            ActorExtension.from_systemprovenance(SystemProvenance("invalid_format@WHOAMI@LAUGH"))

    def test_empty_tokens(self):
        """Test with empty tokens."""
        with self.assertRaises(InvalidInputException) as context:
            ActorExtension.from_systemprovenance(SystemProvenance("example_artifact@FILE@CREATE@"))

    def test_invalid_action_type(self):
        """Test with invalid action type."""
        with self.assertRaises(InvalidInputException) as context:
            ActorExtension.from_systemprovenance(SystemProvenance("example_artifact@FILE@INVALID_ACTION@WRITE_SEND"))

    def test_invalid_artifact_type(self):
        """Test with invalid artifact type."""
        with self.assertRaises(InvalidInputException) as context:
            ActorExtension.from_systemprovenance(SystemProvenance("example_artifact@INVALID_ARTIFACT@CREATE@WRITE_SEND"))

    def test_invalid_actor_type(self):
        """Test with invalid actor type."""
        with self.assertRaises(InvalidInputException) as context:
            ActorExtension.from_systemprovenance(SystemProvenance("example_artifact@FILE@CREATE@INVALID_ACTOR"))

if __name__ == "__main__":
    # Run the tests
    unittest.main()
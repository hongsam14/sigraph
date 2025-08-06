"""_summary
This module is for unit tests for the ArtifactExtension class in the provenance system.
"""

import unittest
from provenance.artifact_extension import ArtifactExtension
from provenance.exceptions import InvalidInputException

class TestFromProvenanceFormattedString(unittest.TestCase):
    """Unit tests for the from_provenance_formatted_string method in ArtifactExtension."""

    def test_valid_data(self):
        """Test with valid data."""
        data = "example_artifact@FILE@CREATE@WRITE_SEND"
        artifact = ArtifactExtension.from_provenance_formatted_string(data)
        self.assertEqual(artifact.name, "example_artifact")
        self.assertEqual(artifact.artifact_type.name, "FILE")
        self.assertEqual(artifact.action_type.name, "CREATE")
        self.assertEqual(artifact.actor_type.name, "WRITE_SEND")

    def test_valid_data2(self):
        """Test with valid data containing '@' in the artifact name."""
        data = "example@artifact@name@FILE@CREATE@WRITE_SEND"
        artifact = ArtifactExtension.from_provenance_formatted_string(data)
        self.assertEqual(artifact.name, "example@artifact@name")
        self.assertEqual(artifact.artifact_type.name, "FILE")
        self.assertEqual(artifact.action_type.name, "CREATE")
        self.assertEqual(artifact.actor_type.name, "WRITE_SEND")

    def test_empty_data(self):
        """Test with empty data."""
        with self.assertRaises(InvalidInputException) as context:
            ArtifactExtension.from_provenance_formatted_string("")

    def test_invalid_format(self):
        """Test with invalid format."""
        with self.assertRaises(InvalidInputException) as context:
            ArtifactExtension.from_provenance_formatted_string("invalid_format")

    def test_missing_tokens(self):
        """Test with missing tokens."""
        with self.assertRaises(InvalidInputException) as context:
            ArtifactExtension.from_provenance_formatted_string("invalid_format@WHOAMI@LAUGH")

    def test_empty_tokens(self):
        """Test with empty tokens."""
        with self.assertRaises(InvalidInputException) as context:
            ArtifactExtension.from_provenance_formatted_string("example_artifact@FILE@CREATE@")

    def test_invalid_action_type(self):
        """Test with invalid action type."""
        with self.assertRaises(InvalidInputException) as context:
            ArtifactExtension.from_provenance_formatted_string("example_artifact@FILE@INVALID_ACTION@WRITE_SEND")

    def test_invalid_artifact_type(self):
        """Test with invalid artifact type."""
        with self.assertRaises(InvalidInputException) as context:
            ArtifactExtension.from_provenance_formatted_string("example_artifact@INVALID_ARTIFACT@CREATE@WRITE_SEND")

    def test_invalid_actor_type(self):
        """Test with invalid actor type."""
        with self.assertRaises(InvalidInputException) as context:
            ArtifactExtension.from_provenance_formatted_string("example_artifact@FILE@CREATE@INVALID_ACTOR")

if __name__ == "__main__":
    # Run the tests
    unittest.main()
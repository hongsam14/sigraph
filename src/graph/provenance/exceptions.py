"""_summary_
This module defines exceptions for the provenance system.
"""

class ProvenanceException(Exception):
    """Base class for all exceptions in the provenance system."""
    def __init__(self, message: str):
        super().__init__(f"there is an error in the provenance system:\n\t{message}")

class InvalidInputException(ProvenanceException):
    """Exception raised for invalid input data."""

    def __init__(self, message: str, dest: tuple[str, ...]):
        super().__init__(f"the provenance system:\n\t{message}. The input data must be {dest}")
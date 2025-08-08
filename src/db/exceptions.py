"""_summary_
This module defines custom exceptions for the database operations.
"""

class DatabaseException(Exception):
    """_summary_
    Base exception for database-related errors.
    """
    def __init__(self, message: str):
        super().__init__(f"Database error:\n\t{message}")

class DatabaseInteractionException(DatabaseException):
    """_summary_
    Exception raised for errors during database interactions.
    """
    def __init__(self, message: str, element: tuple[str, ...]):
        super().__init__(f"Database interaction error:\n\t{message}. Cause Element: {element}")

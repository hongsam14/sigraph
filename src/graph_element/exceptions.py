"""_summary_
This module defines exceptions for the generating system provenance graph.
"""

class GraphElementException(Exception):
    """_summary_
    Exception raised for errors in the graph element processing.
    """
    def __init__(self, message: str):
        super().__init__(f"Error in graph element processing:\n\t{message}")

class InvalidInputException(GraphElementException):
    """_summary_
    Exception raised for invalid input in graph element processing.
    """
    def __init__(self, message: str, element: tuple[str, ...]):
        super().__init__(f"Invalid input:\n\t{message}. Cause Element: {element}")

class InvalidElementException(GraphElementException):
    """_summary_
    Exception raised for invalid graph elements.
    """
    def __init__(self, message: str, element: tuple[str, ...]):
        super().__init__(f"Invalid graph element:\n\t{message}. Cause Element: {element}")

class GraphDBInteractionException(GraphElementException):
    """_summary_
    Exception raised for errors in graph interactions.
    """
    def __init__(self, message: str, element: tuple[str, ...]):
        super().__init__(f"Graph interaction error:\n\t{message}. Cause Element: {element}")
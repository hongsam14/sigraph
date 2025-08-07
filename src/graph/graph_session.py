"""_summary_
This module contains the GraphSession class, which manages the connection to the Neo4j graph database.
It provides methods to upsert system provenance objects and retrieve Sigraph nodes and relationships.
"""

from typing import Any
from py2neo import Graph
from graph.provenance.type import SystemProvenance
from graph.graph_model import GraphNode
from graph.graph_element.element_behavior import GraphElementBehavior

class GraphSession:
    """_summary_
    This class manages the graph connection and interactions with the Neo4j database.
    It provides methods to upsert system provenance objects and retrieve sigraph nodes and relationships.
    """
    __client: Graph
    __logger: Any

    def __init__(self, logger: Any, uri: str, user: str, password: str):
        """_summary_
        Initializes the GraphSession with a Neo4j connection.

        Args:
            loger (Logger): Logger instance for logging.
            uri (str): URI of the Neo4j database.
            user (str): Username for the Neo4j database.
            password (str): Password for the Neo4j database.
        """
        self.__logger = logger
        self.__logger.info(f"Connecting to Neo4j at {uri} with user {user}")
        try:
            self.__client = Graph(f"bolt://{uri}:7687", auth=(user, password))
        except Exception as e:
            
            self.__logger.error(f"Failed to connect to Neo4j database at {uri}. Please check your connection settings.")
            
            raise ConnectionError(
                f"Failed to connect to Neo4j database at {uri}. "
                "Please check your connection settings."
            ) from e
        

    def __del__(self):
        """_summary_
        Destructor for the GraphSession class. Closes the Neo4j connection.
        """
        self.__logger.info("Closing Neo4j connection.")
        self.__client.close()


    def upsert_system_provenance(
            self,
            node: GraphNode,
    ):
        """_summary_
        Upserts a system provenance object in the Neo4j database.

        Args:
            node (GraphNode): The graph node to upsert.

        Raises:
            InvalidInputException: If the node is invalid or missing required fields.
            GraphDBInteractionException: If there is an error interacting with the graph database.
        """
        self.__logger.info(f"Upserting system provenance for node {node.unit_id}")
        try:
            sp_value: SystemProvenance = SystemProvenance(node.system_provenance)
            # Create or update the node in the database
            GraphElementBehavior.upsert_systemprovenance(
                graph_client=self.__client,
                unit_id=node.unit_id,
                related_span_id=node.span_id,
                system_provenance=sp_value,
                parent_id=node.parent_span_id,
            )
        except Exception as e:
            self.__logger.error(f"Failed to upsert system provenance for node {node.unit_id}")
            raise e
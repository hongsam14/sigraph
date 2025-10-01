"""_summary_
This module contains the GraphSession class,
which manages the connection to the Neo4j graph database.
It provides methods to upsert system provenance objects,
and retrieve Sigraph nodes and relationships.
"""

from typing import Any, Optional
from py2neo import Graph
from uuid import UUID
from graph.provenance.type import SystemProvenance
from graph.graph_model import GraphNode
from graph.graph_element.element_behavior import GraphElementBehavior


class GraphSession:
    """_summary_
    This class manages the graph connection and interactions with the Neo4j database.
    It provides methods to upsert system provenance objects,
    and retrieve sigraph nodes and relationships.
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
            self.__logger.error(
                f"Failed to connect to Neo4j database at {uri}.\
                    Please check your connection settings."
            )

            raise ConnectionError(
                f"Failed to connect to Neo4j database at {uri}. "
                "Please check your connection settings."
            ) from e

    def __del__(self):
        """_summary_
        Destructor for the GraphSession class. Closes the Neo4j connection.
        """
        self.__logger.info("Closing Neo4j connection.")
        # self.__client.close()

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
            psp_value: Optional[SystemProvenance] = None
            if node.parent_system_provenance is not None:
                psp_value = SystemProvenance(node.parent_system_provenance)
            # Create or update the node in the database
            GraphElementBehavior.upsert_systemprovenance(
                graph_client=self.__client,
                unit_id=node.unit_id,
                trace_id=node.trace_id,
                timestamp=node.timestamp,
                weight=node.weight,
                process_name=node.process_name,
                related_span_id=node.span_id,
                system_provenance=sp_value,
                parent_id=node.parent_span_id,
                parent_system_provenance=psp_value
            )
        except Exception as e:
            self.__logger.error(
                f"Failed to upsert system provenance for node {node.unit_id} {str(e)}"
            )
            raise e
    
    def clean_debris(self,
                     unit_id: UUID,
    )->dict:
        """_summary_
        Cleans up any orphaned or inconsistent data in the Neo4j database.
        """
        self.__logger.info("Cleaning up debris in the Neo4j database.")
        try:
            result: dict = GraphElementBehavior.clean_debris(
                graph_client=self.__client,
                unit_id=unit_id
            )
            self.__logger.info(f"Cleaned debris: {result}")
            return result
        except Exception as e:
            self.__logger.error(
                f"Failed to clean debris in the Neo4j database: {str(e)}"
            )
            raise e

    def get_related_trace_ids(self,
                              unit_id: UUID,
                              trace_id: str
    ) -> list[str]:
        """_summary_
        Retrieves related trace IDs for a given unit ID and trace ID.

        Args:
            unit_id (UUID): The unit ID to query.
            trace_id (str): The trace ID to query.
        Returns:
            list[str]: A list of related trace IDs.
        Raises:
            GraphDBInteractionException: If there is an error during the retrieval operation.
        """
        self.__logger.info(f"Retrieving related trace IDs for unit_id={unit_id} and trace_id={trace_id}")
        try:
            result: list[str] = GraphElementBehavior.get_related_trace_ids(
                graph_client=self.__client,
                unit_id=unit_id,
                trace_id=trace_id
            )
            self.__logger.info(f"Found {len(result)} related trace IDs for unit_id={unit_id} and trace_id={trace_id}")
            return result
        except Exception as e:
            self.__logger.error(
                f"Failed to retrieve related trace IDs for unit_id={unit_id} and trace_id={trace_id}: {str(e)}"
            )
            raise e

    def get_trace_ids_by_unit(self, 
                              unit_id: UUID
    ) -> list[str]:
        """_summary_
        Retrieves all trace IDs for a given unit ID.

        Args:
            unit_id (UUID): The unit ID to query.

        Returns:
            list[str]: A list of trace IDs that belong to the given unit.

        Raises:
            GraphDBInteractionException: If there is an error during the retrieval operation.
        """
        try:
            return GraphElementBehavior.get_all_trace_ids_by_unit(
                graph_client=self.__client,
                unit_id=unit_id,
            )
        except Exception as e:
            self.__logger.error(f"Failed to get traces by unit_id={unit_id}: {e}")
            raise e    
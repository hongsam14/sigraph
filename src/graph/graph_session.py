"""_summary_
This module contains the GraphSession class,
which manages the connection to the Neo4j graph database.
It provides methods to upsert system provenance objects,
and retrieve Sigraph nodes and relationships.
"""
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import SecretStr
from typing import Any, Optional
from uuid import UUID
from graph.provenance.type import SystemProvenance, ArtifactType
from graph.graph_client.client import GraphClient
from graph.graph_element.element import SigraphIoC, SigraphSummary
from graph.graph_element.element_behavior import GraphElementBehavior
from graph.graph_element.helper import temporal_encoder
from graph.graph_model import GraphNode, GraphTraceNode

class GraphSession:
    """_summary_
    This class manages the graph connection and interactions with the Neo4j database.
    It provides methods to upsert system provenance objects,
    and retrieve sigraph nodes and relationships.
    """

    __client: GraphClient
    __logger: Any

    def __init__(self, logger: Any, uri: str, user: str, password: SecretStr):
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
        
        # gen primary keys dict for GraphClient
        ## from ArtifactType to "artifact"
        ## from Trace to ("unit_id", "trace_id")
        ## from Rule to "rule_id"
        primary_keys: dict[str, str | tuple[str, ...]] | None = {}
        for atype in ArtifactType:
            primary_keys[atype] = "artifact"
        primary_keys["Trace"] = ("unit_id", "trace_id")
        primary_keys["Rule"] = "rule_id"

        try:
            self.__client = GraphClient(
                uri=f"bolt://{uri}:7687",
                user=user,
                password=password,
                logger=logger,
                primary_keys=primary_keys)
            # run constraints
            GraphElementBehavior.apply_constraints(
                graph_client=self.__client,
            )
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
        try:
            self.__client.close()
        except Exception as e:
            self.__logger.error(f"Failed to close Neo4j connection: {str(e)}")
            raise e

    async def upsert_system_provenance(
        self,
        node: GraphNode):
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
            await GraphElementBehavior.upsert_systemprovenance(
                graph_client=self.__client,
                ## node
                unit_id=node.unit_id,
                trace_id=node.trace_id,
                system_provenance=sp_value,
                ## relationship attributes
                timestamp=node.timestamp,
                weight=node.weight,
                ## parent attributes
                parent_id=node.parent_span_id,
                parent_system_provenance=psp_value,
                ## node attributes
                process_name=node.process_name,
                related_span_id=node.span_id,
                related_rule_ids=node.related_rule_ids,
            )
        except Exception as e:
            self.__logger.error(
                f"Failed to upsert system provenance for node {node.unit_id} {str(e)}"
            )
            # raise e
    
    async def clean_debris(self,
                     unit_id: UUID) -> Optional[dict]:
        """_summary_
        Cleans up any orphaned or inconsistent data in the Neo4j database.
        """
        self.__logger.info("Cleaning up debris in the Neo4j database.")
        try:
            result: SigraphSummary = await GraphElementBehavior.clean_debris(
                graph_client=self.__client,
                unit_id=unit_id
            )
            self.__logger.info(f"Cleaned debris: {result}")
            return result.model_dump()
        except Exception as e:
            self.__logger.error(
                f"Failed to clean debris in the Neo4j database: {str(e)}"
            )
            # raise e
            return None

    async def get_related_trace_ids(self,
                              unit_id: UUID,
                              trace_id: str) -> Optional[list[str]]:
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
            result: list[str] = await GraphElementBehavior.get_related_trace_ids(
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
            # raise e
            return None


    async def get_trace_ids_by_unit(self, 
                              unit_id: UUID) -> Optional[list[GraphTraceNode]]:
        """_summary_
        Retrieves all trace IDs for a given unit ID.

        Args:
            unit_id (UUID): The unit ID to query.

        Returns:
            list[GraphTraceNode]: A list of trace nodes that belong to the given unit.

        Raises:
            GraphDBInteractionException: If there is an error during the retrieval operation.
        """
        try:
            out: list[dict] = await GraphElementBehavior.get_all_trace_ids_by_unit(
                graph_client=self.__client,
                unit_id=unit_id,
            )
            result: list[GraphTraceNode] = []
            for item in out:
                tid = item.get("trace_id")
                ## check for None because tid is necessary
                if tid is None:
                    continue
                t_id = str(tid)
                ## check for None because timestamp is necessary
                timestamp_str = item.get("start_time")
                if timestamp_str is None:
                    continue
                timestamp_str = str(timestamp_str)
                ### convert timestamp string to datetime object
                timestamp = datetime.fromisoformat(timestamp_str)
                ## optional fields
                image_name = item.get("representative_process_name")
                span_count = item.get("span_count")
                ## filter trace that have just one span
                if span_count is None or span_count < 2:
                    continue
                ## construct GraphTraceNode
                trace_node = GraphTraceNode(
                    trace_id=t_id,
                    timestamp=timestamp,
                    image_name=image_name,
                )
                result.append(trace_node)
            return result
        except Exception as e:
            self.__logger.error(f"Failed to get traces by unit_id={unit_id}: {e}")
            # raise e 
            return None
        
    async def get_system_provenance(self, unit_id: UUID) -> JSONResponse | None:
        """_summary_
        Renders the system provenance graph for a given unit ID.

        Args:
            unit_id (UUID): The unit ID to render the provenance graph for.

        Returns:
            list[dict]: A list of serialized graph elements representing the system provenance.

        Raises:
            GraphDBInteractionException: If there is an error during the rendering operation.

        """
        try:
            result: dict[str, list[dict[str, Any]]] = await GraphElementBehavior.get_all_provenance(
                graph_client=self.__client,
                unit_id=unit_id,
            )
            return JSONResponse(jsonable_encoder(result, custom_encoder=temporal_encoder))
        except Exception as e:
            self.__logger.error(
                f"Failed to render system provenance for unit_id={unit_id}: {str(e)}"
            )
            # raise e
            return None

    async def flush_unit_data(self, unit_id: UUID) -> Optional[dict]:
        """_summary_
        Flushes all data related to a specific unit ID from the Neo4j database.

        Args:
            unit_id (UUID): The unit ID whose data is to be flushed.

        Returns:
            dict: A dictionary containing the result of the flush operation.
        """
        self.__logger.info(f"Flushing data for unit_id={unit_id}")
        try:
            result: SigraphSummary = await GraphElementBehavior.flush_unit_data(
                graph_client=self.__client,
                unit_id=unit_id
            )
            self.__logger.info(f"Flushed data for unit_id={unit_id}: {result}")
            return result.model_dump()
        except Exception as e:
            self.__logger.error(
                f"Failed to flush data for unit_id={unit_id}: {str(e)}"
            )
            # raise e
            return None
        
    async def flush_all_debris(self) -> Optional[dict]:
        """_summary_
        Flushes all debris (orphaned or inconsistent data) from the Neo4j database for all unit IDs.
        """
        self.__logger.info("Flushing debris for all unit IDs")
        try:
            result: SigraphSummary = await GraphElementBehavior.clean_all_debris(
                graph_client=self.__client,
            )
            # iterate through each unit_id and clean debris
            self.__logger.info("Flushed debris for all unit IDs")
            return result.model_dump()
        except Exception as e:
            self.__logger.error(
                f"Failed to flush debris for all unit IDs: {str(e)}"
            )
            # raise e
            return None
        
    async def get_all_iocs(self,
                           unit_id: UUID) -> list[dict] | None:
        """_summary_
        Retrieves all Indicators of Compromise (IoCs) for a given unit ID.
        Args:
            unit_id (UUID): The unit ID to query.
        
        Returns:
            list[SigraphIoC]: A list of SigraphIoC objects representing the IoCs.
        
        Raises:
            GraphDBInteractionException: If there is an error during the retrieval operation.
        """
        self.__logger.info(f"Retrieving all IoCs for unit_id={unit_id}")
        try:
            result: list[SigraphIoC] = await GraphElementBehavior.get_all_iocs(
                graph_client=self.__client,
                unit_id=unit_id
            )
            self.__logger.info(f"Retrieved {len(result)} IoCs for unit_id={unit_id}")
            return [ioc.model_dump() for ioc in result]
        except Exception as e:
            self.__logger.error(
                f"Failed to retrieve IoCs for unit_id={unit_id}: {str(e)}"
            )
            # raise e
            return None

    
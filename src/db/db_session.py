"""_summary_
This module defines the DBSession class for interacting with OpenSearch.
DBSession is responsible for storing SysLogObject entries.
!!!NOTICE!!!
https://forum.opensearch.org/t/about-python-client-library-and-elasticsearch-dsl-support/4756/11?utm_source=chatgpt.com
to support OpenSearch, you need to use the `elasticsearch` library 7.13 or earlier.
"""

from typing import Any
from uuid import UUID
from fastapi.encoders import jsonable_encoder
from opensearchpy import OpenSearch
from db.db_model import SyslogModel, SyslogSequence, install_syslog_template_and_index
from db.exceptions import DatabaseInteractionException
import traceback


class DBSession:
    """_summary_
    DBSession is a session for interacting with opensearch for storing Syslog Objects.
    """
    __logger: Any
    __index_name: str
    __client: OpenSearch

    def __init__(self, loger: Any, uri: str, index_name: str):
        self.__index_name = index_name
        self.__logger = loger
        self.__logger.info(f"Connecting to OpenSearch at {uri}")
        try:
            self.__client = OpenSearch(
                hosts=[{"host": uri, "port": 9200}],
                http_compress=True,
                use_ssl=False,
            )
        except ConnectionError as e:
            self.__logger.error(f"Failed to connect to OpenSearch at {uri}. Please check your connection settings.")
            raise ConnectionError(
                f"Failed to connect to OpenSearch at {uri}. "
                "Please check your connection settings."
            ) from e
        try:
            # document initialization
            install_syslog_template_and_index(self.__client)
        except Exception as e:
            self.__logger.error(f"Failed to initialize SyslogDocument: {e}")
            raise DatabaseInteractionException(
                f"Failed to initialize SyslogDocument: {e}",
                (self.__index_name,)
            ) from e

    def __del__(self):
        """_summary_
        Destructor to close the connection to OpenSearch.
        """
        if self.__client:
            self.__client.transport.close()
            self.__client = None
            self.__logger.info("Closed connection to OpenSearch.")


    async def store_syslog_object(self, syslog_object: SyslogModel):
        """_summary_
        Save a SyslogObject to OpenSearch.

        Args:
            syslog_object (SyslogModel): The SyslogObject to save.

        Raises:
            DatabaseInteractionException: If there is an error during the save operation.
        """
        try:
            doc = jsonable_encoder(syslog_object)
            self.__client.index(
                index=self.__index_name,
                body=doc,
                params={"refresh": "wait_for"},  # Ensures the document is searchable immediately
            )
        except Exception as e:
            print(traceback.format_exc())
            self.__logger.error(f"Failed to save SyslogObject: {e}")
            raise DatabaseInteractionException(
                f"Failed to save SyslogObject: {e}",
                (str(syslog_object),)
            ) from e
        

    async def get_syslog_sequence_with_trace(self, unit_id: UUID, trace_id: str, label: str = "") -> SyslogSequence:
        """_summary_
        Retrieve a sequence of SyslogObjects associated with a specific trace_id and unit_id.

        Args:
            unit_id (UUID): The unit ID to filter by.
            trace_id (str): The trace ID to filter by.

        Returns:
            List[SyslogModel]: A list of SyslogObjects matching the criteria.

        Raises:
            DatabaseInteractionException: If there is an error during the retrieval operation.
        """
        try:
            query:dict = {
                "size": 100,
                "track_total_hits": True,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"unit_id": f"{unit_id}"}},
                            {"term": {"trace_id": f"{trace_id}"}}
                        ]
                    }
                },
                "sort": [
                    {"timestamp": {"order": "asc"}},
                    {"_id": {"order": "asc"}}  # tie-breaker for consistent pagination
                ]
            }
            syslog_sequence: list[dict] = []
            search_after = None

            while True:
                my_query = dict(query)  # shallow copy
                if search_after is not None:
                    my_query["search_after"] = search_after
                resp = self.__client.search(
                    index=self.__index_name,
                    body=my_query
                    )
                hits = resp.get("hits", {}).get("hits", [])
                if not hits:
                    break
                # collect all raw_data
                for h in hits:
                    src = h.get("_source", {})
                    raw = src.get("raw_data")
                    if raw is not None:
                        syslog_sequence.append(raw)

                ## get next page token
                search_after = hits[-1].get("sort")

            ## align the syslog sequence based on timestamp
            aligned_sequence: list[dict] = sorted(
                syslog_sequence,
                key=lambda x: x.get("Timestamp", "")
            )

            syslog_sequence_model = SyslogSequence(
                label=label,
                syslogs=aligned_sequence
            )

            self.__logger.info(f"Retrieved {len(aligned_sequence)} SyslogObjects for unit_id={unit_id} and trace_id={trace_id}")

            return syslog_sequence_model

        except Exception as e:
            self.__logger.error(f"Failed to retrieve SyslogObjects: {e}")
            raise DatabaseInteractionException(
                f"Failed to retrieve SyslogObjects: {e}",
                (str(unit_id), trace_id)
            ) from e

    async def get_syslog_sequences_with_lucene_query(self, unit_id: UUID, lucene_query: dict) -> list[SyslogSequence]:
        """_summary_
        Retrieve sequences of SyslogObjects based on a Lucene query.

        Args:
            lucene_query (dict): The Lucene query to filter by.

        Returns:
            List[SyslogSequence]: A list of SyslogSequences matching the criteria.

        Raises:
            DatabaseInteractionException: If there is an error during the retrieval operation.
        """
        try:
            query: dict = {
                "size": 100,
                "track_total_hits": True,
                "_source": ["trace_id"],
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"unit_id": f"{unit_id}"}},
                            lucene_query
                        ]
                    }
                },
                "sort": [
                    {"timestamp": {"order": "asc"}},
                    {"_id": {"order": "asc"}}  # tie-breaker for consistent pagination
                ]
            }
            ## get all the trace_ids first
            trace_ids: list[str] = []
            search_after = None
            while True:
                my_query = dict(query)  # shallow copy
                if search_after is not None:
                    my_query["search_after"] = search_after
                resp = self.__client.search(
                    index=self.__index_name,
                    body=my_query
                    )
                hits = resp.get("hits", {}).get("hits", [])
                if not hits:
                    break
                # collect all trace_ids
                for h in hits:
                    src = h.get("_source", {})
                    trace_id = src.get("trace_id")
                    if trace_id and trace_id not in trace_ids:
                        trace_ids.append(trace_id)

                ## get next page token
                search_after = hits[-1].get("sort")

            self.__logger.info(f"Found {len(trace_ids)} unique trace_ids for unit_id={unit_id} with the given Lucene query.")

            ## then get the sequences for each trace_id
            result: list[SyslogSequence] = list[SyslogSequence]()
            for sequence in trace_ids:
                syslog_sequence: SyslogSequence = await self.get_syslog_sequence_with_trace(unit_id=unit_id, trace_id=sequence)
                if syslog_sequence:
                    result.append(syslog_sequence)
            return result

        except Exception as e:
            self.__logger.error(f"Failed to retrieve SyslogSequences: {e}")
            raise DatabaseInteractionException(
                f"Failed to retrieve SyslogSequences: {e}",
                (str(lucene_query),)
            ) from e
    

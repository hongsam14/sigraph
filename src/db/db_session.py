"""_summary_
This module defines the DBSession class for interacting with OpenSearch.
DBSession is responsible for storing SysLogObject entries.
!!!NOTICE!!!
https://forum.opensearch.org/t/about-python-client-library-and-elasticsearch-dsl-support/4756/11?utm_source=chatgpt.com
to support OpenSearch, you need to use the `elasticsearch` library 7.13 or earlier.
"""

from typing import Any
from uuid import UUID
from opensearchpy import OpenSearch
from opensearchpy.helpers import streaming_bulk
from db.db_model import SyslogModel, SyslogSequence, install_syslog_template_and_index
from db.exceptions import DatabaseInteractionException


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
                http_compress=False,
                use_ssl=False,
                timeout=60,
                max_retries=3,
                retry_on_timeout=True,
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

    def __actions(self, docs:list[SyslogModel]):
        for d in docs:
            yield {"_op_type":"index","_index":self.__index_name,"_source":d.model_dump()}

    def __count_clauses(self, query: dict|list)->int:
        """_summary_
        Count the number of clauses in an input query represented as a dictionary.
        """
        clause_count = 0
        def count_recursive(element):
            nonlocal clause_count
            if isinstance(element, dict):
                for key, value in element.items():
                    if key.lower() in ('must', 'should', 'must_not', 'filter'):
                        clause_count += len(value) if isinstance(value, list) else 1
                    count_recursive(value)
            elif isinstance(element, list):
                for item in element:
                    count_recursive(item)
        count_recursive(query)
        return clause_count

    def __split_query(self, query: dict|list, max_clauses: int)->list[dict]:
        """Split the input query into multiple smaller queries if it exceeds the max_clauses."""
        clauses: list[dict] = []
        def extract_clauses(element):
            if isinstance(element, dict):
                for key, value in element.items():
                    if key.lower() in ('must', 'should', 'must_not', 'filter'):
                        if isinstance(value, list):
                            clauses.extend(value)
                        else:
                            clauses.append(value)
                    extract_clauses(value)
            elif isinstance(element, list):
                for item in element:
                    extract_clauses(item)
        # Extract all clauses from the original query
        extract_clauses(query)
        # Split clauses into smaller chunks
        split_queries: list[dict] = []
        for i in range(0, len(clauses), max_clauses):
            chunk: list[dict] = clauses[i:i + max_clauses]
            split_queries.append({
                "query": {
                    "bool": {
                        "should": chunk  # Change this as needed (e.g., "must" or "filter")
                    }
                }
            })
        return split_queries

    def __process_query(self, query: dict|list, max_clauses: int=1024)->list[dict]:
        clause_count = self.__count_clauses(query)
        if clause_count >= max_clauses:
            split_queries = self.__split_query(query=query, max_clauses=max_clauses)
            return split_queries
        else:
            # Process the query here as needed
            if isinstance(query, dict):
                return [query]
            return query


    async def store_syslog_object(self, syslog_bulk: list[SyslogModel]):
        """_summary_
        Save a SyslogObject to OpenSearch.

        Args:
            syslog_object (SyslogModel): The SyslogObject to save.

        Raises:
            DatabaseInteractionException: If there is an error during the save operation.
        """
        try:
            for ok, info in streaming_bulk(
                client=self.__client,
                actions=self.__actions(syslog_bulk),
                chunk_size=500,
                max_retries=3,
                raise_on_error=False,
                request_timeout=60
            ):
                pass
        except Exception as e:
            self.__logger.error(f"Failed to save SyslogObject: {e}")
            raise DatabaseInteractionException(
                f"Failed to save SyslogObject: {e}",
                (str(),)
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
        

    async def get_syslog_by_subquery(self, unit_id: UUID, category: str, query: dict|list) -> SyslogSequence:
        """_summary_
        Retrieve a sequence of SyslogObjects associated with a specific trace_id and unit_id.

        Args:
            unit_id (UUID): The unit ID to filter by.

        Returns:
            List[SyslogModel]: A list of SyslogObjects matching the criteria.

        Raises:
            DatabaseInteractionException: If there is an error during the retrieval operation.
        """

        ## check null
        if not query:
            raise ValueError("Input query is empty or None.")
        if unit_id is None:
            raise ValueError("Input unit_id is None.")
        if not category:
            raise ValueError("Input category is empty or None.")
        try:
            query_template:dict = {
                "size": 100,
                "track_total_hits": True,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"unit_id": f"{unit_id}"}},
                            {"term": {"raw_data.EventName": f"{category}"}},
                        ]
                    }
                },
                "sort": [
                    {"timestamp": {"order": "asc"}},
                    {"_id": {"order": "asc"}}  # tie-breaker for consistent pagination
                ],
            }
            syslog_sequence: list[dict] = []
            search_after = None

            # split query
            processed_query = self.__process_query(query=query, max_clauses=1024)

            for q in processed_query:
                while True:
                    my_query = dict(query_template)  # shallow copy
                    
                    ## check validity of my_query and q
                    if my_query.get("query") is None or my_query["query"].get("bool") is None:
                        raise ValueError("Invalid query template structure")
                    if not isinstance(my_query["query"]["bool"], dict):
                        raise ValueError("Invalid query template structure: 'bool' should be a dictionary")
                    if q.get("query") is None or q["query"].get("bool") is None:
                        raise ValueError("Invalid subquery structure")
                    if not isinstance(q["query"]["bool"], dict):
                        raise ValueError("Invalid subquery structure: 'bool' should be a dictionary")
                    
                    # merge q into my_query
                    ## merge the must clauses with existing must clauses
                    my_query["query"]["bool"]["must"].extend(q["query"]["bool"].get("must", []))
                    ## append other clauses
                    for key, values in q["query"]["bool"].items():
                        if key not in ("must",):
                            if key not in my_query["query"]["bool"]:
                                my_query["query"]["bool"][key] = values
                            else:
                                if isinstance(values, list):
                                    my_query["query"]["bool"][key].extend(values)
                                else:
                                    # if it's not a list, convert to list and append
                                    my_query["query"]["bool"][key] = [values]
                                    my_query["query"]["bool"][key].extend(values)
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
                label="",
                syslogs=aligned_sequence
            )

            self.__logger.info(f"Retrieved {len(aligned_sequence)} SyslogObjects for unit_id={unit_id}, with subqueries {query}.")

            return syslog_sequence_model

        except Exception as e:
            self.__logger.error(f"Failed to retrieve SyslogObjects: {e}")
            raise DatabaseInteractionException(
                f"Failed to retrieve SyslogObjects: {e}",
                (str(unit_id),)
            ) from e


    async def get_trace_ids_with_lucene_query(self, unit_id: UUID, lucene_query: dict) -> list[str]:
        """_summary_
        Retrieve trace IDs based on a Lucene query.

        Args:
            lucene_query (dict): The Lucene query to filter by.

        Returns:
            List[str]: A list of trace IDs matching the criteria.

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

            return trace_ids

        except Exception as e:
            self.__logger.error(f"Failed to retrieve trace IDs: {e}")
            raise DatabaseInteractionException(
                f"Failed to retrieve trace IDs: {e}",
                (str(lucene_query),)
            ) from e

    async def label_syslog_sequences_with_lucene_query(self, unit_id: UUID, input_label: str, lucene_query: dict) -> list[SyslogSequence]:
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
            ## first get all the trace_ids matching the lucene query
            trace_ids: list[str] = await self.get_trace_ids_with_lucene_query(unit_id=unit_id,
                                                                            lucene_query=lucene_query)
            ## then get the sequences for each trace_id
            result: list[SyslogSequence] = []
            for sequence in trace_ids:
                syslog_sequence: SyslogSequence = await self.get_syslog_sequence_with_trace(unit_id=unit_id,
                                                                                            trace_id=sequence,
                                                                                            label=input_label)
                if syslog_sequence:
                    result.append(syslog_sequence)
            return result

        except Exception as e:
            self.__logger.error(f"Failed to retrieve SyslogSequences: {e}")
            raise DatabaseInteractionException(
                f"Failed to retrieve SyslogSequences: {e}",
                (str(lucene_query),)
            ) from e

    async def flush_unit_syslogs(self, unit_id: UUID)->int:
        """_summary_
        Delete SyslogObjects associated with a specific unit_id.

        Args:
            unit_id (UUID): The unit ID to filter by.

        Raises:
            DatabaseInteractionException: If there is an error during the deletion operation.
        """
        try:
            query: dict = {
                "query": {
                    "term": {
                        "unit_id": f"{unit_id}"
                    }
                }
            }
            response = self.__client.delete_by_query(
                index=self.__index_name,
                body=query,
                refresh=True,
                wait_for_completion=True,
                conflicts="proceed"
            )
            deleted = response.get("deleted", 0)
            self.__logger.info(f"Deleted {deleted} SyslogObjects for unit_id={unit_id}.")
            return deleted
        except Exception as e:
            self.__logger.error(f"Failed to delete SyslogObjects: {e}")
            raise DatabaseInteractionException(
                f"Failed to delete SyslogObjects: {e}",
                (str(unit_id),)
            ) from e
        

"""_summary_
This module defines the DBSession class for interacting with OpenSearch to store SysLogObject entries.
!!!NOTICE!!!
https://forum.opensearch.org/t/about-python-client-library-and-elasticsearch-dsl-support/4756/11?utm_source=chatgpt.com
to support OpenSearch, you need to use the `elasticsearch` library 7.13 or earlier.
"""

from typing import Any
from elasticsearch_dsl import connections
from db.db_model import SyslogModel, SyslogDocument
from db.exceptions import DatabaseInteractionException


class DBSession:
    """_summary_
    DBSession is a session for interacting with opensearch for storing Syslog Objects.
    """
    __syslog_doc: SyslogDocument
    __logger: Any
    __index_name: str

    def __init__(self, loger: Any, uri: str, index_name: str):
        self.__index_name = index_name
        self.__syslog_doc = SyslogDocument()
        self.__logger = loger
        self.__logger.info(f"Connecting to OpenSearch at {uri}")

        try:
            connections.create_connection(alias='default', hosts=[f"http://{uri}:9200"])
        except ConnectionError as e:
            self.__logger.error(f"Failed to connect to OpenSearch at {uri}. Please check your connection settings.")
            raise ConnectionError(
                f"Failed to connect to OpenSearch at {uri}. "
                "Please check your connection settings."
            ) from e
        try:
            # document initialization
            self.__syslog_doc.init()
        except Exception as e:
            self.__logger.error(f"Failed to initialize SyslogDocument: {e}")
            raise DatabaseInteractionException(f"Failed to initialize SyslogDocument: {e}", (self.__syslog_doc,))

    
    def __del__(self):
        """_summary_
        Destructor to close the connection to OpenSearch.
        """
        connections.remove_connection(alias='default')
        self.__logger.info("Closed connection to OpenSearch.")


    def store_syslog_object(self, syslog_object: SyslogModel):
        """_summary_
        Save a SyslogObject to OpenSearch.

        Args:
            syslog_object (SyslogModel): The SyslogObject to save.

        Raises:
            DatabaseInteractionException: If there is an error during the save operation.
        """
        try:
            doc: SyslogDocument = SyslogDocument(
                unit_id=str(syslog_object.unit_id),
                span_id=syslog_object.span_id,
                trace_id=syslog_object.trace_id,
                timestamp=syslog_object.timestamp,
                raw_data=syslog_object.raw_data
            )
            doc.save()
        except Exception as e:
            self.__logger.error(f"Failed to save SyslogObject: {e}")
            raise DatabaseInteractionException(
                f"Failed to save SyslogObject: {e}",
                (str(syslog_object),)
            )

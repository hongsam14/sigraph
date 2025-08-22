"""_summary_
This module defines the DBSession class for interacting with OpenSearch.
DBSession is responsible for storing SysLogObject entries.
!!!NOTICE!!!
https://forum.opensearch.org/t/about-python-client-library-and-elasticsearch-dsl-support/4756/11?utm_source=chatgpt.com
to support OpenSearch, you need to use the `elasticsearch` library 7.13 or earlier.
"""

from typing import Any
from opensearchpy import OpenSearch
from db.db_model import SyslogModel, install_syslog_template_and_index
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


    def store_syslog_object(self, syslog_object: SyslogModel):
        """_summary_
        Save a SyslogObject to OpenSearch.

        Args:
            syslog_object (SyslogModel): The SyslogObject to save.

        Raises:
            DatabaseInteractionException: If there is an error during the save operation.
        """
        try:
            self.__client.index(
                index=self.__index_name,
                body=syslog_object,
                params={"refresh": "wait_for"},  # Ensures the document is searchable immediately
            )
        except Exception as e:
            self.__logger.error(f"Failed to save SyslogObject: {e}")
            raise DatabaseInteractionException(
                f"Failed to save SyslogObject: {e}",
                (str(syslog_object),)
            ) from e

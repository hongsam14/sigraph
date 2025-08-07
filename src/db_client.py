"""db_client.py
This module defines the DBClient class for interacting with OpenSearch to store SysLogObject entries.
!!!NOTICE!!!
https://forum.opensearch.org/t/about-python-client-library-and-elasticsearch-dsl-support/4756/11?utm_source=chatgpt.com
to support OpenSearch, you need to use the `elasticsearch` library 7.13 or earlier.
"""

# from elasticsearch_dsl import connections, Document, Keyword, Text, Date
# from model import SysLogObject

# class SyslogDocument(Document):
#     """_summary_
#     SyslogDocument is a document model for storing syslog entries in OpenSearch.
#     """
#     analysis_id = Keyword()
#     span_id = Keyword()
#     trace_id = Keyword()
#     timestamp = Date()
#     raw_data = Text()


#     class Index:
#         name = 'syslog_index'
#         settings = {
#             "number_of_shards": 1,
#             "number_of_replicas": 0
#         }


# class DBClient:
#     """__summary__
#     DBClient is a client for interacting with opensearch for storing Syscall Objects.
#     """
#     __index_name: str
#     __syslog_doc: SyslogDocument


#     def __init__(self, uri: str, index_name: str):
#         self.index_name = index_name
#         self.__syslog_doc = SyslogDocument()
        
#         print(f"Connecting to OpenSearch at {uri} with index {index_name}")
#         connections.create_connection(hosts=[f"http://{uri}:9200"])
        
#         # document initialization
#         self.__syslog_doc.init()

#     def save_syslog_object(self, syslog_object: SysLogObject):
#         """Save a SysLogObject to OpenSearch."""
#         doc = SyslogDocument(
#             analysis_id=str(syslog_object.analysis_id),
#             span_id=syslog_object.span_id,
#             trace_id=syslog_object.trace_id,
#             timestamp=syslog_object.timestamp,
#             raw_data=syslog_object.raw_data
#         )
#         doc.save()

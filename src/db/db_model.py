from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from elasticsearch_dsl import Document, Keyword, Date, Object


class SyslogDocument(Document):
    """_summary_
    SyslogDocument is a document model for storing syslog entries in OpenSearch.
    """
    unit_id = Keyword()
    span_id = Keyword()
    trace_id = Keyword()
    timestamp = Date()
    raw_data = Object(
        dynamic=True,
    )

    class Index:
        name = 'syslog_index'
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
        
        ## Mapping template
        mappings = {
            "dynamic_templates": [
                {
                    "message_text": {
                        "match_mapping_type": "string",
                        "mapping": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 1024
                                }
                            }
                        }
                    }
                },
                {
                    "message_object": {
                        "match_mapping_type": "object",
                        "mapping": {
                            "type": "object",
                        }
                    }
                }
            ]
        }


class SyslogModel(BaseModel):
    """SyslogModel is a Pydantic model for syslog entries interface."""
    unit_id: UUID
    span_id: str
    trace_id: str
    timestamp: datetime
    raw_data: dict

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
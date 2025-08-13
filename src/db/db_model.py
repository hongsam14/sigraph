from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from elasticsearch_dsl import Document, Keyword, Date, Object

## Check for Flattened type support
try:
    from elasticsearch_dsl import Flattened
    HAS_FLATTENED = True
except ImportError:
    HAS_FLATTENED = False

from elasticsearch_dsl import connections


class SyslogDocument(Document):
    """_summary_
    SyslogDocument is a document model for storing syslog entries in OpenSearch.
    """
    unit_id = Keyword()
    span_id = Keyword()
    trace_id = Keyword()
    timestamp = Date()
    # if dsl supports flattened type, use it because it helps prevent field explosion.
    if HAS_FLATTENED:
        raw_data = Flattened()
    else:
        raw_data = Object(enabled=True, dynamic=True)

    class Index:
        name = 'syslog_index'
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }


def install_syslog_template_and_index(client):
        """
        - register dynamic_templates first at Composable Index Template
        - if there are no physical indices, create syslog_index-000000
        """
        # dynamic templates
        # first register id keys.
        dynamic_templates = [
            {
                "ids_as_keyword": {
                    "match_pattern": "regex",
                    "match": "^(trace_id|span_id|unit_id|.*_id)$",
                    "mapping": {"type": "keyword", "ignore_above": 256}
                }
            },
            # register raw_data_strings as keyword or flattened
            {
                "raw_data_strings": {
                    "path_match": "raw_data.*",
                    "mapping": {"type": "keyword", "ignore_above": 1024}
                }
            },
            # else, treat as text and keyword
            {
                "strings_as_text": {
                    "match_mapping_type": "string",
                    "mapping": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword", "ignore_above": 1024}
                        }
                    }
                }
            }
        ]

        # express the properties according to the Doc definition
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/dynamic-templates.html
        properties = {
            "unit_id":  {"type": "keyword"},
            "span_id":  {"type": "keyword"},
            "trace_id": {"type": "keyword"},
            "timestamp": {"type": "date"},
            "raw_data": ({"type": "flattened"} if HAS_FLATTENED else {"type": "object", "dynamic": True})
        }

        # install index template & update
        body = {
            "index_patterns": ["syslog_index-*"],
            "priority": 100,
            "template": {
                "settings": SyslogDocument.Index.settings,
                "mappings": {
                    "dynamic_templates": dynamic_templates,
                    "properties": properties
                },
                "aliases": {
                    "syslog_index": {}  # 생성 시 자동으로 별칭 연결
                }
            }
        }

        # Common ES/OpenSearch API (compatible with OpenSearch 2.x/ES 7.x)
        client.indices.put_index_template(name="syslog-template", body=body)

        # Check if the index exists, if not create it
        if not client.indices.exists(index="syslog_index-*"):
            client.indices.create(
                index="syslog_index-000001",
                body={
                    "settings": SyslogDocument.Index.settings,
                    "mappings": {"dynamic_templates": dynamic_templates, "properties": properties},
                    "aliases": {"syslog_index": {"is_write_index": True}}
                }
            )





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
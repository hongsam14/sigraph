"""_summary_
Define the database model for syslog entries in OpenSearch.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from opensearchpy import OpenSearch


def install_syslog_template_and_index(client: OpenSearch):
    """
    - register dynamic_templates first at Composable Index Template
    - if there are no physical indices, create syslog_index-000000
    """

    settings = {
        "number_of_shards": 1,
        "number_of_replicas": 0
    }

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
                "match_mapping_type": "string",
                "mapping": {"type": "keyword", "ignore_above": 1024}
            }
        },
        {
            "raw_data_strings": {
                "path_match": "raw_data.Metadata.*",
                "match_mapping_type": "string",
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
        "tactics": {"type": "keyword"},
        "rule_ids": {"type": "keyword"},
        "raw_data": {
            "type": "object",
            "dynamic": True,
            "enabled": True,
        }
    }

    # install index template & update
    body = {
        "index_patterns": ["syslog_index-*"],
        "priority": 100,
        "template": {
            "settings": settings,
            "mappings": {
                "dynamic_templates": dynamic_templates,
                "properties": properties
            },
            "aliases": {
                "syslog_index": {} # alias for the write index
            }
        }
    }

    # Common ES/OpenSearch API (compatible with OpenSearch 2.x/ES 7.x)
    if not client.indices.exists_index_template(name="syslog-template"):
        client.indices.put_index_template(name="syslog-template", body=body)

    # Check if the index exists, if not create it
    exists = client.indices.exists_alias(name="syslog_index")
    if not exists:
        print("Creating initial index syslog_index-000001")
        client.indices.create(
            index="syslog_index-000001",
            body={
                "settings": settings,
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
    tactics: Optional[str] = None
    rule_ids: Optional[str] = None
    raw_data: dict

    class Config:
        """Configuration for SyslogModel."""
        orm_mode = True
        arbitrary_types_allowed = True

class SyslogSequence(BaseModel):
    """SyslogSequence is a Pydantic model for a sequence of syslog entries."""
    label: str
    syslogs: list[dict]

    class Config:
        """Configuration for SyslogSequence."""
        orm_mode = True
        arbitrary_types_allowed = True

    def extend(self, other: 'SyslogSequence'):
        """Extend the syslogs list with another SyslogSequence's syslogs."""
        self.syslogs.extend(other.syslogs)

    def sort_by_timestamp(self):
        """Sort the syslogs list by timestamp."""
        self.syslogs.sort(key=lambda x: x.get('Timestamp', ''))

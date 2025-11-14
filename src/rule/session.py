import re
from typing import Any
from uuid import UUID
from pydantic import BaseModel
from fastapi import UploadFile, File
from sigma.backends.opensearch import OpensearchLuceneBackend
from sigma.collection import SigmaCollection
from sigma.exceptions import SigmaError
from sigma.pipelines.sysmon import sysmon_pipeline
from sigma.rule import SigmaRule

from db.db_session import DBSession
from db.db_model import SyslogSequence

class QueryPair(BaseModel):
    category: str
    query: list[dict]

class RuleSession:
    __logger: Any
    __db_session: DBSession
    __backend: OpensearchLuceneBackend

    def __init__(self, logger: Any, db_session: DBSession):
        self.__logger: Any = logger
        self.__db_session: DBSession = db_session
        pipeline = sysmon_pipeline()
        self.__backend: OpensearchLuceneBackend = OpensearchLuceneBackend(pipeline=pipeline)

    async def query_sigma_rules(self,
                          unit_id: UUID,
                          rule_bytes: bytes, 
                          prefix: str = "raw_data.Metadata") -> SyslogSequence:
        """Convert Sigma rule bytes to a list of Lucene query dictionaries."""
        try:
            lucene_queries: list[QueryPair] = self.__sigma_bytes_to_lucene_query(
                rule_bytes=rule_bytes,
                prefix=prefix
                )
            self.__logger.info(f"Converted Sigma rules to {len(lucene_queries)} Lucene queries. queries: {lucene_queries}")
        except Exception as e:
            self.__logger.error(f"Error converting Sigma rules to Lucene queries: {e}")
            raise RuntimeError(
                f"Error converting Sigma rules to Lucene queries: {e}"
            ) from e
        try:
            total_result: SyslogSequence = SyslogSequence(label="", syslogs=[])
            for query_pair in lucene_queries:
                result: SyslogSequence = await self.__db_session.get_syslog_by_subquery(
                    unit_id=unit_id,
                    category=query_pair.category,
                    query=query_pair.query
                )
                total_result.syslogs.extend(result.syslogs)
            return total_result
        except Exception as e:
            self.__logger.error(f"Error querying syslog by Lucene queries: {e}")
            raise RuntimeError(
                f"Error querying syslog by Lucene queries: {e}"
             ) from e

    def __sigma_bytes_to_lucene_query(self, rule_bytes: bytes, prefix: str) -> list[QueryPair]:
        """Convert Sigma rule bytes to a Lucene query dictionary."""
        ret_QueryPair_list: list[QueryPair] = []
        # Parse Sigma rules from bytes
        try:
            rules: SigmaCollection = SigmaCollection.from_yaml(rule_bytes)
        except SigmaError as sigma_e:
            self.__logger.error(f"Failed to parse Sigma rules: {sigma_e}")
            raise ValueError(f"Failed to parse Sigma rules: {sigma_e}") from sigma_e
        except Exception as e:
            self.__logger.error(f"Unexpected error while parsing Sigma rules: {e}")
            raise RuntimeError(f"Unexpected error while parsing Sigma rules: {e}") from e
        
        for rule in rules:
            if not isinstance(rule, SigmaRule):
                self.__logger.error("Encountered a non-SigmaRule object in the collection; skipping.")
                raise TypeError("Encountered a non-SigmaRule object in the collection;")
            ret_queries = []
            try:
                queries: list[Any] = self.__backend.convert_rule(rule, output_format="dsl_lucene")
            except Exception as e:
                self.__logger.error(f"Failed to convert Sigma rule to Lucene query: {e}")
                continue
            for query in queries:
                # Attach 'raw_data.Metadata' to prefix generated query keys
                self.__add_prefix_to_query(query, prefix=prefix)
                ret_queries.append(query)
            ret_QueryPair: QueryPair = QueryPair(
                category=rule.logsource.category,
                query=ret_queries
            )
            ret_QueryPair_list.append(ret_QueryPair)
        return ret_QueryPair_list

    def __add_prefix_to_query(self, query: dict, prefix: str):
        """Add a prefix to all keys in the query dictionary."""
        def scan_recursive(element):
            if isinstance(element, dict):
                for key, value in element.items():
                    if key.lower() == "query" and isinstance(value, str):
                        # meet the query string, add prefix
                        element[key] = self.__add_prefix_to_query_string(value, prefix)
                    scan_recursive(value)
            elif isinstance(element, list):
                for item in element:
                    scan_recursive(item)
        scan_recursive(query)

    def __add_prefix_to_query_string(self, query_string: str, prefix: str) -> str:
        return re.sub(
            pattern=r"\b([A-Za-z0-9_]+):",
            repl=lambda match: f"{prefix}.{match.group(1)}:",
            string=query_string)

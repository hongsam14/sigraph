"""_summary_
GraphClient module for managing Neo4j graph database connections and operations.
It includes the GraphClient class that handles connection setup, constraint application,
and provides methods for interacting with the graph database.
"""

from __future__ import annotations
import asyncio
from typing import List, Dict, Union, Tuple, Any, LiteralString, Callable, cast
from pydantic import SecretStr
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncResult, AsyncSession
from neo4j.exceptions import ServiceUnavailable, TransientError
from .node import Node, Relationship, NodeExtension

class GraphClient:

    __logger: Any
    __driver: AsyncDriver
    __database: str

    __retry_count: int
    __retry_delay: float

    _primary_key_map: Dict[str, Union[str, Tuple[str, ...]]]

    def __init__(
            self,
            logger: Any,
            uri: str,
            user: str,
            password: SecretStr,
            database: str = "neo4j",
            # config
            max_connection_pool_size: int = 20,
            max_connection_lifetime: int = 1800,
            connection_acquisition_timeout: int = 30,
            keep_alive: bool = True,
            # ...
            retry_count: int = 3,
            retry_delay: float = 2.0,
            primary_keys: Dict[str, Union[str, Tuple[str, ...]]] | None = None
            ):
        
        """_summary_
        Initializes the GraphClient with a Neo4j connection.

        Args:
            uri (str): URI of the Neo4j database.
            user (str): Username for the Neo4j database.
            password (SecretStr): Password for the Neo4j database.
        """
        
        self.__logger = logger
        self.__database = database
        self.__driver = AsyncGraphDatabase.driver(
            uri,
            auth=(user, password.get_secret_value()),
            max_connection_pool_size=max_connection_pool_size,
            max_connection_lifetime=max_connection_lifetime,
            connection_acquisition_timeout=connection_acquisition_timeout,
            keep_alive=keep_alive,
        )

        self.__retry_count = retry_count
        self.__retry_delay = retry_delay

        self._primary_key_map: Dict[str, Union[str, Tuple[str, ...]]] = primary_keys or {}

    async def close(self) -> None:
        """_summary_
        Closes the Neo4j database connection.
        """
        await self.__driver.close()

    async def run(self, cypher: LiteralString, **params: Any) -> List[dict[str, Any]]:
        """_summary_
        Executes a Cypher query against the Neo4j database.

        Args:
            cypher (str): The Cypher query to execute.
            params (Any): Parameters for the Cypher query.

        Returns:
            List[Dict[str, Any]]: The result of the query as a list of dictionaries.
        """
        for attempt_count in range(self.__retry_count):
            try:
                async with self.__driver.session(database=self.__database) as session:
                    ## set query parameters

                    result: AsyncResult = await session.run(cypher, **params)
                    return await result.data()
            except (ServiceUnavailable, TransientError) as e:
                # check attempt count
                # if last attempt, raise the exception
                if attempt_count == self.__retry_count - 1:
                    self.__logger.error(
                        f"All {self.__retry_count} attempts failed. "
                        f"Raising exception."
                    )
                    raise e
                # sleep for retry delay
                # delay increases with each attempt (exponential backoff)
                await asyncio.sleep(self.__retry_delay * (attempt_count ** 2))
        raise RuntimeError("Unreachable code reached in run()")
        

    async def merge_node(self, sub_node: Node, primary_label: str, primary_key: str) -> None:
        """_summary_
        Merges a node into the Neo4j database.

        Args:
            node (Node): The node to merge.
            primary_label (str): The primary label of the node.
            primary_key (str): The primary key property of the node.
        """

        ## extract labels and properties and check primary key exists
        labels, props = NodeExtension.extract_node(sub_node)
        if primary_key not in props:
            raise ValueError(
                f"merge() needs property '{primary_key}' in node props. got: {list(props.keys())}"
            )
        pk_val = props[primary_key]
        extra_labels = [elem for elem in labels if elem != primary_label]

        ## generate query and params
        query = [
            f"MERGE (n:`{primary_label}` {{{primary_key}: $pk}})",
            "SET n += $props",
        ]
        for l in extra_labels:
            query.append(f"SET n:`{l}`")
        params = {"pk": pk_val, "props": props}
        cypher_str = "\n".join(query)
        cypher = cast(LiteralString, cypher_str)

        ## execute query
        async with self.__driver.session(database=self.__database) as session:
            await self._retry_write(
                session,
                self._work_transaction_async,
                cypher,
                **params
            )
            return
        raise RuntimeError("Unreachable code reached in merge_node()")

    async def create_relation(self, rel: Relationship) -> None:
        # extract start/end nodes
        slabels, sprops = NodeExtension.extract_node(rel.start)
        elabels, eprops = NodeExtension.extract_node(rel.end)
        
        if not slabels or not elabels:
            raise ValueError("Both start/end nodes must have at least one label")

        start_primary_label = slabels[0]
        end_primary_label = elabels[0]

        ## get schema primary keys from map
        start_primary_key = self._primary_key_map.get(start_primary_label)
        end_primary_key = self._primary_key_map.get(end_primary_label)
        if start_primary_key is None or end_primary_key is None:
            raise ValueError(
                f"primary_keys mapping required for labels: {start_primary_label} -> ?, {end_primary_label} -> ?"
            )
        
        ## pick id values
        s_id = NodeExtension.pick_id(sprops, start_primary_key)
        e_id = NodeExtension.pick_id(eprops, end_primary_key)

        ## generate cypher query
        set_extra_start_properties = [f"SET s:`{l}`" for l in slabels[1:]]
        set_extra_exit_properties = [f"SET e:`{l}`" for l in elabels[1:]]

        s_match = ", ".join([f"{k}: $s_id.{k}" for k in s_id.keys()])
        e_match = ", ".join([f"{k}: $e_id.{k}" for k in e_id.keys()])

        rel_props = rel.properties or {}
        rel_set = "SET r += $rprops" if rel_props else ""

        cypher = f"""
        MERGE (s:`{start_primary_label}` {{ {s_match} }})
        SET s += $sprops
        {' '.join(set_extra_start_properties)}
        MERGE (e:`{end_primary_label}` {{ {e_match} }})
        SET e += $eprops
        {' '.join(set_extra_exit_properties)}
        MERGE (s)-[r:`{rel.type}`]->(e)
        {rel_set}
        RETURN elementId(r) as rid
        """

        # attach params
        params = {
            "s_id": s_id,
            "e_id": e_id,
            "sprops": sprops,
            "eprops": eprops,
            "rprops": rel_props,
        }

        async with self.__driver.session(database=self.__database) as session:
            await self._retry_write(session=session, func=self._work_transaction_async, cypher=cypher, **params)
            return
            # ## check return type is correct
            # if rows is None:
            #     return None
            # if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            #     raise ValueError("Unexpected result format from create_relation()")
            # return rows[0].get("rid")
        raise RuntimeError("Unreachable code reached in create_relation()")


    async def _retry_write(self, session: AsyncSession, func: Callable, *args: Any, **kwargs: Any) -> Any:
        for attempt_count in range(self.__retry_count):
            try:
                return await session.execute_write(func, *args, **kwargs)
            except (ServiceUnavailable, TransientError) as e:
                if attempt_count == self.__retry_count - 1:
                    raise e
                await asyncio.sleep(self.__retry_delay * (attempt_count ** 2))

        raise RuntimeError("Unreachable code reached in _retry_write()")

    async def _work_transaction_async(self, tx: Any, cypher: LiteralString, **params: Any) -> List[dict[str, Any]]:
        result: AsyncResult = await tx.run(cypher, **params)
        return await result.consume()
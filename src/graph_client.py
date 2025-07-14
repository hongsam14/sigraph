"""_summary_
This module provides a GraphClient class for interacting syscall nodes in a graph database.
"""

from uuid import UUID
from py2neo import Graph, Node, Relationship
from model import SyscallOP, Syscall, SyscallNode


class GraphClient:
    """__summary_
    GraphClient is a client for interacting with a Neo4j graph database with Syscall Object.
    """
    __driver: Graph

    def __init__(self, uri: str, user: str, password: str):
        print(f"Connecting to Neo4j at {uri} with user {user} with password {password}")
        try:
            # Initialize the Neo4j driver with the provided URI, user, and password
            self.__driver = Graph(f"bolt://{uri}:7687", auth=(user, password))
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Neo4j database at {uri}. "
                "Please check your connection settings."
            ) from e

    def upsert_syscall_object(self, syscall_node: SyscallNode):
        """_summary_
        upsert syscall object in the graph database.
        This method will either update an existing syscall node or create a new one

        Args:
            syscall_node (SyscallNode): The syscall node to be upserted.
        Raises:
            ValueError: If multiple syscall nodes are found with the same syscall and analysis_id.
            This means there is a data inconsistency in the graph.
        Returns:
            None
        """
        # search for the same syscall object in the graph.
        # If it exists, update it. If not, create it.
        current = self.__get_syscall_from_graph(
            syscall=syscall_node.syscall, analysis_id=syscall_node.analysis_id
        )
        # if there is no matched node, then create a new node.
        if not current:
            current = Node(
                self.__syscall_label(syscall_node.syscall),
                syscall=str(syscall_node.syscall),
                analysis_id=str(syscall_node.analysis_id),
            )
        # set data to the node.
        current["analysis_id"] = str(syscall_node.analysis_id)
        if syscall_node.parent:
            current["parent"] = [
                str(parent_syscall) for parent_syscall in syscall_node.parent
            ]
        if syscall_node.tactics:
            current["tactics"] = list(
                set(syscall_node.tactics + current.get("tactics", []))
            )
        if syscall_node.matched_ids:
            current["matched_ids"] = list(
                set(
                    str(i)
                    for i in syscall_node.matched_ids
                    + [UUID(m) for m in current.get("matched_ids", []) if m]
                )
            )
        if syscall_node.start_at:
            current["start_at"] = syscall_node.start_at.isoformat()
        if syscall_node.end_at:
            current["end_at"] = syscall_node.end_at.isoformat()
        # update the current node in the graph.
        self.__driver.merge(
            current, self.__syscall_label(syscall_node.syscall), "syscall"
        )
        # check if the syscall object has parent. create a relationship with the parent.
        if syscall_node.parent and len(syscall_node.parent) > 0:
            # if it has parent, then create a relationship with the parent.
            for parent_syscall in syscall_node.parent:
                # get node type from the parent syscall
                current_parent = self.__driver.nodes.match(
                    self.__syscall_label(parent_syscall),
                    syscall=str(parent_syscall),
                    analysis_id=str(syscall_node.analysis_id),
                )
                current_parent = self.__get_syscall_from_graph(
                    syscall=parent_syscall, analysis_id=syscall_node.analysis_id
                )
                # if there is no matched parent node, then create a new node.
                if not current_parent:
                    current_parent = Node(
                        self.__syscall_label(parent_syscall),
                        syscall=str(parent_syscall),
                        analysis_id=str(syscall_node.analysis_id),
                    )
                self.__driver.merge(
                    current_parent, self.__syscall_label(parent_syscall), "syscall"
                )
                # creaet relationship
                self.__create_relationship(
                    parent=current_parent,
                    parent_label=parent_syscall.type,
                    child=current,
                    child_label=syscall_node.syscall.type,
                )

    def __syscall_label(self, syscall: Syscall) -> str:
        """Map syscall.type to Neo4j label"""
        return syscall.type.lower()  # execve, file, network
    
    def __get_syscall_from_graph(self, syscall: Syscall, analysis_id: UUID) -> Node:
        """Get syscall node from the graph database"""
        # search for the syscall node in the graph.
        current = list(self.__driver.nodes.match(
            self.__syscall_label(syscall),
            syscall=str(syscall),
            analysis_id=str(analysis_id),
        ))
        # if there is no matched node, then return None.
        if not current or len(current) == 0:
            return None
        # if there are multiple matched nodes, then raise an error.
        elif len(current) > 1:
            raise ValueError(
                f"Multiple syscall objects found with syscall {syscall} and analysis_id {analysis_id}. "
                "This should not happen. Please check your data."
            )
        return current[0]

    def __create_relationship(
        self, parent: Node, parent_label: SyscallOP, child: Node, child_label: SyscallOP
    ):
        """Create a relationship between parent and child nodes"""
        # check labels of parent and child nodes
        if parent_label == SyscallOP.EXECVE and child_label == SyscallOP.FILE:
            rel_type = "WRITE_TO"
        elif parent_label == SyscallOP.FILE and child_label == SyscallOP.EXECVE:
            rel_type = "READ_FROM"
        elif parent_label == SyscallOP.NETWORK and child_label == SyscallOP.EXECVE:
            rel_type = "RECV_FROM"
        elif parent_label == SyscallOP.EXECVE and child_label == SyscallOP.NETWORK:
            rel_type = "SEND_TO"
        else:
            rel_type = "CREATE"

        rel = Relationship(parent, rel_type, child)
        self.__driver.merge(rel)

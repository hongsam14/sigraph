"""_summary_
Node module for defining the Node class representing nodes in a Neo4j graph database.

It includes attributes for labels and properties, along with methods for
managing node data.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Iterable, Mapping, Tuple, Union

@dataclass(frozen=False)
class Node:
    """_summary_
    Represents a node in a Neo4j graph database.

    Attributes:
        - labels (List[str]): List of labels associated with the node.
        - properties (Dict[str, Any]): Dictionary of properties for the node.
    """
    labels: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

    def __init__(self,
                 labels: List[str],
                 properties: Dict[str, Any] | None = None) -> None:
        """_summary_
        Initializes a Node with given labels and properties.

        Args:
            - labels (List[str]): List of labels for the node.
            - properties (Dict[str, Any] | None): Dictionary of properties for the node.
        """
        self.labels = labels
        self.properties = properties if properties is not None else {}

    @classmethod
    def from_label(cls, label: str, **properties: Any)-> "Node":
        """_summary_
        Creates a Node instance from a single label and optional properties.

        Args:
            - label (str): The label for the node.
            - properties (Any): Additional properties for the node.

        Returns:
            - Node: An instance of the Node class.

        Raises:
            - ValueError: If the label is an empty string.
        """
        if not label:
            raise ValueError("Label must be a non-empty string.")
        return cls(labels=[label], properties=properties)
    
    def with_labels(self, extra: Iterable[str]) -> "Node":
        """_summary_
        Creates a new Node instance with additional labels.

        Args:
            - extra (Iterable[str]): Additional labels to add to the node.

        Returns:
            - Node: A new Node instance with the combined labels.
        """
        return Node(labels=list(dict.fromkeys([*self.labels, *extra])), properties=dict(self.properties))
    
    def with_props(self, **extra: Any) -> "Node":
        """_summary_
        Creates a new Node instance with additional properties.
        
        Args:
            - extra (Any): Additional properties to add to the node.
        
        Returns:
            - Node: A new Node instance with the combined properties.
        """
        props = dict(self.properties)
        props.update(extra)
        return Node(labels=list(self.labels), properties=props)

    def __getitem__(self, key: str) -> Any:
        """_summary_
        Allows dictionary-like access to node properties.

        Args:
            - key (str): The property key to access.
        Returns:
            - Any: The value associated with the given key.
        Raises:
            - KeyError: If the key does not exist in the properties.
        """
        if key in self.properties:
            return self.properties[key]
        raise KeyError(f"Key '{key}' not found in node properties.")

    def __setitem__(self, key: str, value: Any) -> None:
        """_summary_
        Allows setting properties on the node.

        Args:
            - key (str): The property key to set.
            - value (Any): The value to set for the given key.
        """
        self.properties[key] = value

    def __contains__(self, key: str) -> bool:
        """_summary_
        Checks if a property key exists in the node.

        Args:
            - key (str): The property key to check.

        Returns:
            - bool: True if the key exists, False otherwise.
        """
        return key in self.properties

    def get(self, key: str, default: Any = None) -> Any:
        """_summary_
        Gets a property value with a default if the key does not exist.

        Args:
            - key (str): The property key to access.
            - default (Any): The default value to return if the key is not found.
        """
        return self.properties.get(key, default)

@dataclass(frozen=False)
class Relationship:
    """_summary_
    Represents a relationship between two nodes in a Neo4j graph database.

    Attributes:
        - start (Node | Mapping[str, Any] | Any): The starting node of the relationship.
        - end (Node | Mapping[str, Any] | Any): The ending node of the relationship.
        - type (str): The type of the relationship.
        - properties (Dict[str, Any]): Dictionary of properties for the relationship.
    """
    start: Node | Mapping[str, Any] | Any
    end: Node | Mapping[str, Any] | Any
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def __init__(self,
                    start: Node | Mapping[str, Any] | Any,
                    type: str,
                    end: Node | Mapping[str, Any] | Any,
                    properties: Dict[str, Any] | None = None) -> None:
        """_summary_
        Initializes a Relationship with given start/end nodes, type, and properties.
        Args:
            - start (Node | Mapping[str, Any] | Any): The starting node of the relationship.
            - type (str): The type of the relationship.
            - end (Node | Mapping[str, Any] | Any): The ending node of the relationship.
            - properties (Dict[str, Any] | None): Dictionary of properties for the relationship.
        """
        self.start = start
        self.end = end
        self.type = type
        self.properties = properties if properties is not None else {}

    @classmethod
    def from_any(x: Any) -> "Relationship":
        """_summary_
        Creates a Relationship instance from various input types.

        Args:
            - x (Any): The input to convert into a Relationship.

        Returns:
            - Relationship: An instance of the Relationship class.

        Raises:
            - ValueError: If the input cannot be converted to a Relationship.
        """
        if isinstance(x, Relationship):
            return x
        if isinstance(x, Mapping):
            try:
                start = x["start"]
                end = x["end"]
                type_ = x["type"]
                properties = x.get("properties", {})
                return Relationship(start=start, end=end, type=type_, properties=properties)
            except KeyError as e:
                raise ValueError(f"Missing key in mapping: {e}")
        raise ValueError("Cannot convert to Relationship.")
    
    def with_props(self, **extra: Any) -> "Relationship":
        """_summary_
        Creates a new Relationship instance with additional properties.

        Args:
            - extra (Any): Additional properties to add to the relationship.
        
        Returns:
            - Relationship: A new Relationship instance with the combined properties.
        """
        props = dict(self.properties)
        props.update(extra)
        return Relationship(
            start=self.start,
            end=self.end,
            type=self.type,
            properties=props
        )

    def __getitem__(self, key: str) -> Any:
        """_summary_
        Allows dictionary-like access to relationship properties.

        Args:
            - key (str): The property key to access.

        Returns:
            - Any: The value associated with the given key.

        Raises:
            - KeyError: If the key does not exist in the properties.
        """
        if key in self.properties:
            return self.properties[key]
        raise KeyError(f"Key '{key}' not found in relationship properties.")
    
    def __setitem__(self, key: str, value: Any) -> None:
        """_summary_
        Allows setting properties on the relationship.

        Args:
            - key (str): The property key to set.
            - value (Any): The value to set for the given key.
        """
        self.properties[key] = value

    def __contains__(self, key: str) -> bool:
        """_summary_
        Checks if a property key exists in the relationship.

        Args:
            - key (str): The property key to check.
        
        Returns:
            - bool: True if the key exists, False otherwise.
        """
        return key in self.properties

    def get(self, key: str, default: Any = None) -> Any:
        """_summary_
        Gets a property value with a default if the key does not exist.

        Args:
            - key (str): The property key to access.
            - default (Any): The default value to return if the key is not found.
        """
        return self.properties.get(key, default)


class NodeExtension:
    """
    Extension class for Node & Relationship to add additional functionality.
    """

    @staticmethod
    def is_node(obj: Any) -> bool:
        """_summary_
        Checks if the given object is a Node or has Node-like attributes.
        """
        if isinstance(obj, Node):
            return True
        return hasattr(obj, "labels") and hasattr(obj, "properties")
    
    @staticmethod
    def is_relationship(obj: Any) -> bool:
        """_summary_
        Checks if the given object is a Relationship or has Relationship-like attributes.
        """
        if isinstance(obj, Relationship):
            return True
        return (
            hasattr(obj, "start") and
            hasattr(obj, "end") and
            hasattr(obj, "type") and
            hasattr(obj, "properties")
        )
    
    @staticmethod
    def dict_to_node(labels: List[str], data: dict[str, Any]) -> Node:
        """_summary_
        Converts a dictionary to a Node instance.

        Args:
            - data (Dict[str, Any]): The dictionary containing node data.

        Returns:
            - Node: An instance of the Node class.

        Raises:
            - ValueError: If the dictionary does not contain required keys.
        """
        try:
            if labels is None:
                labels = data["labels"]
            properties = {k: v for k, v in data.items() if k != "labels"}
            return Node(labels=labels, properties=properties)
        except KeyError as e:
            raise ValueError(f"Missing key in dictionary: {e}")

    @staticmethod
    def extract_node(obj: Node | Mapping[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
        """_summary_
        Extracts labels and properties from a Node or mapping.
        labels's key can be either **"labels"** or **"_labels"**.

        Args:
            - node (Node | Mapping[str, Any]): The node to extract from.

        Returns:
            - Tuple[List[str], Dict[str, Any]]: A tuple containing the labels and properties.
        """
        if isinstance(obj, Node):
            return list(obj.labels), dict(obj.properties)
        
        if isinstance(obj, Mapping):
            labels = list(obj.get("labels", [])) or list(obj.get("_labels", []))
            properties = {key: value for key, value in obj.items() if key not in ("labels", "_labels")}
            if not isinstance(labels, list):
                raise ValueError("Labels must be a list.")
            if not isinstance(properties, dict):
                raise ValueError("Properties must be a dictionary.")
            if labels:
                return labels, properties
        raise ValueError("Cannot extract node data.")
    
    @staticmethod
    def pick_id(props: Dict[str, Any], primary_key: Union[str, Tuple[str, ...]]) -> Dict[str, Any]:
        """_summary_
        Picks the ID value from properties based on the primary key.

        Args:
            - props (Dict[str, Any]): The properties dictionary.
            - primary_key (Union[str, Tuple[str, ...]]): The primary key or keys to look for.

        Returns:
            - Dict[str, Any]: A dictionary containing the ID key-value pair. {{primary_key: value}}

        Raises:
            - ValueError: If the primary key(s) are not found in the properties.
        """
        if isinstance(primary_key, tuple):
            ## check missing keys in props
            missing_keys = [key for key in primary_key if key not in props]
            if missing_keys:
                raise ValueError(f"Missing primary key(s) in properties: {missing_keys}")
            return {key: props[key] for key in primary_key}
        if primary_key not in props:
            raise ValueError(f"Missing primary key '{primary_key}' in properties.")
        return {primary_key: props[primary_key]}
        

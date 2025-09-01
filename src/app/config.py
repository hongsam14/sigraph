"""_summary_
Configuration settings for the application.
"""

import os
from pydantic import SecretStr

class AppConfig:
    """_summary_
    Application configuration class to manage environment variables and settings.
    """    
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI", "localhost")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password: SecretStr = SecretStr(os.getenv("NEO4J_PASSWORD", ""))
        
        self.opensearch_uri = os.getenv("OPENSEARCH_URI", "localhost")
        self.opensearch_index = os.getenv("OPENSEARCH_INDEX", "syslog_index")
        
        self.backend_uri = os.getenv("BACKEND_URI", "localhost")
        self.backend_port = os.getenv("BACKEND_PORT", "8765")
        
        self.ai_model = os.getenv("AI_MODEL", "")
        self.ai_realtime_model = os.getenv("AI_REALTIME_MODEL", "")
        self.ai_chunk_size = int(os.getenv("AI_CHUNK_SIZE", 400))
        self.ai_overlap = int(os.getenv("AI_OVERLAP", 40))
        self.ai_api_key: SecretStr = SecretStr(os.getenv("AI_API_KEY", ""))

    def get_graph_session_config(self)-> dict:
        """Gets graph session configuration"""
        return {
            "uri": self.neo4j_uri,
            "user": self.neo4j_user,
        }

    def get_neo4j_password(self)-> SecretStr:
        """Gets Neo4j password"""
        return self.neo4j_password

    def get_db_session_config(self)-> dict:
        """Gets database session configuration"""
        return {
            "uri": self.opensearch_uri,
            "index_name": self.opensearch_index
        }

    def get_backend_config(self)-> dict:
        """Gets backend configuration"""
        return {
            "uri": self.backend_uri,
            "port": self.backend_port
        }

    def get_ai_config(self)-> dict:
        """Gets AI configuration"""
        return {
            "model": self.ai_model,
            "realtime_model": self.ai_realtime_model,
            "chunk_size": self.ai_chunk_size,
            "overlap": self.ai_overlap,
        }

    def get_ai_api_key(self)->SecretStr:
        """Gets AI API key"""
        return self.ai_api_key

"""_summary_
Configuration settings for the application.
"""

import os

class AppConfig:
    """_summary_
    Application configuration class to manage environment variables and settings.
    """
    
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI", "localhost")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "")
        self.opensearch_uri = os.getenv("OPENSEARCH_URI", "localhost")
        self.opensearch_index = os.getenv("OPENSEARCH_INDEX", "syslog_index")
        self.backend_uri = os.getenv("BACKEND_URI", "localhost")
        self.backend_port = os.getenv("BACKEND_PORT", 8765)
        self.open_ai_api_key = os.getenv("OPENAI_API_KEY", "")

    def get_graph_session_config(self):
        return {
            "uri": self.neo4j_uri,
            "user": self.neo4j_user,
            "password": self.neo4j_password
        }

    def get_db_session_config(self):
        return {
            "uri": self.opensearch_uri,
            "index_name": self.opensearch_index
        }

    def get_backend_config(self):
        return {
            "uri": self.backend_uri,
            "port": self.backend_port
        }
    
    def get_openai_api_key(self):
        return self.open_ai_api_key

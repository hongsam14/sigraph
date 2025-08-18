import requests
from requests import exceptions
import streamlit as st
from app.config import AppConfig

def send_message(config: AppConfig, message: str) -> dict:
    """
    Send message to the FastAPI backend and handle response
    """
    try:
        response = requests.post(
            f"http://{config.backend_uri}:{config.backend_port}/chat",
            params={"query": message},
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        
        # Simply return the response dict
        return data
    except exceptions.ConnectionError:
        error_msg = f"Unable to connect to backend at {config.backend_uri}:{config.backend_port}"
        st.error(error_msg)
        return {"error": error_msg}
    
    except exceptions.RequestException as e:
        error_msg = f"Error: {str(e)}"
        st.error(error_msg)
        return {"error": error_msg}
import os
import uvicorn
from typing import Any
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from app.config import AppConfig
from loguru import logger
from app.backend.api import BackendAPI

g_config: AppConfig = AppConfig()

def create_app(config: AppConfig) -> FastAPI:
    # Load environment variables from .env file
    load_dotenv()


    print(f"Configuration loaded: \n{config.get_backend_config()}\
        \n{config.get_graph_session_config()}\
        \n{config.get_db_session_config()}")

    ## check if log path exists, if not create it
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Initialize FastAPI application
    app = FastAPI()

    # Create Logger
    # TODO: This can be raise race condition if multiple instances are created.
    logger.add("logs/app.log",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            level="INFO")

    # Initialize Backend API
    backend_api = BackendAPI(logger, config)

    # Include the router in the FastAPI app
    app.include_router(backend_api.api_router)

    return app

## for local testing
if __name__ == "__main__":
    # run server
    uvicorn.run(
        create_app(g_config),
        host=g_config.backend_uri,
        port=int(g_config.backend_port)
        )
    
## for production level deployment
## for gunicorn server

app = create_app(g_config)

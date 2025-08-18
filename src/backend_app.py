import uvicorn
from typing import Any
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from app.config import AppConfig
from loguru import logger
from app.backend.api import BackendAPI


def main():
    # Load environment variables from .env file
    load_dotenv()

    config: AppConfig = AppConfig()

    print(f"Configuration loaded: \n{config.get_backend_config()}\
        \n{config.get_graph_session_config()}\
        \n{config.get_db_session_config()}")

    # Initialize FastAPI application
    app = FastAPI()

    # Create Logger
    logger.add("logs/app.log",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            level="INFO")

    # Initialize Backend API
    backend_api = BackendAPI(logger, config)


    # Include the router in the FastAPI app
    app.include_router(backend_api.api_router)

    # run server
    uvicorn.run(app, host=config.backend_uri, port=int(config.backend_port))

if __name__ == "__main__":
    main()

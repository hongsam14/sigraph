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

    # Initialize Backend API
    backend_api = BackendAPI(logger, config)

    # Include the router in the FastAPI app
    app.include_router(backend_api.api_router)
    
    @app.get("/healthz")      # liveness
    async def healthz():
        return {"ok": True}

    ready = True
    
    @app.get("/readyz")       # readiness
    async def readyz():
        return {"ready": ready}
    
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


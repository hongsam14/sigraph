from typing import Any
from fastapi import APIRouter
from app.config import AppConfig
from app.backend.v1.api import DBAPI
from app.backend.v1.api import AIAPI

class BackendAPI:
    # db_api: DBAPI
    ai_api: AIAPI

    api_router = APIRouter(prefix="/api")

    def __init__(self, logger: Any, config: AppConfig):
        self.db_api = DBAPI(logger, config)
        self.ai_api = AIAPI(logger, config)
        # Include the database API router
        self.api_router.include_router(self.db_api.api_router)
        self.api_router.include_router(self.ai_api.api_router)

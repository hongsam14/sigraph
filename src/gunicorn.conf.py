# Gunicorn configuration file
import os
import sys
import multiprocessing
from typing import Any
from dotenv import load_dotenv
from loguru import logger

# bind address
bind = f"0.0.0.0:{os.getenv('PORT', '8765')}"

# workers config: CPU*2~4
workers = int(os.getenv("WEB_CONCURRENCY", max(2, multiprocessing.cpu_count() * 2)))
worker_class = "uvicorn.workers.UvicornWorker"
threads = int(os.getenv("WEB_THREADS", 1))  # ASGI 비동기면 1 권장

# timeout/connection
timeout = int(os.getenv("TIMEOUT", 30))
graceful_timeout = int(os.getenv("GRACEFUL_TIMEOUT", 30))
keepalive = int(os.getenv("KEEPALIVE", 5))
backlog = int(os.getenv("BACKLOG", 4096))

# performance/stability
preload_app = True
worker_tmp_dir = "/dev/shm"

# logs
accesslog = os.getenv("ACCESS_LOG", "/app/logs/gunicorn_access.log")  # file or use '-' for stdout
errorlog  = os.getenv("ERROR_LOG", "/app/logs/gunicorn_error.log")
loglevel  = os.getenv("LOG_LEVEL", "info")

# Gunicorn hooks
def post_fork(server: Any, worker: Any) -> None:
    """Post-fork hook to re-initialize the application after forking.

    This function is called by Gunicorn after a worker process is forked.
    It re-initializes the FastAPI application to ensure that each worker
    has its own instance of the application.

    Args:
        server (Any): The Gunicorn server instance.
        worker (Any): The worker process instance.
    """
    # Remove existing logger handlers to avoid duplicate logs
    logger.remove()

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Create Logger
    # TODO: This can be raise race condition if multiple instances are created.
    logger.add("logs/backend-app.log",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            level="INFO",
            enqueue=True
            )
from flask import request
import time
import structlog
from app.core.config import config

logger = structlog.get_logger()

def register_logging_middleware(app):
    @app.before_request
    def start_timer():
        request.start_time = time.time()
        
    @app.after_request
    def log_request(response):
        if request.path.startswith('/static'):
            return response
            
        duration = time.time() - request.start_time
        
        logger.info(
            "http_request",
            method=request.method,
            path=request.path,
            status=response.status_code,
            duration=round(duration, 4),
            ip=request.remote_addr,
            user_agent=request.user_agent.string
        )
        return response

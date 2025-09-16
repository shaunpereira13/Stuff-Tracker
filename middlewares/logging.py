import logging
import time
from fastapi import Request

logger = logging.getLogger("uvicorn")

async def log_incoming_requests(request: Request, call_next):
    logger.info(f"INCOMING REQUEST | {request.method} {request.url.path} | From: {request.client.host}")
    
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000

    logger.info(f"RESPONSE SENT | {request.method} {request.url.path} | Status: {response.status_code} | Time: {duration:.2f}ms")
    return response
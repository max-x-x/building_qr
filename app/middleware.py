import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования HTTP запросов"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Логируем входящий запрос
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.info(
            f"Входящий запрос: {request.method} {request.url.path} "
            f"от {client_ip} (User-Agent: {user_agent})"
        )
        
        # Обрабатываем запрос
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Логируем успешный ответ
            logger.info(
                f"Ответ: {request.method} {request.url.path} -> "
                f"{response.status_code} [{process_time:.3f}s]"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Логируем ошибку
            logger.error(
                f"Ошибка в запросе: {request.method} {request.url.path} -> "
                f"Exception: {str(e)} [{process_time:.3f}s]",
                exc_info=True
            )
            
            raise

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления заголовков безопасности"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Добавляем заголовки безопасности
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления уникального ID к каждому запросу"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import uuid
        request_id = str(uuid.uuid4())
        
        # Добавляем request_id в заголовки ответа
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        # Логируем с request_id
        logger.info(f"Request ID: {request_id} - {request.method} {request.url.path}")
        
        return response

class CORSMiddleware(BaseHTTPMiddleware):
    """Middleware для обработки CORS запросов"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Обрабатываем OPTIONS запросы
        if request.method == "OPTIONS":
            response = Response(status_code=200)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        
        response = await call_next(request)
        
        # Добавляем CORS заголовки к ответу
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response

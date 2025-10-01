from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Union

class Settings(BaseSettings):
    load_dotenv()
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "QR Code API")
    API_V1_STR: str = "/api/v1"
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin")
    ALLOWED_ORIGINS: Union[List[str], str] = Field(default=["*"], description="Разрешенные источники для CORS")
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            if v.strip() == "":
                return ["*"]
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Настройки базы данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/qr_code_db")
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "False").lower() == "true"
    
    # Настройки API
    API_DOMAIN: str = os.getenv("API_DOMAIN", "localhost")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8002")
    
    # Настройки логирования
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

settings = Settings()

def setup_logging():
    """Настройка логгера с записью в файл"""
    # Создаем директорию для логов
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Настройка форматирования
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Настройка файлового хендлера с ротацией
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Настройка консольного хендлера
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Настройка логгера для FastAPI
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(logging.INFO)
    
    # Настройка логгера для uvicorn
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.INFO)
    
    return root_logger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from .config import settings, setup_logging
from .middleware import LoggingMiddleware, SecurityHeadersMiddleware, RequestIDMiddleware
from .routers import location, login, photo, sessions
from .database import create_tables

# Настройка логирования
setup_logging()

# --- инициализация приложения ---
app = FastAPI(title=settings.PROJECT_NAME)

# Создание таблиц в базе данных
create_tables()

# Планировщик задач
scheduler = AsyncIOScheduler()

async def auto_create_daily_sessions():
    """Автоматическое создание посещений для прорабов"""
    try:
        from .api import APIClient
        from .database import get_db
        from .models import Session as SessionModel, UserRole
        from datetime import datetime, timedelta
        
        # Получаем сессию базы данных
        db = next(get_db())
        
        try:
            # Логинимся как админ через нашу ручку логина
            api_client = APIClient()
            admin_response = api_client.login("admin@gmail.com", "111")
            
            if not admin_response.get("access"):
                # Если админ не может войти, создаем запись для него
                admin_session = SessionModel(
                    user_id="96a96730-2116-4425-add5-e9f2a3f302d1",  # ID админа
                    user_role=UserRole.FOREMAN,
                    object_id=1,
                    visit_date=datetime.now()
                )
                db.add(admin_session)
                db.commit()
                
                # Повторно пытаемся войти
                admin_response = api_client.login("admin@gmail.com", "111")
                
                if not admin_response.get("access"):
                    print("Ошибка авторизации админа для автоматического создания")
                    return
            
            token = admin_response.get("token")
            
            # Получаем список пользователей
            users_response = api_client.get_users(token)
            
            if users_response.get("status") != "success":
                print("Ошибка получения пользователей")
                return
            
            users = users_response.get("users", [])
            
            # Фильтруем только прорабов
            foremen = [user for user in users if user.get("role") == "foreman"]
            
            if not foremen:
                print("Прорабы не найдены для автоматического создания")
                return
            
            # Дата на завтра
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            created_sessions = 0
            
            # Создаем посещения для каждого прораба
            for foreman in foremen:
                try:
                    new_session = SessionModel(
                        user_id=foreman.get("id"),
                        user_role=UserRole.FOREMAN,
                        object_id=1,  # Дефолтный объект
                        visit_date=datetime.fromisoformat(tomorrow)
                    )
                    
                    db.add(new_session)
                    created_sessions += 1
                    
                except Exception as e:
                    print(f"Ошибка создания сессии для {foreman.get('id')}: {e}")
                    continue
            
            db.commit()
            print(f"Автоматически создано {created_sessions} посещений на {tomorrow}")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"Ошибка автоматического создания посещений: {e}")

# Настройка планировщика
scheduler.add_job(
    auto_create_daily_sessions,
    trigger=CronTrigger(hour=0, minute=0),  # Каждый день в 00:00
    id='daily_sessions',
    name='Ежедневное создание посещений',
    replace_existing=True
)

# Middleware для Request ID (должен быть первым)
app.add_middleware(RequestIDMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для безопасности
app.add_middleware(SecurityHeadersMiddleware)

# Middleware для логирования (должен быть последним)
app.add_middleware(LoggingMiddleware)

# Роуты
api_prefix = "/api/v1"
app.include_router(login.router, prefix=f"{api_prefix}/login", tags=["auth"])
app.include_router(location.router, prefix=f"{api_prefix}/location", tags=["location"])
app.include_router(photo.router, prefix=f"{api_prefix}/photo", tags=["photo"])
app.include_router(sessions.router, prefix=f"{api_prefix}/sessions", tags=["sessions"])


@app.get("/ping")
async def ping():
    from datetime import datetime
    return {
        "status": "success",
        "message": "API работает",
        "timestamp": datetime.now().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    """Запуск планировщика при старте приложения"""
    scheduler.start()
    print("Планировщик запущен")
    
    # Запускаем создание посещений при первом запуске
    await auto_create_daily_sessions()

@app.on_event("shutdown")
async def shutdown_event():
    """Остановка планировщика при выключении приложения"""
    scheduler.shutdown()
    print("Планировщик остановлен")



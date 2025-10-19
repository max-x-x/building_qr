from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings, setup_logging
from .database import create_tables
from .middleware import LoggingMiddleware, SecurityHeadersMiddleware, RequestIDMiddleware
from .routers import location, login, photo, sessions, session_history

setup_logging()

app = FastAPI(title=settings.PROJECT_NAME)
create_tables()
scheduler = AsyncIOScheduler()

async def auto_create_daily_sessions():
    try:
        from .api import APIClient
        from .database import get_db
        from .models import Session as SessionModel, UserRole
        
        db = next(get_db())
        
        try:
            api_client = APIClient()
            admin_response = api_client.login("admin@gmail.com", "111")
            
            if not admin_response.get("access"):
                admin_session = SessionModel(
                    user_id="96a96730-2116-4425-add5-e9f2a3f302d1",
                    user_role=UserRole.FOREMAN,
                    object_id=1,
                    area_name=None,
                    visit_date=datetime.now()
                )
                db.add(admin_session)
                db.commit()
                
                admin_response = api_client.login("admin@gmail.com", "111")
                
                if not admin_response.get("access"):
                    print("Ошибка авторизации админа для автоматического создания")
                    return
            
            token = admin_response.get("token")
            objects_response = api_client.get_objects(token)
            
            if objects_response.get("status") != "success":
                print("Ошибка получения объектов")
                return
            
            objects = objects_response.get("objects", [])
            active_objects = [obj for obj in objects if obj.get("status") == "active" and obj.get("foreman")]
            
            if not active_objects:
                print("Активные объекты с прорабами не найдены")
                return
            
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            created_sessions = 0
            
            for obj in active_objects:
                try:
                    foreman = obj.get("foreman")
                    if not foreman:
                        continue
                    
                    # Получаем детали объекта для получения полной информации о подполигонах
                    print(f"Получаем детали объекта {obj.get('id')}")
                    object_details = api_client.get_object_details(obj.get("id"), token)
                    if object_details.get("status") != "success":
                        print(f"Ошибка получения деталей объекта {obj.get('id')}: {object_details}")
                        continue
                        
                    obj_with_details = object_details.get("object", {})
                    areas = obj_with_details.get("areas", [])
                    print(f"Получены детали объекта {obj.get('id')}: {len(areas)} подполигонов")
                    print(f"Объект {obj.get('id')}: найдено {len(areas)} полигонов")
                    if not areas:
                        # Если нет полигонов, создаем посещение только на объект
                        print(f"Создаем посещение для объекта {obj.get('id')} без полигона")
                        new_session = SessionModel(
                            user_id=foreman.get("id"),
                            user_role=UserRole.FOREMAN,
                            object_id=obj.get("id"),
                            area_id=None,
                            area_name=None,
                            visit_date=datetime.fromisoformat(tomorrow)
                        )
                        db.add(new_session)
                        created_sessions += 1
                    else:
                        # Создаем посещение для каждого полигона
                        print(f"Создаем посещения для объекта {obj.get('id')} с {len(areas)} полигонами")
                        for area in areas:
                            print(f"  - Полигон ID: {area.get('id')}")
                            new_session = SessionModel(
                                user_id=foreman.get("id"),
                                user_role=UserRole.FOREMAN,
                                object_id=obj.get("id"),
                                area_id=area.get("id"),
                                area_name=area.get("name"),
                                visit_date=datetime.fromisoformat(tomorrow)
                            )
                            db.add(new_session)
                            created_sessions += 1
                    
                except Exception as e:
                    print(f"Ошибка создания сессии для объекта {obj.get('id')}: {e}")
                    continue
            
            db.commit()
            print(f"Автоматически создано {created_sessions} посещений на {tomorrow} для {len(active_objects)} объектов")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"Ошибка автоматического создания посещений: {e}")

scheduler.add_job(
    auto_create_daily_sessions,
    trigger=CronTrigger(hour=0, minute=0),
    id='daily_sessions',
    name='Ежедневное создание посещений',
    replace_existing=True
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)

api_prefix = "/api/v1"
app.include_router(login.router, prefix=f"{api_prefix}/login", tags=["auth"])
app.include_router(location.router, prefix=f"{api_prefix}/location", tags=["location"])
app.include_router(photo.router, prefix=f"{api_prefix}/photo", tags=["photo"])
app.include_router(sessions.router, prefix=f"{api_prefix}/sessions", tags=["sessions"])
app.include_router(session_history.router, prefix=f"{api_prefix}/session-history", tags=["session-history"])

@app.get("/ping")
async def ping():
    return {
        "status": "success",
        "message": "API работает",
        "timestamp": datetime.now().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    scheduler.start()
    print("Планировщик запущен")
    await auto_create_daily_sessions()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Планировщик остановлен")



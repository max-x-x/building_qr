from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from ..database import get_db
from ..models import Session as SessionModel, UserRole

router = APIRouter()

class SessionCreateRequest(BaseModel):
    user_id: str
    user_role: str
    object_id: int
    visit_date: str = None

class SessionCreateResponse(BaseModel):
    status: str
    message: str
    session_id: int

@router.post("/create", response_model=SessionCreateResponse)
async def create_session(
    session_data: SessionCreateRequest,
    db: Session = Depends(get_db)
):
    try:
        try:
            role_enum = UserRole(session_data.user_role)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Неверная роль. Доступные роли: {[role.value for role in UserRole]}"
            )
        
        if session_data.visit_date:
            try:
                visit_date = datetime.fromisoformat(session_data.visit_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Неверный формат даты. Используйте формат YYYY-MM-DD"
                )
        else:
            visit_date = datetime.now()
        
        new_session = SessionModel(
            user_id=session_data.user_id,
            user_role=role_enum,
            object_id=session_data.object_id,
            visit_date=visit_date
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return SessionCreateResponse(
            status="success",
            message="Запись посещения создана",
            session_id=new_session.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания записи: {str(e)}")

@router.get("/list")
async def list_sessions(
    user_id: str = None,
    object_id: int = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(SessionModel)
        
        if user_id:
            query = query.filter(SessionModel.user_id == user_id)
        if object_id:
            query = query.filter(SessionModel.object_id == object_id)
        
        sessions = query.order_by(SessionModel.visit_date.desc()).all()
        
        return {
            "status": "success",
            "sessions": [
                {
                    "id": session.id,
                    "user_id": session.user_id,
                    "user_role": session.user_role.value,
                    "object_id": session.object_id,
                    "visit_date": session.visit_date.isoformat()
                }
                for session in sessions
            ],
            "total": len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения записей: {str(e)}")

@router.get("/planned/{object_id}")
async def get_planned_visits(
    object_id: int,
    db: Session = Depends(get_db)
):
    try:
        sessions = db.query(SessionModel).filter(
            SessionModel.object_id == object_id
        ).order_by(SessionModel.visit_date.asc()).all()
        
        visits_by_date = {}
        for session in sessions:
            visit_date = session.visit_date.date()
            if visit_date not in visits_by_date:
                visits_by_date[visit_date] = []
            
            visits_by_date[visit_date].append({
                "id": session.id,
                "user_id": session.user_id,
                "user_role": session.user_role.value,
                "visit_time": session.visit_date.time().isoformat(),
                "visit_datetime": session.visit_date.isoformat()
            })
        
        planned_visits = []
        for visit_date, visits in visits_by_date.items():
            planned_visits.append({
                "date": visit_date.isoformat(),
                "visits_count": len(visits),
                "visits": visits
            })
        
        return {
            "status": "success",
            "object_id": object_id,
            "planned_visits": planned_visits,
            "total_visits": len(sessions),
            "total_days": len(visits_by_date)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения запланированных посещений: {str(e)}")

@router.post("/auto-create")
async def auto_create_sessions(db: Session = Depends(get_db)):
    try:
        from ..api import APIClient
        
        api_client = APIClient()
        admin_response = api_client.login("admin@gmail.com", "111")
        
        if not admin_response.get("access"):
            admin_session = SessionModel(
                user_id="96a96730-2116-4425-add5-e9f2a3f302d1",
                user_role=UserRole.FOREMAN,
                object_id=1,
                visit_date=datetime.now()
            )
            db.add(admin_session)
            db.commit()
            
            admin_response = api_client.login("admin@gmail.com", "111")
            
            if not admin_response.get("access"):
                raise HTTPException(status_code=401, detail="Ошибка авторизации админа")
        
        token = admin_response.get("token")
        users_response = api_client.get_users(token)
        
        if users_response.get("status") != "success":
            raise HTTPException(status_code=500, detail="Ошибка получения пользователей")
        
        users = users_response.get("users", [])
        foremen = [user for user in users if user.get("role") == "foreman"]
        
        if not foremen:
            return {
                "status": "success",
                "message": "Прорабы не найдены",
                "created_sessions": 0
            }
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        created_sessions = 0
        
        for foreman in foremen:
            try:
                new_session = SessionModel(
                    user_id=foreman.get("id"),
                    user_role=UserRole.FOREMAN,
                    object_id=1,
                    visit_date=datetime.fromisoformat(tomorrow)
                )
                
                db.add(new_session)
                created_sessions += 1
                
            except Exception as e:
                print(f"Ошибка создания сессии для {foreman.get('id')}: {e}")
                continue
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Создано {created_sessions} посещений на {tomorrow}",
            "created_sessions": created_sessions,
            "foremen_count": len(foremen)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка автоматического создания: {str(e)}")

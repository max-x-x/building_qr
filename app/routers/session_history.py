from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models import SessionHistory

router = APIRouter()

class SessionHistoryCreateRequest(BaseModel):
    user_id: str
    object_id: int
    sub_polygon_id: int = None
    latitude: float
    longitude: float

class SessionHistoryCreateResponse(BaseModel):
    status: str
    message: str
    history_id: int

@router.post("/create", response_model=SessionHistoryCreateResponse)
async def create_session_history(
    history_data: SessionHistoryCreateRequest,
    db: Session = Depends(get_db)
):
    try:
        new_history = SessionHistory(
            user_id=history_data.user_id,
            object_id=history_data.object_id,
            sub_polygon_id=history_data.sub_polygon_id,
            latitude=history_data.latitude,
            longitude=history_data.longitude
        )
        
        db.add(new_history)
        db.commit()
        db.refresh(new_history)
        
        return SessionHistoryCreateResponse(
            status="success",
            message="Запись истории посещения создана",
            history_id=new_history.id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания записи истории: {str(e)}")

@router.get("/list")
async def get_session_history(
    user_id: str = None,
    object_id: int = None,
    sub_polygon_id: int = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(SessionHistory)
        
        if user_id:
            query = query.filter(SessionHistory.user_id == user_id)
        if object_id:
            query = query.filter(SessionHistory.object_id == object_id)
        if sub_polygon_id:
            query = query.filter(SessionHistory.sub_polygon_id == sub_polygon_id)
        
        history = query.order_by(SessionHistory.date.desc()).all()
        
        return {
            "status": "success",
            "history": [
                {
                    "id": record.id,
                    "user_id": record.user_id,
                    "object_id": record.object_id,
                    "sub_polygon_id": record.sub_polygon_id,
                    "date": record.date.isoformat(),
                    "latitude": record.latitude,
                    "longitude": record.longitude
                }
                for record in history
            ],
            "total": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения истории посещений: {str(e)}")

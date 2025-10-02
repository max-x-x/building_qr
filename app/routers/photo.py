import base64
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import APIClient
from app.database import get_db
from app.models import Session as SessionModel

router = APIRouter()

class PhotoUploadRequest(BaseModel):
    token: str
    photos_base64: list[str]

class PhotoUploadResponse(BaseModel):
    status: str
    message: str

@router.post("/upload", response_model=PhotoUploadResponse)
async def upload_photo(request: PhotoUploadRequest, db: Session = Depends(get_db)):
    try:
        if not request.photos_base64:
            raise HTTPException(status_code=400, detail="Base64 изображения не предоставлены")
        
        if not request.token:
            raise HTTPException(status_code=401, detail="Токен не предоставлен")
        
        for photo in request.photos_base64:
            try:
                base64.b64decode(photo)
            except Exception:
                raise HTTPException(
                    status_code=400, 
                    detail="Неверный формат base64"
                )
        
        api_client = APIClient()
        user_response = api_client.get_user_me(request.token)
        
        if user_response["status"] != "success":
            raise HTTPException(
                status_code=401, 
                detail="Ошибка получения данных пользователя"
            )
        
        user_data = user_response["user"]
        user_id = user_data.get("id")
        role = user_data.get("role")
        
        if not user_id or not role:
            raise HTTPException(
                status_code=400, 
                detail="Неполные данные пользователя"
            )
        
        today = date.today()
        start = datetime.combine(today, datetime.min.time())
        end = start.replace(hour=23, minute=59, second=59)
        
        session = db.query(SessionModel).filter(
            SessionModel.user_id == user_id,
            SessionModel.visit_date >= start,
            SessionModel.visit_date <= end
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=400, 
                detail="Нет активной сессии на сегодня"
            )
        
        object_id = session.object_id
        today_str = today.strftime("%Y-%m-%d")
        
        photos_data = {
            "photos_base64": request.photos_base64,
            "date": today_str
        }
        
        if role == "foreman":
            result = api_client.upload_photos_foreman(user_id, photos_data, request.token)
        else:
            role_mapping = {
                "ssk": "ССК",
                "iko": "ИКО"
            }
            tag = role_mapping.get(role, role.upper())
            
            result = api_client.upload_photos_violation(
                tag,
                object_id,
                photos_data,
                request.token
            )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=400, 
                detail=result["message"]
            )
        
        return PhotoUploadResponse(
            status="success",
            message=result["message"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


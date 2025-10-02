import base64
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api import APIClient

router = APIRouter()

class PhotoUploadRequest(BaseModel):
    token: str
    object_id: int
    photos_base64: list[str]

class PhotoUploadResponse(BaseModel):
    status: str
    message: str

@router.post("/upload", response_model=PhotoUploadResponse)
async def upload_photo(request: PhotoUploadRequest):
    try:
        if not request.photos_base64:
            raise HTTPException(status_code=400, detail="Base64 изображения не предоставлены")
        
        if not request.token:
            raise HTTPException(status_code=401, detail="Токен не предоставлен")
        
        if not request.object_id:
            raise HTTPException(status_code=400, detail="ID объекта не указан")
        
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
                request.object_id,
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

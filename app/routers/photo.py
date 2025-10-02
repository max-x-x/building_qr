from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import base64
from app.api import APIClient

router = APIRouter()

class PhotoUploadRequest(BaseModel):
    token: str
    role: str
    uuid: str
    tag: Optional[str] = None
    object_id: Optional[int] = None
    photos_base64: list[str]
    date: str

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
        
        if not request.role:
            raise HTTPException(status_code=400, detail="Роль не указана")
        
        if not request.uuid:
            raise HTTPException(status_code=400, detail="UUID не указан")
        
        for photo in request.photos_base64:
            try:
                base64.b64decode(photo)
            except Exception:
                raise HTTPException(status_code=400, detail="Неверный формат base64")
        
        api_client = APIClient()
        photos_data = {
            "photos_base64": request.photos_base64,
            "date": request.date
        }
        
        if request.role == "foreman":
            result = api_client.upload_photos_foreman(request.uuid, photos_data, request.token)
        else:
            if not request.tag:
                raise HTTPException(status_code=400, detail="Тег не указан для роли, отличной от foreman")
            if not request.object_id:
                raise HTTPException(status_code=400, detail="ID объекта не указан для роли, отличной от foreman")
            
            result = api_client.upload_photos_violation(
                request.tag, 
                request.object_id, 
                photos_data, 
                request.token
            )
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return PhotoUploadResponse(
            status="success",
            message=result["message"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


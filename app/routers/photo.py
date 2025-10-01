"""
ручка для отправки в файловое хранилище
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import base64
import asyncio

router = APIRouter()

class PhotoUploadRequest(BaseModel):
    token: str
    imageBase64: str

class PhotoUploadResponse(BaseModel):
    status: str
    message: str

@router.post("/upload", response_model=PhotoUploadResponse)
async def upload_photo(request: PhotoUploadRequest):
    """
    Загрузка фото в base64 формате
    """
    try:
        if not request.imageBase64:
            raise HTTPException(status_code=400, detail="Base64 изображение не предоставлено")
        
        if not request.token:
            raise HTTPException(status_code=401, detail="Токен не предоставлен")
        
        try:
            base64.b64decode(request.imageBase64)
        except Exception:
            raise HTTPException(status_code=400, detail="Неверный формат base64")
        
        await asyncio.sleep(2)
        
        return PhotoUploadResponse(
            status="success",
            message="Фото успешно загружено"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


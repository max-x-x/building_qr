import logging
from typing import Dict, Any

import requests

from app.config import settings

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.API_BASE_URL
        self.session = requests.Session()

    def login(self, email: str, password: str) -> Dict[str, Any]:
        try:
            response = self.session.post(
                "https://building-api.itc-hub.ru/api/v1/auth/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get("user", {})
                role = user_data.get("role", "")
                
                role_mapping = {
                    "foreman": "1",
                    "ssk": "2",
                    "iko": "3",
                    "admin": "1"
                }
                
                return {
                    "status": "success",
                    "access": True,
                    "token": data.get("access"),
                    "user_id": user_data.get("id"),
                    "role": role,
                    "message": "Вход выполнен успешно"
                }
            else:
                return {
                    "status": "error",
                    "access": False,
                    "message": "Неверные учетные данные"
                }
        except Exception as e:
            return {
                "status": "error",
                "access": False,
                "message": f"Ошибка подключения: {str(e)}"
            }

    def get_users(self, token: str) -> Dict[str, Any]:
        try:
            response = self.session.get(
                "https://building-api.itc-hub.ru/api/v1/users",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "users": data.get("items", []),
                    "message": "Пользователи получены"
                }
            else:
                return {
                    "status": "error",
                    "message": "Ошибка получения пользователей"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка подключения: {str(e)}"
            }

    def get_user_me(self, token: str) -> Dict[str, Any]:
        try:
            response = self.session.get(
                "https://building-api.itc-hub.ru/api/v1/users/me",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "user": data,
                    "message": "Данные пользователя получены"
                }
            else:
                return {
                    "status": "error",
                    "message": "Ошибка получения данных пользователя"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка подключения: {str(e)}"
            }

    def get_poligon(self, object_id: int, token: str = None):
        try:
            response = requests.get(
                f"https://building-api.itc-hub.ru/api/v1/objects/{object_id}",
                headers={
                    "Authorization": f"Bearer {token}" if token else "",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                main_polygon = data.get("main_polygon", {})
                
                if main_polygon:
                    geometry = main_polygon.get("geometry", {})
                    coordinates = geometry.get("coordinates", [])
                    
                    if coordinates and len(coordinates) > 0:
                        polygon_coords = coordinates[0]
                        return polygon_coords
                
                return None
            else:
                return None
        except Exception as e:
            print(f"Ошибка получения полигона: {e}")
            return None

    def upload_photos_foreman(self, foreman_id: str, photos_data: dict, token: str) -> Dict[str, Any]:
        try:
            response = self.session.post(
                f"https://building-s3-api.itc-hub.ru/upload/foreman/visit/{foreman_id}",
                json=photos_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "Фото успешно загружены для прораба"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Ошибка загрузки фото: {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка подключения: {str(e)}"
            }

    def get_objects(self, token: str) -> Dict[str, Any]:
        try:
            response = self.session.get(
                "https://building-api.itc-hub.ru/api/v1/objects",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "objects": data.get("items", []),
                    "message": "Объекты получены"
                }
            else:
                return {
                    "status": "error",
                    "message": "Ошибка получения объектов"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка подключения: {str(e)}"
            }

    def get_object_details(self, object_id: int, token: str) -> Dict[str, Any]:
        try:
            response = self.session.get(
                f"https://building-api.itc-hub.ru/api/v1/objects/{object_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "object": data,
                    "message": "Детали объекта получены"
                }
            else:
                return {
                    "status": "error",
                    "message": "Ошибка получения деталей объекта"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка подключения: {str(e)}"
            }

    def upload_photos_violation(self, tag: str, entity_id: int, photos_data: dict, token: str) -> Dict[str, Any]:
        role_mapping = {
            "ssk": "ССК",
            "iko": "ИКО"
        }
        
        russian_tag = role_mapping.get(tag.lower(), tag)
        
        try:
            response = self.session.post(
                f"https://building-s3-api.itc-hub.ru/upload/violation/{russian_tag}/{entity_id}/creation",
                json=photos_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": f"Фото успешно загружены для {tag}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Ошибка загрузки фото: {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка подключения: {str(e)}"
            }

import requests
import logging
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class APIClient:
    """Клиент для работы с API"""

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
                
                # Маппинг ролей с внешнего API на внутренние
                role_mapping = {
                    "foreman": "1",  # PRORAB
                    "ssk": "2",      # SSK
                    "iko": "3",      # IKO
                    "admin": "1"     # Админ как прораб
                }
                
                return {
                    "status": "success",
                    "access": True,
                    "token": data.get("access"),
                    "user_id": user_data.get("id"),
                    "role": role,  # Возвращаем оригинальное название роли
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

    def get_poligon(self, object_id: int, token: str = None):
        """
        принимает айди объенкта отдает полигон объекта
        :param object_id:
        :param token:
        :return:
        """
        try:
            response = self.session.get(
                "https://building-api.itc-hub.ru/api/v1/areas/list",
                headers={
                    "Authorization": f"Bearer {token}" if token else "",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                areas = data.get("items", [])
                
                # Ищем полигон с нужным id (object_id соответствует id полигона)
                for area in areas:
                    if area.get("id") == object_id:
                        geometry = area.get("geometry", {})
                        coordinates = geometry.get("coordinates", [])
                        
                        if coordinates and len(coordinates) > 0:
                            # Извлекаем координаты полигона
                            polygon_coords = coordinates[0]  # Первый массив координат
                            # Конвертируем из [longitude, latitude] в [latitude, longitude]
                            return [[coord[1], coord[0]] for coord in polygon_coords]
                
                return None
            else:
                return None
        except Exception as e:
            print(f"Ошибка получения полигона: {e}")
            return None
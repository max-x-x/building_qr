#!/usr/bin/env python3
"""
Скрипт для тестирования всех ручек API
"""

import requests
import json
import base64
from typing import Dict, Any

class APITester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None

    def print_response(self, endpoint: str, method: str, response: requests.Response):
        """Выводит полный ответ от ручки"""
        print(f"\n{'='*60}")
        print(f"ЭНДПОИНТ: {method} {endpoint}")
        print(f"СТАТУС КОД: {response.status_code}")
        print(f"ЗАГОЛОВКИ:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\nТЕЛО ОТВЕТА:")
        try:
            json_data = response.json()
            print(json.dumps(json_data, indent=2, ensure_ascii=False))
        except:
            print(response.text)
        print(f"{'='*60}")

    def test_health_check(self):
        """Тестирует health check"""
        print("\n🔍 Тестирование health check...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            self.print_response("/health", "GET", response)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка при тестировании health check: {e}")
            return False

    def test_login(self):
        """Тестирует авторизацию"""
        print("\n🔐 Тестирование авторизации...")
        try:
            login_data = {
                "email": "admin@admin.admin",
                "password": "admin"
            }
            response = self.session.post(f"{self.base_url}/api/v1/login/login", json=login_data)
            self.print_response("/api/v1/login/login", "POST", response)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                if self.token:
                    print(f"✅ Токен получен: {self.token[:20]}...")
                return True
            return False
        except Exception as e:
            print(f"❌ Ошибка при тестировании авторизации: {e}")
            return False

    def test_location(self):
        """Тестирует отправку геолокации"""
        print("\n📍 Тестирование отправки геолокации...")
        if not self.token:
            print("❌ Нет токена для тестирования геолокации")
            return False
        
        try:
            location_data = {
                "token": self.token,
                "latitude": 55.7558,
                "longitude": 37.6176,
                "object_id": 1
            }
            response = self.session.post(f"{self.base_url}/api/v1/location/", json=location_data)
            self.print_response("/api/v1/location/", "POST", response)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка при тестировании геолокации: {e}")
            return False

    def test_photo_upload(self):
        """Тестирует загрузку фото"""
        print("\n📸 Тестирование загрузки фото...")
        if not self.token:
            print("❌ Нет токена для тестирования загрузки фото")
            return False
        
        try:
            # Создаем тестовое base64 изображение (1x1 пиксель PNG)
            test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            photo_data = {
                "token": self.token,
                "imageBase64": test_image_base64
            }
            response = self.session.post(f"{self.base_url}/api/v1/photo/upload", json=photo_data)
            self.print_response("/api/v1/photo/upload", "POST", response)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка при тестировании загрузки фото: {e}")
            return False

    def test_ping(self):
        """Тестирует ping ручку"""
        print("\n🏓 Тестирование ping...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/ping/")
            self.print_response("/api/v1/ping/", "GET", response)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка при тестировании ping: {e}")
            return False

    def test_create_session(self):
        """Тестирует создание записи посещения"""
        print("\n📝 Тестирование создания записи посещения...")
        try:
            session_data = {
                "user_id": 123,
                "user_role": "1",
                "object_id": 456
            }
            response = self.session.post(f"{self.base_url}/api/v1/sessions/create", json=session_data)
            self.print_response("/api/v1/sessions/create", "POST", response)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка при тестировании создания записи: {e}")
            return False

    def test_list_sessions(self):
        """Тестирует получение списка посещений"""
        print("\n📋 Тестирование получения списка посещений...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/sessions/list")
            self.print_response("/api/v1/sessions/list", "GET", response)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка при тестировании списка посещений: {e}")
            return False

    def test_planned_visits(self):
        """Тестирует получение запланированных посещений на объект"""
        print("\n📅 Тестирование получения запланированных посещений...")
        try:
            object_id = 456  # Используем тот же object_id, что и в тесте создания
            response = self.session.get(f"{self.base_url}/api/v1/sessions/planned/{object_id}")
            self.print_response(f"/api/v1/sessions/planned/{object_id}", "GET", response)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка при тестировании запланированных посещений: {e}")
            return False

    def run_all_tests(self):
        """Запускает все тесты"""
        print("🚀 Запуск тестирования всех ручек API")
        print(f"Базовый URL: {self.base_url}")
        
        results = {}
        
        # Тест 1: Health check
        results["health"] = self.test_health_check()
        
        # Тест 2: Сначала создаем посещение, потом авторизация
        results["create_session"] = self.test_create_session()
        results["login"] = self.test_login()
        
        # Тест 3: Геолокация (только если авторизация прошла)
        if results["login"]:
            results["location"] = self.test_location()
        else:
            print("\n⏭️ Пропуск теста геолокации - авторизация не прошла")
            results["location"] = False
        
        # Тест 4: Загрузка фото (только если авторизация прошла)
        if results["login"]:
            results["photo"] = self.test_photo_upload()
        else:
            print("\n⏭️ Пропуск теста загрузки фото - авторизация не прошла")
            results["photo"] = False

        # Тест 5: Ping
        results["ping"] = self.test_ping()

        # Тест 6: Ping
        # уже выше перенесено создание посещения

        # Тест 7: Получение списка посещений
        results["list_sessions"] = self.test_list_sessions()

        # Тест 8: Получение запланированных посещений на объект
        results["planned_visits"] = self.test_planned_visits()
        
        # Итоги
        print(f"\n{'='*60}")
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
        print(f"{'='*60}")
        for test_name, success in results.items():
            status = "✅ ПРОШЕЛ" if success else "❌ НЕ ПРОШЕЛ"
            print(f"{test_name.upper()}: {status}")
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        print(f"\nВсего тестов: {total_tests}")
        print(f"Прошло: {passed_tests}")
        print(f"Не прошло: {total_tests - passed_tests}")
        
        return results

if __name__ == "__main__":
    print("🧪 Запуск тестов API...")
    tester = APITester()
    results = tester.run_all_tests()
    
    if all(results.values()):
        print("\n✅ Все тесты прошли!")
    else:
        print("\n❌ Некоторые тесты не прошли!")

#!/usr/bin/env python3
"""
Тест автоматического создания посещений
"""

import requests
import json
from typing import Dict, Any


class AutoSessionsTester:
    def __init__(self, base_url: str = "http://localhost:8022"):
        self.base_url = base_url
        self.session = requests.Session()

    def print_response(self, endpoint: str, method: str, response: requests.Response):
        """Выводит полный ответ от ручки"""
        print(f"\n{'=' * 60}")
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
        print(f"{'=' * 60}")

    def test_auto_create_sessions(self):
        """Тестирует автоматическое создание посещений"""
        print("\n🤖 Тестирование автоматического создания посещений...")
        try:
            response = self.session.post(f"{self.base_url}/api/v1/sessions/auto-create")
            self.print_response("/api/v1/sessions/auto-create", "POST", response)

            if response.status_code == 200:
                data = response.json()
                created_sessions = data.get("created_sessions", 0)
                active_objects = data.get("active_objects_count", 0)

                print(f"\n✅ Успешно создано {created_sessions} посещений для {active_objects} объектов")
                return True
            else:
                print(f"\n❌ Ошибка создания посещений: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Ошибка при тестировании автоматического создания: {e}")
            return False

    def test_list_sessions_after_auto_create(self):
        """Тестирует получение списка посещений после автоматического создания"""
        print("\n📋 Тестирование получения списка посещений после автосоздания...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/sessions/list")
            self.print_response("/api/v1/sessions/list", "GET", response)

            if response.status_code == 200:
                data = response.json()
                sessions = data.get("sessions", [])
                total = data.get("total", 0)

                print(f"\n✅ Найдено {total} посещений в базе данных")

                # Показываем последние 5 посещений
                if sessions:
                    print("\nПоследние 5 посещений:")
                    for i, session in enumerate(sessions[:5]):
                        print(f"  {i + 1}. ID: {session.get('id')}, "
                              f"Пользователь: {session.get('user_id')}, "
                              f"Роль: {session.get('user_role')}, "
                              f"Объект: {session.get('object_id')}, "
                              f"Дата: {session.get('visit_date')}")

                return True
            else:
                print(f"\n❌ Ошибка получения списка посещений: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Ошибка при получении списка посещений: {e}")
            return False

    def test_ping(self):
        """Тестирует ping ручку"""
        print("\n🏓 Тестирование ping...")
        try:
            response = self.session.get(f"{self.base_url}/ping")
            self.print_response("/ping", "GET", response)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка при тестировании ping: {e}")
            return False

    def run_auto_sessions_test(self):
        """Запускает тест автоматического создания посещений"""
        print("🚀 Запуск тестирования автоматического создания посещений")
        print(f"Базовый URL: {self.base_url}")

        results = {}

        # Тест 1: Ping
        results["ping"] = self.test_ping()

        # Тест 2: Автоматическое создание посещений
        results["auto_create"] = self.test_auto_create_sessions()

        # Тест 3: Проверка списка посещений после создания
        results["list_sessions"] = self.test_list_sessions_after_auto_create()

        # Итоги
        print(f"\n{'=' * 60}")
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
        print(f"{'=' * 60}")
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
    print("🧪 Запуск теста автоматического создания посещений...")
    tester = AutoSessionsTester()
    results = tester.run_auto_sessions_test()

    if all(results.values()):
        print("\n✅ Все тесты прошли!")
    else:
        print("\n❌ Некоторые тесты не прошли!")

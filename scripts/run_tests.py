#!/usr/bin/env python3
"""
Скрипт для запуска тестов okama-bot
Предоставляет удобный интерфейс для запуска различных типов тестов
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Главная функция"""
    print("🧪 Okama-bot Test Runner")
    print("=" * 40)
    
    # Проверяем, что мы в правильной директории
    if not os.path.exists("bot.py"):
        print("❌ Ошибка: Запустите скрипт из корневой папки проекта")
        sys.exit(1)
    
    # Проверяем наличие тестов
    tests_dir = Path("tests")
    if not tests_dir.exists():
        print("❌ Ошибка: Папка tests не найдена")
        sys.exit(1)
    
    print("📁 Найдены тесты:")
    for test_file in tests_dir.glob("test_*.py"):
        print(f"   ✅ {test_file.name}")
    
    print("\n🚀 Запуск быстрых тестов...")
    
    try:
        # Запускаем быстрые тесты
        result = subprocess.run([
            sys.executable, 
            "tests/test_runner.py", 
            "--quick"
        ], cwd=os.getcwd())
        
        if result.returncode == 0:
            print("\n🎉 Все тесты пройдены успешно!")
        else:
            print("\n❌ Некоторые тесты провалены")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Ошибка при запуске тестов: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

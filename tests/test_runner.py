#!/usr/bin/env python3
"""
Запускатор тестов для okama-bot
Предоставляет удобный интерфейс для запуска различных типов тестов
"""

import sys
import os
import argparse
import subprocess
import time
from datetime import datetime
from typing import List, Dict, Any

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_utilities import TestReporter, TestRunner


class TestSuiteRunner:
    """Запускатор набора тестов"""
    
    def __init__(self):
        self.reporter = TestReporter()
        self.test_modules = {
            'comprehensive': 'test_comprehensive_regression',
            'simple': 'test_simple_regression',
            'portfolio_risk': 'test_portfolio_risk_metrics_fix',
            'additional_metrics': 'test_additional_metrics_calculation',
            'hk_comparison': 'test_hk_comparison_debug',
            'test_command': 'test_test_command'
        }
    
    def run_single_test(self, test_module: str, verbose: bool = False) -> bool:
        """Запускает один тестовый модуль"""
        if test_module not in self.test_modules:
            print(f"❌ Неизвестный тестовый модуль: {test_module}")
            return False
        
        module_name = self.test_modules[test_module]
        test_file = f"tests/{module_name}.py"
        
        if not os.path.exists(test_file):
            print(f"❌ Файл теста не найден: {test_file}")
            return False
        
        print(f"🧪 Запуск теста: {test_module}")
        print(f"📁 Файл: {test_file}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Запускаем тест через subprocess
            cmd = [sys.executable, test_file]
            if verbose:
                cmd.append('-v')
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print("✅ Тест завершен успешно")
                self.reporter.add_test_result(test_module, "passed", duration=duration)
                return True
            else:
                print("❌ Тест провален")
                print(f"Ошибка: {result.stderr}")
                self.reporter.add_test_result(test_module, "failed", result.stderr, duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Ошибка при запуске теста: {e}")
            self.reporter.add_test_result(test_module, "failed", str(e), duration)
            return False
    
    def run_all_tests(self, verbose: bool = False) -> bool:
        """Запускает все тесты"""
        self.reporter.start_test_suite()
        
        all_passed = True
        
        for test_module in self.test_modules.keys():
            success = self.run_single_test(test_module, verbose)
            if not success:
                all_passed = False
            print()  # Пустая строка между тестами
        
        self.reporter.end_test_suite()
        return all_passed
    
    def run_regression_tests(self, verbose: bool = False) -> bool:
        """Запускает только регрессионные тесты"""
        self.reporter.start_test_suite()
        
        regression_tests = ['comprehensive', 'portfolio_risk', 'additional_metrics']
        all_passed = True
        
        for test_module in regression_tests:
            success = self.run_single_test(test_module, verbose)
            if not success:
                all_passed = False
            print()
        
        self.reporter.end_test_suite()
        return all_passed
    
    def run_quick_tests(self, verbose: bool = False) -> bool:
        """Запускает быстрые тесты"""
        self.reporter.start_test_suite()
        
        quick_tests = ['comprehensive']  # Только основной регрессионный тест
        all_passed = True
        
        for test_module in quick_tests:
            success = self.run_single_test(test_module, verbose)
            if not success:
                all_passed = False
            print()
        
        self.reporter.end_test_suite()
        return all_passed
    
    def list_available_tests(self):
        """Показывает доступные тесты"""
        print("📋 Доступные тесты:")
        print("-" * 30)
        
        for key, module in self.test_modules.items():
            test_file = f"tests/{module}.py"
            exists = "✅" if os.path.exists(test_file) else "❌"
            print(f"{exists} {key:15} - {module}")
        
        print()
        print("💡 Использование:")
        print("  python tests/test_runner.py --test comprehensive")
        print("  python tests/test_runner.py --all")
        print("  python tests/test_runner.py --regression")
        print("  python tests/test_runner.py --quick")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Запускатор тестов для okama-bot')
    parser.add_argument('--test', choices=['comprehensive', 'simple', 'portfolio_risk', 'additional_metrics', 'hk_comparison', 'test_command'],
                       help='Запустить конкретный тест')
    parser.add_argument('--all', action='store_true', help='Запустить все тесты')
    parser.add_argument('--regression', action='store_true', help='Запустить регрессионные тесты')
    parser.add_argument('--quick', action='store_true', help='Запустить быстрые тесты')
    parser.add_argument('--simple', action='store_true', help='Запустить простые тесты')
    parser.add_argument('--list', action='store_true', help='Показать доступные тесты')
    parser.add_argument('--verbose', '-v', action='store_true', help='Подробный вывод')
    
    args = parser.parse_args()
    
    runner = TestSuiteRunner()
    
    if args.list:
        runner.list_available_tests()
        return
    
    if args.test:
        success = runner.run_single_test(args.test, args.verbose)
        sys.exit(0 if success else 1)
    
    elif args.all:
        success = runner.run_all_tests(args.verbose)
        sys.exit(0 if success else 1)
    
    elif args.regression:
        success = runner.run_regression_tests(args.verbose)
        sys.exit(0 if success else 1)
    
    elif args.quick:
        success = runner.run_quick_tests(args.verbose)
        sys.exit(0 if success else 1)
    
    elif args.simple:
        success = runner.run_single_test('simple', args.verbose)
        sys.exit(0 if success else 1)
    
    else:
        # По умолчанию запускаем простые тесты
        print("🚀 Запуск простых тестов по умолчанию...")
        success = runner.run_single_test('simple', args.verbose)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

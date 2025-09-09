#!/usr/bin/env python3
"""
Тест для команды /test в боте
"""

import unittest
import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestTestCommand(unittest.TestCase):
    """Тест команды /test"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.bot = ShansAi()
        
        # Mock Telegram objects
        self.mock_update = Mock()
        self.mock_context = Mock()
        
        # Setup mock update
        self.mock_update.effective_user = Mock()
        self.mock_update.effective_user.id = 12345
        self.mock_update.effective_user.first_name = "TestUser"
        
        # Setup mock context
        self.mock_context.bot = Mock()
        self.mock_context.bot.send_message = AsyncMock()
        self.mock_context.args = []
    
    def test_test_command_without_args(self):
        """Тест команды /test без аргументов (должна использовать quick)"""
        async def run_test():
            with patch.object(self.bot, '_run_tests', new_callable=AsyncMock) as mock_run_tests:
                mock_run_tests.return_value = {
                    'success': True,
                    'stdout': 'Test passed',
                    'stderr': '',
                    'duration': 1.5,
                    'test_type': 'quick'
                }
                
                await self.bot.test_command(self.mock_update, self.mock_context)
                
                # Проверяем, что _run_tests была вызвана с 'quick'
                mock_run_tests.assert_called_once_with('quick')
                
                # Проверяем, что сообщение было отправлено
                self.mock_context.bot.send_message.assert_called()
                print("✅ Test command without args test passed")
        
        asyncio.run(run_test())
    
    def test_test_command_with_args(self):
        """Тест команды /test с аргументами"""
        async def run_test():
            # Тест с аргументом 'all'
            self.mock_context.args = ['all']
            
            with patch.object(self.bot, '_run_tests', new_callable=AsyncMock) as mock_run_tests:
                mock_run_tests.return_value = {
                    'success': True,
                    'stdout': 'All tests passed',
                    'stderr': '',
                    'duration': 5.0,
                    'test_type': 'all'
                }
                
                await self.bot.test_command(self.mock_update, self.mock_context)
                
                # Проверяем, что _run_tests была вызвана с 'all'
                mock_run_tests.assert_called_once_with('all')
                print("✅ Test command with 'all' arg test passed")
        
        asyncio.run(run_test())
    
    def test_test_command_invalid_arg(self):
        """Тест команды /test с неверным аргументом (должен использовать quick)"""
        async def run_test():
            # Тест с неверным аргументом
            self.mock_context.args = ['invalid']
            
            with patch.object(self.bot, '_run_tests', new_callable=AsyncMock) as mock_run_tests:
                mock_run_tests.return_value = {
                    'success': True,
                    'stdout': 'Test passed',
                    'stderr': '',
                    'duration': 1.5,
                    'test_type': 'quick'
                }
                
                await self.bot.test_command(self.mock_update, self.mock_context)
                
                # Проверяем, что _run_tests была вызвана с 'quick' (fallback)
                mock_run_tests.assert_called_once_with('quick')
                print("✅ Test command with invalid arg test passed")
        
        asyncio.run(run_test())
    
    def test_run_tests_success(self):
        """Тест функции _run_tests при успешном выполнении"""
        async def run_test():
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout='Test passed\n',
                    stderr=''
                )
                
                result = await self.bot._run_tests('quick')
                
                self.assertTrue(result['success'])
                self.assertEqual(result['stdout'], 'Test passed\n')
                self.assertEqual(result['stderr'], '')
                self.assertEqual(result['test_type'], 'quick')
                self.assertGreater(result['duration'], 0)
                print("✅ Run tests success test passed")
        
        asyncio.run(run_test())
    
    def test_run_tests_failure(self):
        """Тест функции _run_tests при неудачном выполнении"""
        async def run_test():
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=1,
                    stdout='',
                    stderr='Test failed\n'
                )
                
                result = await self.bot._run_tests('quick')
                
                self.assertFalse(result['success'])
                self.assertEqual(result['stdout'], '')
                self.assertEqual(result['stderr'], 'Test failed\n')
                self.assertEqual(result['test_type'], 'quick')
                print("✅ Run tests failure test passed")
        
        asyncio.run(run_test())
    
    def test_run_tests_timeout(self):
        """Тест функции _run_tests при таймауте"""
        async def run_test():
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = Exception('Timeout')
                
                result = await self.bot._run_tests('quick')
                
                self.assertFalse(result['success'])
                self.assertIn('Timeout', result['stderr'])
                self.assertEqual(result['test_type'], 'quick')
                print("✅ Run tests timeout test passed")
        
        asyncio.run(run_test())
    
    def test_format_test_results_success(self):
        """Тест форматирования результатов при успехе"""
        result = {
            'success': True,
            'stdout': 'Test passed\nAll good',
            'stderr': '',
            'duration': 1.5,
            'test_type': 'quick'
        }
        
        formatted = self.bot._format_test_results(result, 'quick')
        
        self.assertIn('✅', formatted)
        self.assertIn('Пройдены', formatted)
        self.assertIn('quick', formatted)
        self.assertIn('1.5', formatted)
        self.assertIn('Test passed', formatted)
        print("✅ Format test results success test passed")
    
    def test_format_test_results_failure(self):
        """Тест форматирования результатов при неудаче"""
        result = {
            'success': False,
            'stdout': 'Some output',
            'stderr': 'Test failed\nError message',
            'duration': 2.0,
            'test_type': 'regression'
        }
        
        formatted = self.bot._format_test_results(result, 'regression')
        
        self.assertIn('❌', formatted)
        self.assertIn('Провалены', formatted)
        self.assertIn('regression', formatted)
        self.assertIn('2.0', formatted)
        self.assertIn('Test failed', formatted)
        self.assertIn('Error message', formatted)
        print("✅ Format test results failure test passed")
    
    def test_format_test_results_long_output(self):
        """Тест форматирования результатов с длинным выводом"""
        # Создаем длинный вывод
        long_output = '\n'.join([f'Line {i}' for i in range(50)])
        
        result = {
            'success': True,
            'stdout': long_output,
            'stderr': '',
            'duration': 1.0,
            'test_type': 'all'
        }
        
        formatted = self.bot._format_test_results(result, 'all')
        
        # Проверяем, что вывод был обрезан
        self.assertIn('Line 30', formatted)  # Должны быть последние строки
        self.assertNotIn('Line 0', formatted)  # Первые строки должны быть обрезаны
        print("✅ Format test results long output test passed")
    
    def test_format_test_results_message_length_limit(self):
        """Тест ограничения длины сообщения"""
        # Создаем очень длинный вывод
        very_long_output = 'A' * 5000
        
        result = {
            'success': True,
            'stdout': very_long_output,
            'stderr': '',
            'duration': 1.0,
            'test_type': 'comprehensive'
        }
        
        formatted = self.bot._format_test_results(result, 'comprehensive')
        
        # Проверяем, что сообщение было обрезано
        self.assertLess(len(formatted), 4000)
        self.assertIn('... (сообщение обрезано)', formatted)
        print("✅ Format test results message length limit test passed")


if __name__ == '__main__':
    print("🧪 Тестирование команды /test")
    unittest.main(verbosity=2)

"""
Test for info command context functionality
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path to import bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import OkamaFinanceBot


class TestInfoContext(unittest.TestCase):
    """Test class for info command context functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot = OkamaFinanceBot()
        
    def test_get_random_examples(self):
        """Test getting random examples from asset service"""
        examples = self.bot.asset_service.get_random_examples(3)
        
        # Check that we get the right number of examples
        self.assertEqual(len(examples), 3)
        
        # Check that all examples are strings
        for example in examples:
            self.assertIsInstance(example, str)
            
        # Check that examples contain dots (okama format)
        for example in examples:
            self.assertIn('.', example)
    
    def test_is_likely_asset_symbol(self):
        """Test asset symbol detection"""
        # Test valid symbols
        self.assertTrue(self.bot.asset_service.is_likely_asset_symbol('SBER.MOEX'))
        self.assertTrue(self.bot.asset_service.is_likely_asset_symbol('SPY.US'))
        self.assertTrue(self.bot.asset_service.is_likely_asset_symbol('AAPL'))
        self.assertTrue(self.bot.asset_service.is_likely_asset_symbol('SBER'))
        
        # Test ISIN codes
        self.assertTrue(self.bot.asset_service.is_likely_asset_symbol('US0378331005'))  # Apple ISIN
        self.assertTrue(self.bot.asset_service.is_likely_asset_symbol('RU0009029540'))  # Sberbank ISIN
        self.assertFalse(self.bot.asset_service.is_likely_asset_symbol('US037833100'))   # Too short
        self.assertFalse(self.bot.asset_service.is_likely_asset_symbol('US03783310055')) # Too long
        self.assertFalse(self.bot.asset_service.is_likely_asset_symbol('123456789012'))  # No letters at start
        
        # Test invalid symbols
        self.assertFalse(self.bot.asset_service.is_likely_asset_symbol(''))
        self.assertFalse(self.bot.asset_service.is_likely_asset_symbol('hello world'))
        self.assertFalse(self.bot.asset_service.is_likely_asset_symbol('123'))
        self.assertFalse(self.bot.asset_service.is_likely_asset_symbol('A' * 20))  # Too long
    
    def test_resolve_symbol_or_isin(self):
        """Test symbol resolution"""
        # Test already formatted symbols
        result = self.bot.asset_service.resolve_symbol_or_isin('SBER.MOEX')
        self.assertNotIn('error', result)
        self.assertEqual(result['symbol'], 'SBER.MOEX')
        
        # Test plain tickers
        result = self.bot.asset_service.resolve_symbol_or_isin('SBER')
        self.assertNotIn('error', result)
        
        # Test ISIN codes
        result = self.bot.asset_service.resolve_symbol_or_isin('US0378331005')  # Apple ISIN
        # Note: This might fail if okama.Asset.search is not available or no data
        # We just check that it doesn't crash
        self.assertIsInstance(result, dict)
        
        # Test invalid input
        result = self.bot.asset_service.resolve_symbol_or_isin('')
        self.assertIn('error', result)
    
    @patch('okama.Asset')
    def test_search_by_isin_direct_creation(self, mock_asset):
        """Test ISIN search via direct okama.Asset creation"""
        # Mock successful direct ISIN creation
        mock_asset.return_value = Mock()
        
        result = self.bot.asset_service.search_by_isin('RU0009029540')
        self.assertEqual(result, 'RU0009029540')
        
        # Test with exception in direct creation
        mock_asset.side_effect = Exception("Direct creation failed")
        result = self.bot.asset_service.search_by_isin('INVALID123')
        self.assertIsNone(result)

    @patch('okama.Asset.search')
    def test_search_by_isin_fallback(self, mock_search):
        """Test ISIN search fallback via okama.Asset.search"""
        # Mock successful search result
        mock_result = Mock()
        mock_result.isin = 'US0378331005'
        mock_result.ticker = 'AAPL.US'
        mock_search.return_value = [mock_result]
        
        result = self.bot.asset_service.search_by_isin('US0378331005')
        self.assertEqual(result, 'AAPL.US')
        
        # Test with no results
        mock_search.return_value = []
        result = self.bot.asset_service.search_by_isin('INVALID123')
        self.assertIsNone(result)
        
        # Test with exception
        mock_search.side_effect = Exception("Search failed")
        result = self.bot.asset_service.search_by_isin('US0378331005')
        self.assertIsNone(result)
    
    @patch('bot.OkamaFinanceBot._send_message_safe')
    async def test_info_command_empty_args(self, mock_send):
        """Test info command with empty arguments"""
        # Mock update and context
        update = Mock()
        context = Mock()
        context.args = []
        
        # Call the command
        await self.bot.info_command(update, context)
        
        # Check that message was sent
        mock_send.assert_called_once()
        
        # Check that message contains examples
        call_args = mock_send.call_args[0]
        message = call_args[1]
        self.assertIn('Укажите название инструмента', message)
        self.assertIn('пример', message)
    
    @patch('bot.OkamaFinanceBot._send_message_safe')
    async def test_handle_message_asset_symbol(self, mock_send):
        """Test handling message with asset symbol"""
        # Mock update and context
        update = Mock()
        update.message.text = 'SBER.MOEX'
        update.effective_user.id = 123
        context = Mock()
        
        # Mock asset service methods
        with patch.object(self.bot.asset_service, 'get_asset_info') as mock_get_info:
            mock_get_info.return_value = {
                'name': 'Sberbank',
                'exchange': 'MOEX',
                'country': 'Russia',
                'currency': 'RUB',
                'type': 'Stock'
            }
            
            # Call the handler
            await self.bot.handle_message(update, context)
            
            # Check that asset info was requested
            mock_get_info.assert_called_once_with('SBER.MOEX')


if __name__ == '__main__':
    unittest.main()

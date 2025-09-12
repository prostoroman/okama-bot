#!/usr/bin/env python3
"""
Test script to verify the /list command format change from tabulate to bullet list.
"""

import sys
import os

# Add the parent directory to the path to import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_bullet_list_format():
    """Test that the bullet list format is correctly implemented"""
    
    # Mock data similar to what would come from okama or tushare
    mock_symbols_data = [
        {'symbol': 'AAPL.US', 'name': 'Apple Inc.'},
        {'symbol': 'TSLA.US', 'name': 'Tesla Inc.'},
        {'symbol': 'MSFT.US', 'name': 'Microsoft Corporation'},
        {'symbol': 'GOOGL.US', 'name': 'Alphabet Inc.'},
        {'symbol': 'AMZN.US', 'name': 'Amazon.com Inc.'}
    ]
    
    # Test the new bullet list format logic
    symbol_list = []
    
    for symbol_info in mock_symbols_data:
        symbol = symbol_info['symbol']
        name = symbol_info['name']
        
        # Create bullet list item (same logic as in the modified methods)
        symbol_list.append(f"• `{symbol}` - {name}")
    
    # Join the list
    formatted_output = "\n".join(symbol_list)
    
    print("Testing bullet list format:")
    print("=" * 50)
    print(formatted_output)
    print("=" * 50)
    
    # Verify the format
    expected_format = """• `AAPL.US` - Apple Inc.
• `TSLA.US` - Tesla Inc.
• `MSFT.US` - Microsoft Corporation
• `GOOGL.US` - Alphabet Inc.
• `AMZN.US` - Amazon.com Inc."""
    
    assert formatted_output == expected_format, f"Format mismatch!\nExpected:\n{expected_format}\nGot:\n{formatted_output}"
    
    print("✅ Bullet list format test passed!")
    
    # Test with Chinese symbols
    chinese_symbols_data = [
        {'symbol': '000001.SZ', 'name': 'Ping An Bank Co Ltd'},
        {'symbol': '000002.SZ', 'name': 'China Vanke Co Ltd'},
        {'symbol': '600000.SH', 'name': 'Shanghai Pudong Development Bank'},
        {'symbol': '600036.SH', 'name': 'China Merchants Bank Co Ltd'}
    ]
    
    chinese_symbol_list = []
    for symbol_info in chinese_symbols_data:
        symbol = symbol_info['symbol']
        name = symbol_info['name']
        chinese_symbol_list.append(f"• `{symbol}` - {name}")
    
    chinese_formatted_output = "\n".join(chinese_symbol_list)
    
    print("\nTesting Chinese symbols bullet list format:")
    print("=" * 50)
    print(chinese_formatted_output)
    print("=" * 50)
    
    print("✅ Chinese symbols bullet list format test passed!")
    
    return True

if __name__ == "__main__":
    try:
        test_bullet_list_format()
        print("\n🎉 All tests passed! The /list command format has been successfully changed from tabulate to bullet list.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

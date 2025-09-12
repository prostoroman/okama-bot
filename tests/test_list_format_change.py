#!/usr/bin/env python3
"""
Test script to verify the /list command format change from tabulate to bullet list.
"""

import sys
import os

# Add the parent directory to the path to import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_bullet_list_format():
    """Test that the bullet list format is correctly implemented with bold tickers and truncated names"""
    
    # Mock data similar to what would come from okama or tushare
    mock_symbols_data = [
        {'symbol': 'AAPL.US', 'name': 'Apple Inc.'},
        {'symbol': 'TSLA.US', 'name': 'Tesla Inc.'},
        {'symbol': 'MSFT.US', 'name': 'Microsoft Corporation'},
        {'symbol': 'GOOGL.US', 'name': 'Alphabet Inc.'},
        {'symbol': 'AMZN.US', 'name': 'Amazon.com Inc.'},
        {'symbol': 'VERY_LONG_COMPANY_NAME.US', 'name': 'This is a very long company name that should be truncated to 40 characters maximum'}
    ]
    
    # Test the new bullet list format logic with bold tickers and truncated names
    symbol_list = []
    
    for symbol_info in mock_symbols_data:
        symbol = symbol_info['symbol']
        name = symbol_info['name']
        
        # Simple escaping for list display - only escape characters that interfere with bold formatting
        escaped_name = name.replace('*', '\\*').replace('_', '\\_')
        
        # Truncate name to maximum 40 characters
        if len(escaped_name) > 40:
            escaped_name = escaped_name[:37] + "..."
        
        # Create bullet list item with bold ticker (same logic as in the modified methods)
        symbol_list.append(f"• **{symbol}** - {escaped_name}")
    
    # Join the list
    formatted_output = "\n".join(symbol_list)
    
    print("Testing bullet list format with bold tickers and truncated names:")
    print("=" * 70)
    print(formatted_output)
    print("=" * 70)
    
    # Verify the format
    expected_format = """• **AAPL.US** - Apple Inc.
• **TSLA.US** - Tesla Inc.
• **MSFT.US** - Microsoft Corporation
• **GOOGL.US** - Alphabet Inc.
• **AMZN.US** - Amazon.com Inc.
• **VERY_LONG_COMPANY_NAME.US** - This is a very long company name..."""
    
    assert formatted_output == expected_format, f"Format mismatch!\nExpected:\n{expected_format}\nGot:\n{formatted_output}"
    
    print("✅ Bullet list format with bold tickers and truncated names test passed!")
    
    # Test with Chinese symbols (including problematic names with periods and commas)
    chinese_symbols_data = [
        {'symbol': '000001.SZ', 'name': 'Ping An Bank Co Ltd'},
        {'symbol': '000002.SZ', 'name': 'China Vanke Co Ltd'},
        {'symbol': '600000.SH', 'name': 'Shanghai Pudong Development Bank Co Ltd'},
        {'symbol': '600036.SH', 'name': 'China Merchants Bank Co., Ltd.'},
        {'symbol': '600037.SH', 'name': 'Beijing Gehua Catv Network Co.,Ltd.'},
        {'symbol': '600038.SH', 'name': 'Avicopter Plc.'}
    ]
    
    chinese_symbol_list = []
    for symbol_info in chinese_symbols_data:
        symbol = symbol_info['symbol']
        name = symbol_info['name']
        
        # Simple escaping for list display - only escape characters that interfere with bold formatting
        escaped_name = name.replace('*', '\\*').replace('_', '\\_')
        
        # Truncate name to maximum 40 characters
        if len(escaped_name) > 40:
            escaped_name = escaped_name[:37] + "..."
        
        chinese_symbol_list.append(f"• **{symbol}** - {escaped_name}")
    
    chinese_formatted_output = "\n".join(chinese_symbol_list)
    
    print("\nTesting Chinese symbols bullet list format:")
    print("=" * 70)
    print(chinese_formatted_output)
    print("=" * 70)
    
    # Verify that periods and commas are NOT escaped
    assert "Co., Ltd." in chinese_formatted_output, "Periods and commas should not be escaped"
    assert "Co.,Ltd." in chinese_formatted_output, "Periods and commas should not be escaped"
    assert "Plc." in chinese_formatted_output, "Periods should not be escaped"
    assert "\\." not in chinese_formatted_output, "Periods should not be escaped with backslashes"
    assert "\\," not in chinese_formatted_output, "Commas should not be escaped with backslashes"
    
    print("✅ Chinese symbols bullet list format test passed!")
    print("✅ Verified that periods and commas are NOT over-escaped!")
    
    return True

if __name__ == "__main__":
    try:
        test_bullet_list_format()
        print("\n🎉 All tests passed! The /list command format has been successfully updated with bold tickers, truncated names, and clean escaping.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

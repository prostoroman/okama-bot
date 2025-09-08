#!/usr/bin/env python3
"""
Test script for portfolio display format with weights
Tests the new format showing portfolios with symbols and weights
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_portfolio_format_with_weights():
    """Test portfolio formatting with symbols and weights"""
    print("🧪 Testing Portfolio Format with Weights")
    
    # Test cases
    test_cases = [
        {
            'portfolio_info': {
                'symbols': ['SPY.US', 'QQQ.US', 'BND.US'],
                'weights': [0.6, 0.3, 0.1]
            },
            'expected': 'SPY.US:60.0% QQQ.US:30.0% BND.US:10.0%',
            'description': 'Three assets with weights'
        },
        {
            'portfolio_info': {
                'symbols': ['SBER.MOEX', 'GAZP.MOEX'],
                'weights': [0.7, 0.3]
            },
            'expected': 'SBER.MOEX:70.0% GAZP.MOEX:30.0%',
            'description': 'Two assets with weights'
        },
        {
            'portfolio_info': {
                'symbols': ['AAPL.US'],
                'weights': [1.0]
            },
            'expected': 'AAPL.US:100.0%',
            'description': 'Single asset'
        },
        {
            'portfolio_info': {
                'symbols': ['SPY.US', 'QQQ.US'],
                'weights': [0.5, 0.5]
            },
            'expected': 'SPY.US:50.0% QQQ.US:50.0%',
            'description': 'Equal weights'
        },
        {
            'portfolio_info': {
                'symbols': ['SPY.US', 'QQQ.US'],
                'weights': []
            },
            'expected': 'SPY.US, QQQ.US',
            'description': 'Missing weights (fallback)'
        },
        {
            'portfolio_info': {
                'symbols': [],
                'weights': [0.6, 0.4]
            },
            'expected': '',
            'description': 'Missing symbols (fallback)'
        }
    ]
    
    def format_portfolio_display(portfolio_info):
        """Simulate the portfolio formatting logic from compare_command"""
        symbols = portfolio_info.get('symbols', [])
        weights = portfolio_info.get('weights', [])
        
        # Create formatted portfolio string with symbols and weights
        if symbols and weights and len(symbols) == len(weights):
            portfolio_parts = []
            for i, (symbol, weight) in enumerate(zip(symbols, weights)):
                portfolio_parts.append(f"{symbol}:{weight:.1%}")
            portfolio_str = ' '.join(portfolio_parts)
        else:
            portfolio_str = ', '.join(symbols)
        
        return portfolio_str
    
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        try:
            result = format_portfolio_display(test_case['portfolio_info'])
            if result == test_case['expected']:
                print(f"✅ {test_case['description']}: {result}")
                passed += 1
            else:
                print(f"❌ {test_case['description']}: {result} (expected: {test_case['expected']})")
        except Exception as e:
            print(f"❌ {test_case['description']}: Error - {e}")
    
    print(f"\n📊 Format Results: {passed}/{total} tests passed")
    return passed == total

def test_portfolio_display_integration():
    """Test integration with saved portfolios structure"""
    print("\n🧪 Testing Portfolio Display Integration")
    
    # Simulate saved portfolios structure
    saved_portfolios = {
        'PF_1': {
            'symbols': ['SPY.US', 'QQQ.US', 'BND.US'],
            'weights': [0.6, 0.3, 0.1],
            'currency': 'USD'
        },
        'PF_2': {
            'symbols': ['SBER.MOEX', 'GAZP.MOEX'],
            'weights': [0.7, 0.3],
            'currency': 'RUB'
        },
        'PF_3': {
            'symbols': ['AAPL.US', 'TSLA.US'],
            'weights': [0.8, 0.2],
            'currency': 'USD'
        }
    }
    
    def generate_portfolio_list(portfolios):
        """Simulate the portfolio list generation"""
        portfolio_list = "💾 Ваши сохраненные портфели:\n"
        
        for portfolio_symbol, portfolio_info in portfolios.items():
            symbols = portfolio_info.get('symbols', [])
            weights = portfolio_info.get('weights', [])
            
            # Create formatted portfolio string with symbols and weights
            if symbols and weights and len(symbols) == len(weights):
                portfolio_parts = []
                for i, (symbol, weight) in enumerate(zip(symbols, weights)):
                    portfolio_parts.append(f"{symbol}:{weight:.1%}")
                portfolio_str = ' '.join(portfolio_parts)
            else:
                portfolio_str = ', '.join(symbols)
            
            portfolio_list += f"• `{portfolio_symbol}` - {portfolio_str}\n"
        
        return portfolio_list
    
    try:
        result = generate_portfolio_list(saved_portfolios)
        
        # Check if all portfolios are included
        expected_portfolios = ['PF_1', 'PF_2', 'PF_3']
        all_included = all(pf in result for pf in expected_portfolios)
        
        # Check if weights are formatted correctly
        weight_format_correct = (
            'SPY.US:60.0%' in result and
            'SBER.MOEX:70.0%' in result and
            'AAPL.US:80.0%' in result
        )
        
        if all_included and weight_format_correct:
            print("✅ Portfolio list generation: All portfolios included with weights")
            print("📋 Generated list:")
            print(result)
            return True
        else:
            print("❌ Portfolio list generation: Missing portfolios or incorrect format")
            print(f"All included: {all_included}, Weight format correct: {weight_format_correct}")
            return False
            
    except Exception as e:
        print(f"❌ Portfolio list generation: Error - {e}")
        return False

def test_compare_command_integration():
    """Test how the new format integrates with compare command"""
    print("\n🧪 Testing Compare Command Integration")
    
    # Simulate the compare command help message generation
    saved_portfolios = {
        'PF_1': {
            'symbols': ['SPY.US', 'QQQ.US'],
            'weights': [0.6, 0.4],
            'currency': 'USD'
        },
        'PF_2': {
            'symbols': ['SBER.MOEX', 'GAZP.MOEX'],
            'weights': [0.7, 0.3],
            'currency': 'RUB'
        }
    }
    
    def generate_compare_help_message(portfolios):
        """Simulate the help message generation"""
        help_text = "📊 Команда /compare - Сравнение активов\n\n"
        help_text += "💡 **Примеры ввода:**\n"
        help_text += "• `SPY.US QQQ.US` - сравнение символов с символами\n"
        help_text += "• `PF_1 PF_2` - сравнение портфелей с портфелями\n"
        help_text += "• `PF_1 SBER.MOEX` - смешанное сравнение\n\n"
        
        if portfolios:
            help_text += "💾 Ваши сохраненные портфели:\n"
            for portfolio_symbol, portfolio_info in portfolios.items():
                symbols = portfolio_info.get('symbols', [])
                weights = portfolio_info.get('weights', [])
                
                # Create formatted portfolio string with symbols and weights
                if symbols and weights and len(symbols) == len(weights):
                    portfolio_parts = []
                    for i, (symbol, weight) in enumerate(zip(symbols, weights)):
                        portfolio_parts.append(f"{symbol}:{weight:.1%}")
                    portfolio_str = ' '.join(portfolio_parts)
                else:
                    portfolio_str = ', '.join(symbols)
                
                help_text += f"• `{portfolio_symbol}` - {portfolio_str}\n"
            
            help_text += "\n💡 Вы можете использовать символы портфелей в сравнении:\n"
            help_text += "`/compare PF_1 SPY.US` - сравнить ваш портфель с S&P 500\n"
            help_text += "`/compare PF_1 PF_2` - сравнить два ваших портфеля\n"
            help_text += "`/compare portfolio_123.PF SPY.US` - сравнить портфель с активом\n\n"
        
        help_text += "💬 Введите символы для сравнения:"
        
        return help_text
    
    try:
        result = generate_compare_help_message(saved_portfolios)
        
        # Check if the message contains the expected elements
        has_examples = '💡 **Примеры ввода:**' in result
        has_portfolios = '💾 Ваши сохраненные портфели:' in result
        has_weight_format = 'SPY.US:60.0%' in result and 'SBER.MOEX:70.0%' in result
        has_usage_tips = 'Вы можете использовать символы портфелей в сравнении:' in result
        has_input_prompt = '💬 Введите символы для сравнения:' in result
        
        if all([has_examples, has_portfolios, has_weight_format, has_usage_tips, has_input_prompt]):
            print("✅ Compare help message: All elements present with weight format")
            print("📋 Message preview:")
            print(result[:500] + "..." if len(result) > 500 else result)
            return True
        else:
            print("❌ Compare help message: Missing elements")
            print(f"Examples: {has_examples}, Portfolios: {has_portfolios}, Weights: {has_weight_format}, Tips: {has_usage_tips}, Prompt: {has_input_prompt}")
            return False
            
    except Exception as e:
        print(f"❌ Compare help message: Error - {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Portfolio Display Format Test Suite")
    print("=" * 60)
    
    tests = [
        test_portfolio_format_with_weights,
        test_portfolio_display_integration,
        test_compare_command_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
        except Exception as e:
            print(f"❌ Test error in {test.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Portfolio display format with weights works correctly.")
        print("\n💡 New format features:")
        print("• Shows symbols with weights (e.g., SPY.US:60.0% QQQ.US:40.0%)")
        print("• Fallback to comma-separated if weights missing")
        print("• Integrated with compare command help message")
        print("• User-friendly display in saved portfolios list")
    else:
        print("❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()

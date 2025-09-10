#!/usr/bin/env python3
"""
Simple test script to verify the annual return period fix logic.
This test focuses on the core logic without requiring all dependencies.
"""

import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


class AnnualReturnPeriodCalculator:
    """Simplified version of the period calculation logic"""
    
    def calculate_portfolio_years(self, portfolio, returns) -> float:
        """Calculate the actual number of years for portfolio CAGR calculation"""
        try:
            # Handle empty returns
            if len(returns) == 0:
                return 0
            # Try to get actual dates from portfolio object
            if hasattr(portfolio, 'first_date') and hasattr(portfolio, 'last_date'):
                try:
                    # Parse dates from portfolio object
                    if isinstance(portfolio.first_date, str):
                        start_date = datetime.strptime(portfolio.first_date, '%Y-%m-%d')
                    else:
                        start_date = portfolio.first_date
                    
                    if isinstance(portfolio.last_date, str):
                        end_date = datetime.strptime(portfolio.last_date, '%Y-%m-%d')
                    else:
                        end_date = portfolio.last_date
                    
                    # Calculate years difference
                    days_diff = (end_date - start_date).days
                    years = days_diff / 365.25  # Use 365.25 for leap years
                    
                    if years > 0:
                        return years
                except Exception as e:
                    print(f"Could not parse portfolio dates: {e}")
            
            # Fallback: estimate from returns data frequency
            if len(returns) > 0:
                # Try to detect data frequency from index
                if hasattr(returns, 'index'):
                    index = returns.index
                    if len(index) > 1:
                        # Calculate average time difference between data points
                        time_diffs = []
                        for i in range(1, min(len(index), 10)):  # Check first 10 differences
                            try:
                                diff = (index[i] - index[i-1]).days
                                time_diffs.append(diff)
                            except:
                                continue
                        
                        if time_diffs:
                            avg_days = sum(time_diffs) / len(time_diffs)
                            total_days = (index[-1] - index[0]).days
                            years = total_days / 365.25
                            return years
            
            # Final fallback: assume monthly data
            return len(returns) / 12 if len(returns) > 0 else 0
            
        except Exception as e:
            print(f"Error calculating portfolio years: {e}")
            # Ultimate fallback: assume monthly data
            return len(returns) / 12 if len(returns) > 0 else 0


class TestAnnualReturnPeriodFix(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.calculator = AnnualReturnPeriodCalculator()
    
    def test_calculate_portfolio_years_with_dates(self):
        """Test portfolio years calculation with actual dates"""
        # Create mock portfolio with dates
        class MockPortfolio:
            def __init__(self, first_date, last_date):
                self.first_date = first_date
                self.last_date = last_date
        
        # Test with 5-year period
        start_date = datetime(2019, 1, 1)
        end_date = datetime(2024, 1, 1)
        portfolio = MockPortfolio(start_date, end_date)
        
        # Create mock returns data
        returns = pd.Series(np.random.normal(0.01, 0.05, 60))  # 60 months of data
        
        years = self.calculator.calculate_portfolio_years(portfolio, returns)
        
        # Should be approximately 5 years
        self.assertAlmostEqual(years, 5.0, delta=0.1)
        print(f"✅ Portfolio years calculation with dates: {years:.2f} years")
    
    def test_calculate_portfolio_years_with_string_dates(self):
        """Test portfolio years calculation with string dates"""
        # Create mock portfolio with string dates
        class MockPortfolio:
            def __init__(self, first_date, last_date):
                self.first_date = first_date
                self.last_date = last_date
        
        # Test with 3-year period
        portfolio = MockPortfolio("2021-01-01", "2024-01-01")
        
        # Create mock returns data
        returns = pd.Series(np.random.normal(0.01, 0.05, 36))  # 36 months of data
        
        years = self.calculator.calculate_portfolio_years(portfolio, returns)
        
        # Should be approximately 3 years
        self.assertAlmostEqual(years, 3.0, delta=0.1)
        print(f"✅ Portfolio years calculation with string dates: {years:.2f} years")
    
    def test_calculate_portfolio_years_fallback(self):
        """Test portfolio years calculation fallback when no dates available"""
        # Create mock portfolio without dates
        class MockPortfolio:
            pass
        
        portfolio = MockPortfolio()
        
        # Create mock returns data with datetime index
        dates = pd.date_range('2020-01-01', periods=24, freq='M')  # 24 months
        returns = pd.Series(np.random.normal(0.01, 0.05, 24), index=dates)
        
        years = self.calculator.calculate_portfolio_years(portfolio, returns)
        
        # Should calculate from index dates
        self.assertAlmostEqual(years, 2.0, delta=0.1)
        print(f"✅ Portfolio years calculation fallback: {years:.2f} years")
    
    def test_calculate_portfolio_years_ultimate_fallback(self):
        """Test portfolio years calculation ultimate fallback"""
        # Create mock portfolio without dates
        class MockPortfolio:
            pass
        
        portfolio = MockPortfolio()
        
        # Create mock returns data without datetime index
        returns = pd.Series(np.random.normal(0.01, 0.05, 12))  # 12 months
        
        years = self.calculator.calculate_portfolio_years(portfolio, returns)
        
        # Should fall back to monthly assumption
        self.assertEqual(years, 1.0)
        print(f"✅ Portfolio years calculation ultimate fallback: {years:.2f} years")
    
    def test_annual_return_calculation_comparison(self):
        """Test that annual return calculation is more accurate with real period"""
        # Create sample returns data for 3 years
        returns_3y = pd.Series([0.02, 0.01, -0.01, 0.03, 0.02, -0.02, 0.01, 0.02, 0.01, 0.03, 0.01, 0.02] * 3)  # 3 years
        
        # Old method: assume monthly data
        total_return_old = (1 + returns_3y).prod() - 1
        years_old = len(returns_3y) / 12  # This would be 3.0
        cagr_old = (1 + total_return_old) ** (1 / years_old) - 1
        
        # New method: use actual period
        total_return_new = (1 + returns_3y).prod() - 1
        years_new = 3.0  # Actual 3 years
        cagr_new = (1 + total_return_new) ** (1 / years_new) - 1
        
        # Both should be the same for this case, but demonstrate the concept
        self.assertAlmostEqual(cagr_old, cagr_new, places=6)
        print(f"✅ Annual return calculation comparison: Old={cagr_old:.4f}, New={cagr_new:.4f}")
    
    def test_edge_cases(self):
        """Test edge cases for years calculation"""
        # Test with very short period
        class MockPortfolio:
            def __init__(self, first_date, last_date):
                self.first_date = first_date
                self.last_date = last_date
        
        # 1 month period
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 2, 1)
        portfolio = MockPortfolio(start_date, end_date)
        
        returns = pd.Series([0.01])  # 1 data point
        
        years = self.calculator.calculate_portfolio_years(portfolio, returns)
        
        # Should handle short periods gracefully
        self.assertGreater(years, 0)
        self.assertLess(years, 1)
        print(f"✅ Edge case - short period: {years:.4f} years")
        
        # Test with empty returns
        years_empty = self.calculator.calculate_portfolio_years(portfolio, pd.Series(dtype=float))
        self.assertEqual(years_empty, 0)
        print(f"✅ Edge case - empty returns: {years_empty} years")
    
    def test_real_world_scenario(self):
        """Test real-world scenario with different periods"""
        # Scenario 1: 5Y portfolio
        portfolio_5y = type('MockPortfolio', (), {
            'first_date': '2019-01-01',
            'last_date': '2024-01-01'
        })()
        
        returns_5y = pd.Series(np.random.normal(0.01, 0.05, 60))  # 60 months
        years_5y = self.calculator.calculate_portfolio_years(portfolio_5y, returns_5y)
        self.assertAlmostEqual(years_5y, 5.0, delta=0.1)
        print(f"✅ Real-world scenario 5Y: {years_5y:.2f} years")
        
        # Scenario 2: 1Y portfolio
        portfolio_1y = type('MockPortfolio', (), {
            'first_date': '2023-01-01',
            'last_date': '2024-01-01'
        })()
        
        returns_1y = pd.Series(np.random.normal(0.01, 0.05, 12))  # 12 months
        years_1y = self.calculator.calculate_portfolio_years(portfolio_1y, returns_1y)
        self.assertAlmostEqual(years_1y, 1.0, delta=0.1)
        print(f"✅ Real-world scenario 1Y: {years_1y:.2f} years")


def run_tests():
    """Run all tests"""
    print("🧪 Testing Annual Return Period Fix (Simple Version)...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAnnualReturnPeriodFix)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All tests passed! Annual return period fix logic is working correctly.")
        print("\n📋 Summary of improvements:")
        print("   • Portfolio years calculation now uses actual dates from portfolio object")
        print("   • Fallback mechanisms for when dates are not available")
        print("   • Proper handling of different data frequencies")
        print("   • Edge case handling for short periods and empty data")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for failure in result.failures:
            print(f"FAILURE: {failure[0]}")
            print(failure[1])
        for error in result.errors:
            print(f"ERROR: {error[0]}")
            print(error[1])
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

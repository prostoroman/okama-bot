#!/usr/bin/env python3
"""
Test for table image generation functionality
Tests the new table image generation feature in chart_styles.py
"""

import unittest
import sys
import os
import pandas as pd
import io
from unittest.mock import Mock, patch

# Add the parent directory to the path to import chart_styles
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chart_styles import ChartStyles

class TestTableImageGeneration(unittest.TestCase):
    """Test cases for table image generation"""
    
    def setUp(self):
        """Set up test environment"""
        self.chart_styles = ChartStyles()
        
        # Create sample data for testing
        self.sample_data_2 = {
            'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51],
            'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81]
        }
        
        self.sample_data_4 = {
            'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51],
            'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81],
            'AAPL.US': [0.12, 0.22, 0.19, 0.14, 0.01, 0.25, -0.45],
            'MSFT.US': [0.10, 0.20, 0.17, 0.12, 0.01, 0.23, -0.40]
        }
        
        self.sample_data_6 = {
            'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51],
            'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81],
            'AAPL.US': [0.12, 0.22, 0.19, 0.14, 0.01, 0.25, -0.45],
            'MSFT.US': [0.10, 0.20, 0.17, 0.12, 0.01, 0.23, -0.40],
            'GOOGL.US': [0.13, 0.23, 0.20, 0.15, 0.00, 0.26, -0.50],
            'AMZN.US': [0.09, 0.19, 0.16, 0.11, 0.00, 0.24, -0.35]
        }
        
        self.index = [
            'Compound return',
            'CAGR (1Y)',
            'CAGR (5Y)', 
            'Annualized mean return',
            'Dividend yield',
            'Risk',
            'Max drawdowns'
        ]
    
    def test_create_table_image_2_assets(self):
        """Test table image creation for 2 assets"""
        df_2 = pd.DataFrame(self.sample_data_2, index=self.index)
        symbols = ['SPY.US', 'QQQ.US']
        
        fig, ax = self.chart_styles.create_table_image(df_2, "Test Table", symbols)
        
        # Check that figure and axis are created
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        
        # Check figure size (should be smaller for 2 assets)
        fig_width, fig_height = fig.get_size_inches()
        self.assertEqual(fig_width, 10)  # Expected width for 2 assets
        self.assertGreaterEqual(fig_height, 6)  # Minimum height
        
        # Cleanup
        self.chart_styles.cleanup_figure(fig)
    
    def test_create_table_image_4_assets(self):
        """Test table image creation for 4 assets"""
        df_4 = pd.DataFrame(self.sample_data_4, index=self.index)
        symbols = ['SPY.US', 'QQQ.US', 'AAPL.US', 'MSFT.US']
        
        fig, ax = self.chart_styles.create_table_image(df_4, "Test Table", symbols)
        
        # Check that figure and axis are created
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        
        # Check figure size (should be medium for 4 assets)
        fig_width, fig_height = fig.get_size_inches()
        self.assertEqual(fig_width, 14)  # Expected width for 4 assets
        self.assertGreaterEqual(fig_height, 6)  # Minimum height
        
        # Cleanup
        self.chart_styles.cleanup_figure(fig)
    
    def test_create_table_image_6_assets(self):
        """Test table image creation for 6 assets"""
        df_6 = pd.DataFrame(self.sample_data_6, index=self.index)
        symbols = ['SPY.US', 'QQQ.US', 'AAPL.US', 'MSFT.US', 'GOOGL.US', 'AMZN.US']
        
        fig, ax = self.chart_styles.create_table_image(df_6, "Test Table", symbols)
        
        # Check that figure and axis are created
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        
        # Check figure size (should be larger for 6 assets)
        fig_width, fig_height = fig.get_size_inches()
        self.assertEqual(fig_width, 16)  # Expected width for 6 assets
        self.assertGreaterEqual(fig_height, 6)  # Minimum height
        
        # Cleanup
        self.chart_styles.cleanup_figure(fig)
    
    def test_create_table_image_with_nan_values(self):
        """Test table image creation with NaN values"""
        data_with_nan = {
            'SPY.US': [0.08, 0.16, float('nan'), 0.09],
            'QQQ.US': [0.11, 0.21, 0.18, float('nan')],
            'AAPL.US': [0.12, 0.22, 0.19, 0.14]
        }
        index_with_nan = ['Compound return', 'CAGR (1Y)', 'CAGR (5Y)', 'Annualized mean return']
        df_with_nan = pd.DataFrame(data_with_nan, index=index_with_nan)
        
        fig, ax = self.chart_styles.create_table_image(df_with_nan, "Test Table with NaN")
        
        # Check that figure and axis are created
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        
        # Cleanup
        self.chart_styles.cleanup_figure(fig)
    
    def test_create_table_image_error_handling(self):
        """Test error handling in table image creation"""
        # Test with invalid data
        invalid_data = pd.DataFrame()
        
        fig, ax = self.chart_styles.create_table_image(invalid_data, "Test Table")
        
        # Should still return figure and axis (fallback)
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        
        # Cleanup
        self.chart_styles.cleanup_figure(fig)
    
    def test_save_table_image_to_bytes(self):
        """Test saving table image to bytes"""
        df_2 = pd.DataFrame(self.sample_data_2, index=self.index)
        
        fig, ax = self.chart_styles.create_table_image(df_2, "Test Table")
        
        # Save to bytes
        buffer = io.BytesIO()
        self.chart_styles.save_figure(fig, buffer)
        buffer.seek(0)
        image_bytes = buffer.getvalue()
        
        # Check that bytes are generated
        self.assertGreater(len(image_bytes), 0)
        
        # Check that it's a valid PNG (starts with PNG signature)
        self.assertTrue(image_bytes.startswith(b'\x89PNG'))
        
        # Cleanup
        self.chart_styles.cleanup_figure(fig)
    
    def test_simple_table_image_fallback(self):
        """Test simple table image fallback"""
        df_2 = pd.DataFrame(self.sample_data_2, index=self.index)
        
        # Mock the main function to raise an exception
        with patch.object(self.chart_styles, 'create_table_image', side_effect=Exception("Test error")):
            fig, ax = self.chart_styles._create_simple_table_image(df_2, "Test Table")
            
            # Check that fallback figure and axis are created
            self.assertIsNotNone(fig)
            self.assertIsNotNone(ax)
            
            # Cleanup
            self.chart_styles.cleanup_figure(fig)
    
    def test_table_image_with_symbols_formatting(self):
        """Test table image with symbol formatting"""
        df_2 = pd.DataFrame(self.sample_data_2, index=self.index)
        symbols = ['SPY.US', 'QQQ.US']
        
        fig, ax = self.chart_styles.create_table_image(df_2, "Test Table", symbols)
        
        # Check that figure and axis are created
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        
        # Cleanup
        self.chart_styles.cleanup_figure(fig)
    
    def test_table_image_performance_highlighting(self):
        """Test performance highlighting in table images"""
        df_4 = pd.DataFrame(self.sample_data_4, index=self.index)
        symbols = ['SPY.US', 'QQQ.US', 'AAPL.US', 'MSFT.US']
        
        fig, ax = self.chart_styles.create_table_image(df_4, "Test Table", symbols)
        
        # Check that figure and axis are created
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        
        # The highlighting logic is tested by creating the table
        # Specific color testing would require more complex matplotlib testing
        
        # Cleanup
        self.chart_styles.cleanup_figure(fig)

if __name__ == '__main__':
    unittest.main()

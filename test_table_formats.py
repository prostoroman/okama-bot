#!/usr/bin/env python3
"""
Test different table formatting options for Telegram
"""

import pandas as pd
import sys
import os

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Optional imports
try:
    import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

def test_table_formats():
    """Test different table formatting options for Telegram"""
    
    # Create sample data similar to okama.AssetList.describe()
    sample_data = {
        'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51, 0.39],
        'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81, 0.64],
        'AAPL.US': [0.12, 0.22, 0.19, 0.14, 0.01, 0.25, -0.45, 0.55],
        'inflation': [0.02, 0.03, 0.03, 0.03, None, None, None, None]
    }
    
    sample_index = [
        'Compound return',
        'CAGR (1Y)',
        'CAGR (5Y)', 
        'Annualized mean return',
        'Dividend yield',
        'Risk',
        'Max drawdowns',
        'CVAR'
    ]
    
    df = pd.DataFrame(sample_data, index=sample_index)
    
    print("=== TESTING DIFFERENT TABLE FORMATS FOR TELEGRAM ===\n")
    
    if TABULATE_AVAILABLE:
        # Test 1: Pipe format (current)
        print("1. PIPE FORMAT (current):")
        print("=" * 50)
        pipe_table = tabulate.tabulate(df, headers='keys', tablefmt='pipe', floatfmt='.2f')
        print(f"```\n{pipe_table}\n```")
        print(f"Length: {len(pipe_table)} characters\n")
        
        # Test 2: Simple format
        print("2. SIMPLE FORMAT:")
        print("=" * 50)
        simple_table = tabulate.tabulate(df, headers='keys', tablefmt='simple', floatfmt='.2f')
        print(f"```\n{simple_table}\n```")
        print(f"Length: {len(simple_table)} characters\n")
        
        # Test 3: Grid format
        print("3. GRID FORMAT:")
        print("=" * 50)
        grid_table = tabulate.tabulate(df, headers='keys', tablefmt='grid', floatfmt='.2f')
        print(f"```\n{grid_table}\n```")
        print(f"Length: {len(grid_table)} characters\n")
        
        # Test 4: Fancy grid format
        print("4. FANCY GRID FORMAT:")
        print("=" * 50)
        fancy_table = tabulate.tabulate(df, headers='keys', tablefmt='fancy_grid', floatfmt='.2f')
        print(f"```\n{fancy_table}\n```")
        print(f"Length: {len(fancy_table)} characters\n")
        
        # Test 5: Plain format
        print("5. PLAIN FORMAT:")
        print("=" * 50)
        plain_table = tabulate.tabulate(df, headers='keys', tablefmt='plain', floatfmt='.2f')
        print(f"```\n{plain_table}\n```")
        print(f"Length: {len(plain_table)} characters\n")
        
        # Test 6: Compact format
        print("6. COMPACT FORMAT:")
        print("=" * 50)
        compact_table = tabulate.tabulate(df, headers='keys', tablefmt='compact', floatfmt='.2f')
        print(f"```\n{compact_table}\n```")
        print(f"Length: {len(compact_table)} characters\n")
    
    # Test 7: Custom compact format
    print("7. CUSTOM COMPACT FORMAT:")
    print("=" * 50)
    custom_table = create_custom_compact_table(df)
    print(f"```\n{custom_table}\n```")
    print(f"Length: {len(custom_table)} characters\n")
    
    # Test 8: Vertical format (one metric per line)
    print("8. VERTICAL FORMAT:")
    print("=" * 50)
    vertical_table = create_vertical_table(df)
    print(f"```\n{vertical_table}\n```")
    print(f"Length: {len(vertical_table)} characters\n")
    
    # Test 9: Horizontal format (one asset per line)
    print("9. HORIZONTAL FORMAT:")
    print("=" * 50)
    horizontal_table = create_horizontal_table(df)
    print(f"```\n{horizontal_table}\n```")
    print(f"Length: {len(horizontal_table)} characters\n")

def create_custom_compact_table(df):
    """Create a custom compact table format"""
    result = []
    
    # Header
    columns = df.columns.tolist()
    header = "Metric".ljust(20) + " | " + " | ".join([col.ljust(8) for col in columns])
    result.append(header)
    result.append("-" * len(header))
    
    # Data rows
    for idx, row in df.iterrows():
        row_str = str(idx).ljust(20) + " | "
        values = []
        for col in columns:
            value = row[col]
            if pd.isna(value):
                values.append("N/A".ljust(8))
            elif isinstance(value, (int, float)):
                values.append(f"{value:.2f}".ljust(8))
            else:
                values.append(str(value).ljust(8))
        row_str += " | ".join(values)
        result.append(row_str)
    
    return "\n".join(result)

def create_vertical_table(df):
    """Create vertical format - one metric per line"""
    result = []
    
    for idx, row in df.iterrows():
        result.append(f"📊 {idx}:")
        for col in df.columns:
            value = row[col]
            if pd.isna(value):
                result.append(f"  • {col}: N/A")
            elif isinstance(value, (int, float)):
                result.append(f"  • {col}: {value:.2f}")
            else:
                result.append(f"  • {col}: {value}")
        result.append("")
    
    return "\n".join(result)

def create_horizontal_table(df):
    """Create horizontal format - one asset per line"""
    result = []
    
    for col in df.columns:
        result.append(f"📈 {col}:")
        for idx, row in df.iterrows():
            value = row[col]
            if pd.isna(value):
                result.append(f"  • {idx}: N/A")
            elif isinstance(value, (int, float)):
                result.append(f"  • {idx}: {value:.2f}")
            else:
                result.append(f"  • {idx}: {value}")
        result.append("")
    
    return "\n".join(result)

if __name__ == '__main__':
    test_table_formats()

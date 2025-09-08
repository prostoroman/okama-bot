#!/usr/bin/env python3
"""
Test script to verify environment variable setting before matplotlib import
"""

import os
import tempfile

print("🔧 Testing Environment Variable Setting")
print("=" * 50)

# Test 1: Set environment variable
print("1. Setting MPLCONFIGDIR...")
matplotlib_cache_dir = os.path.join(tempfile.gettempdir(), 'matplotlib_cache')
os.makedirs(matplotlib_cache_dir, exist_ok=True)
os.environ['MPLCONFIGDIR'] = matplotlib_cache_dir

print(f"   Cache directory: {matplotlib_cache_dir}")
print(f"   Directory exists: {os.path.exists(matplotlib_cache_dir)}")
print(f"   MPLCONFIGDIR set: {os.environ.get('MPLCONFIGDIR')}")

# Test 2: Import matplotlib after setting environment variable
print("\n2. Importing matplotlib...")
import matplotlib
import matplotlib.pyplot as plt

print(f"   Matplotlib version: {matplotlib.__version__}")
print(f"   Matplotlib config path: {matplotlib.matplotlib_fname()}")
print(f"   MPLCONFIGDIR still set: {os.environ.get('MPLCONFIGDIR')}")

# Test 3: Test plotting
print("\n3. Testing plotting...")
try:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
    ax.set_title('Test Plot')
    
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    
    image_data = buf.getvalue()
    print(f"   ✅ Plot created successfully ({len(image_data)} bytes)")
    
    plt.close(fig)
except Exception as e:
    print(f"   ❌ Error creating plot: {e}")

print("\n" + "=" * 50)
print("✅ Environment variable test completed")

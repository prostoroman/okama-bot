#!/usr/bin/env python3
"""
Test script to verify matplotlib configuration and cache directory setup
"""

import os
import sys
import tempfile
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

def test_matplotlib_config():
    """Test matplotlib configuration and cache directory"""
    print("🧪 Testing Matplotlib Configuration")
    print("=" * 50)
    
    # Test 1: Check cache directory
    print("1. Testing cache directory configuration...")
    try:
        mplconfigdir = os.environ.get('MPLCONFIGDIR')
        if mplconfigdir:
            print(f"   ✅ MPLCONFIGDIR set to: {mplconfigdir}")
            
            # Check if directory exists and is writable
            if os.path.exists(mplconfigdir):
                print(f"   ✅ Cache directory exists: {mplconfigdir}")
            else:
                print(f"   ⚠️  Cache directory doesn't exist: {mplconfigdir}")
                
            # Test write permissions
            test_file = os.path.join(mplconfigdir, 'test_write.txt')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"   ✅ Cache directory is writable: {mplconfigdir}")
            except Exception as e:
                print(f"   ❌ Cache directory not writable: {e}")
        else:
            print("   ⚠️  No MPLCONFIGDIR environment variable set")
    except Exception as e:
        print(f"   ❌ Error checking cache directory: {e}")
    
    # Test 2: Check backend
    print("\n2. Testing matplotlib backend...")
    try:
        backend = matplotlib.get_backend()
        print(f"   ✅ Backend: {backend}")
        
        if backend == 'Agg':
            print("   ✅ Using Agg backend (suitable for headless environments)")
        else:
            print(f"   ⚠️  Using {backend} backend")
    except Exception as e:
        print(f"   ❌ Error checking backend: {e}")
    
    # Test 3: Test basic plotting
    print("\n3. Testing basic plotting functionality...")
    try:
        # Create a simple plot
        fig, ax = plt.subplots(figsize=(8, 6))
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        ax.plot(x, y, label='sin(x)')
        ax.set_title('Test Plot')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.legend()
        ax.grid(True)
        
        # Save to buffer
        import io
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        
        # Check if image was created successfully
        image_data = buf.getvalue()
        if len(image_data) > 0:
            print(f"   ✅ Plot created successfully ({len(image_data)} bytes)")
        else:
            print("   ❌ Plot creation failed (empty buffer)")
            
        plt.close(fig)
        
    except Exception as e:
        print(f"   ❌ Error creating plot: {e}")
    
    # Test 4: Check environment
    print("\n4. Checking environment...")
    print(f"   Python version: {sys.version}")
    print(f"   Environment: {'RENDER' if os.getenv('RENDER') else 'LOCAL'}")
    print(f"   Temp directory: {tempfile.gettempdir()}")
    print(f"   Current working directory: {os.getcwd()}")
    
    # Test 5: Check matplotlib version and configuration
    print("\n5. Checking matplotlib configuration...")
    try:
        print(f"   Matplotlib version: {matplotlib.__version__}")
        print(f"   Matplotlib data path: {matplotlib.get_data_path()}")
        print(f"   Matplotlib config path: {matplotlib.matplotlib_fname()}")
    except Exception as e:
        print(f"   ❌ Error checking matplotlib config: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Matplotlib configuration test completed")

def main():
    """Main function"""
    try:
        test_matplotlib_config()
        print("\n🎉 All tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Test script to verify context store fix
"""

import os
import tempfile

print("🔧 Testing Context Store Fix")
print("=" * 50)

# Test 1: Import and initialize context store
print("1. Testing context store initialization...")
try:
    import sys
    import os
    # Add parent directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from services.context_store import JSONUserContextStore
    store = JSONUserContextStore()
    print(f"   ✅ Context store initialized successfully")
    print(f"   Filepath: {store._filepath}")
    print(f"   Directory exists: {os.path.exists(os.path.dirname(store._filepath))}")
except Exception as e:
    print(f"   ❌ Error initializing context store: {e}")

# Test 2: Test user context operations
print("\n2. Testing user context operations...")
try:
    # Test getting user context
    user_id = 12345
    context = store.get_user_context(user_id)
    print(f"   ✅ User context retrieved: {len(context)} keys")
    
    # Test updating user context
    updated = store.update_user_context(user_id, test_key="test_value")
    print(f"   ✅ User context updated: {updated.get('test_key')}")
    
    # Test conversation entry
    store.add_conversation_entry(user_id, "test message", "test response")
    print(f"   ✅ Conversation entry added")
    
    print(f"   ✅ All context store operations successful")
except Exception as e:
    print(f"   ❌ Error in context operations: {e}")

# Test 3: Check file creation
print("\n3. Testing file creation...")
try:
    if os.path.exists(store._filepath):
        file_size = os.path.getsize(store._filepath)
        print(f"   ✅ Context file created: {store._filepath}")
        print(f"   File size: {file_size} bytes")
    else:
        print(f"   ⚠️  Context file not found: {store._filepath}")
except Exception as e:
    print(f"   ❌ Error checking file: {e}")

print("\n" + "=" * 50)
print("✅ Context store test completed")

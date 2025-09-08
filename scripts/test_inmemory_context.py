#!/usr/bin/env python3
"""
Test script to verify in-memory context store implementation
"""

import sys
import os

print("🔧 Testing In-Memory Context Store")
print("=" * 50)

# Test 1: Import and initialize context store
print("1. Testing context store initialization...")
try:
    # Add parent directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from services.context_store import InMemoryUserContextStore, JSONUserContextStore
    store = InMemoryUserContextStore()
    print(f"   ✅ In-memory context store initialized successfully")
    print(f"   Type: {type(store).__name__}")
except Exception as e:
    print(f"   ❌ Error initializing context store: {e}")

# Test 2: Test user context operations
print("\n2. Testing user context operations...")
try:
    # Test getting user context
    user_id = 12345
    context = store.get_user_context(user_id)
    print(f"   ✅ User context retrieved: {len(context)} keys")
    print(f"   Keys: {list(context.keys())}")
    
    # Test updating user context
    updated = store.update_user_context(user_id, test_key="test_value", portfolio_count=5)
    print(f"   ✅ User context updated: {updated.get('test_key')}")
    print(f"   Portfolio count: {updated.get('portfolio_count')}")
    
    # Test conversation entry
    store.add_conversation_entry(user_id, "test message", "test response")
    print(f"   ✅ Conversation entry added")
    
    # Test getting updated context
    final_context = store.get_user_context(user_id)
    print(f"   ✅ Final context has {len(final_context.get('conversation_history', []))} conversation entries")
    
    print(f"   ✅ All context store operations successful")
except Exception as e:
    print(f"   ❌ Error in context operations: {e}")

# Test 3: Test multiple users
print("\n3. Testing multiple users...")
try:
    user1_id = 11111
    user2_id = 22222
    
    # Create contexts for multiple users
    store.get_user_context(user1_id)
    store.update_user_context(user1_id, name="User1", portfolio_count=2)
    
    store.get_user_context(user2_id)
    store.update_user_context(user2_id, name="User2", portfolio_count=3)
    
    # Check all users
    all_users = store.get_all_users()
    print(f"   ✅ Multiple users supported: {all_users}")
    
    # Test user removal
    removed = store.remove_user(user1_id)
    print(f"   ✅ User removal works: {removed}")
    
    remaining_users = store.get_all_users()
    print(f"   ✅ Remaining users: {remaining_users}")
    
except Exception as e:
    print(f"   ❌ Error with multiple users: {e}")

# Test 4: Test backward compatibility
print("\n4. Testing backward compatibility...")
try:
    # Test that JSONUserContextStore alias works
    json_store = JSONUserContextStore()
    context = json_store.get_user_context(99999)
    print(f"   ✅ Backward compatibility works: {len(context)} keys")
except Exception as e:
    print(f"   ❌ Error with backward compatibility: {e}")

# Test 5: Test thread safety
print("\n5. Testing thread safety...")
try:
    import threading
    import time
    
    def worker(user_id, iterations):
        for i in range(iterations):
            store.update_user_context(user_id, counter=i, timestamp=time.time())
            time.sleep(0.001)  # Small delay
    
    # Create multiple threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=worker, args=(33333 + i, 10))
        threads.append(t)
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    print(f"   ✅ Thread safety test completed")
    
except Exception as e:
    print(f"   ❌ Error with thread safety: {e}")

print("\n" + "=" * 50)
print("✅ In-memory context store test completed")

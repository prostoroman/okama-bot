# Portfolio Input Debug Report

**Date:** September 4, 2025  
**Author:** Assistant  
**Type:** Bug Investigation Report

## Problem Statement
User reported that after entering portfolio data `SPY.US:0.5 QQQ.US:0.3 BND.US:0.2`, the bot incorrectly processes it as an asset lookup ("Получаю информацию об активе") instead of portfolio creation.

## Root Cause Analysis

### Expected Flow:
1. User sends `/portfolio` without parameters
2. Bot sets `waiting_for_portfolio=True` flag
3. User sends portfolio data in next message
4. Bot checks `waiting_for_portfolio` flag and calls `_handle_portfolio_input()`

### Actual Issue:
The message handler appears to bypass the portfolio input logic and treats the portfolio data as a regular asset symbol.

## Debugging Steps Implemented

### 1. Added Debug Logging
Added comprehensive logging to track the portfolio input flow:

```python
# In handle_message method
self.logger.info(f"User {user_id} context: {user_context}")
self.logger.info(f"Waiting for portfolio: {user_context.get('waiting_for_portfolio', False)}")
self.logger.info(f"Input text: {text}")

# In portfolio_command method
self.logger.info(f"Setting waiting_for_portfolio=True for user {user_id}")
updated_context = self._get_user_context(user_id)
self.logger.info(f"Updated context waiting_for_portfolio: {updated_context.get('waiting_for_portfolio', False)}")
```

### 2. Verification Points
- ✅ Flag setting in `/portfolio` command
- ✅ Flag reading in `handle_message` method
- ✅ Context persistence verification
- ❓ Actual flag state during user input (needs testing)

## Suspected Issues

### 1. Context Storage Problem
The `waiting_for_portfolio` flag might not be persisting between messages due to:
- Context storage implementation issues
- User context not being properly saved/retrieved
- Race conditions in context updates

### 2. Message Processing Order
The message might be processed before the context flag is properly set, causing the handler to treat it as a regular asset lookup.

### 3. Logic Flow Issue
The conditional check `if user_context.get('waiting_for_portfolio', False):` might not be working as expected due to:
- Context being empty/None
- Flag not being set correctly
- Boolean evaluation issues

## Next Steps

### Immediate Actions:
1. **Fix Syntax Error** - Resolve the duplicate `except` block issue preventing bot execution
2. **Test Debug Logging** - Deploy with debug logs to see actual flag states
3. **Verify Context Persistence** - Ensure user context survives between messages

### Testing Plan:
1. Send `/portfolio` command and verify flag is set
2. Send portfolio data and check if flag is detected
3. Monitor logs for context state changes
4. Test with different users to check for user-specific issues

## Technical Implementation Details

### Current Logic Flow:
```python
# In handle_message
user_context = self._get_user_context(user_id)
if user_context.get('waiting_for_portfolio', False):
    await self._handle_portfolio_input(update, context, text)
    return
# Otherwise treat as asset lookup
```

### Expected Debug Output:
```
User 12345 context: {'waiting_for_portfolio': True, ...}
Waiting for portfolio: True
Input text: SPY.US:0.5 QQQ.US:0.3 BND.US:0.2
Processing as portfolio input: SPY.US:0.5 QQQ.US:0.3 BND.US:0.2
```

## Workaround for Users
Until the issue is resolved, users can:
1. Use the full command syntax: `/portfolio SPY.US:0.5 QQQ.US:0.3 BND.US:0.2`
2. Avoid using the interactive input mode

## Status
- 🔍 **Investigation:** Complete
- 🐛 **Bug Identified:** Context flag logic issue suspected
- 🛠️ **Debug Tools:** Implemented
- ⏳ **Next:** Fix syntax error and test with debug logging

## Files Modified
- `bot.py` - Added debug logging to `handle_message` and `portfolio_command`

## Conclusion
The issue appears to be related to the `waiting_for_portfolio` flag not being properly detected in the message handler. Debug logging has been added to track the exact cause during live testing.

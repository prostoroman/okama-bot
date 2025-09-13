#!/usr/bin/env python3
"""
Script to update all _send_callback_message calls to use _send_callback_message_with_keyboard_removal
This script will replace manual keyboard removal + callback message with the new combined function.
"""

import re

def update_callback_message_calls():
    """Update all _send_callback_message calls to use the new combined function"""
    
    # Read the bot.py file
    with open('bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patterns to fix
    fixes = [
        # Fix pattern: remove keyboard + send callback message
        (
            r'(\s+)# Remove keyboard from previous message before sending new message\n(\s+)await self\._remove_keyboard_before_new_message\(update, context\)\n(\s+)\n(\s+)# Create keyboard for compare command\n(\s+)keyboard = self\._create_compare_command_keyboard\([^)]+\)\n(\s+)await self\._send_callback_message\(update, context, ([^,]+), ([^)]+)\)',
            r'\1# Create keyboard for compare command\n\2keyboard = self._create_compare_command_keyboard(symbols, currency)\n\2await self._send_callback_message_with_keyboard_removal(update, context, \7, \8)'
        ),
        # Fix pattern: just send callback message (for cases where keyboard removal was already done)
        (
            r'(\s+)# Create keyboard for compare command\n(\s+)keyboard = self\._create_compare_command_keyboard\([^)]+\)\n(\s+)await self\._send_callback_message\(update, context, ([^,]+), ([^)]+)\)',
            r'\1# Create keyboard for compare command\n\2keyboard = self._create_compare_command_keyboard(symbols, currency)\n\2await self._send_callback_message_with_keyboard_removal(update, context, \4, \5)'
        )
    ]
    
    # Apply fixes
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write the updated content back
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Successfully updated all _send_callback_message calls")
    print("📋 Updated patterns:")
    for i, (pattern, _) in enumerate(fixes, 1):
        print(f"   {i}. Updated callback message calls to use combined function")

if __name__ == "__main__":
    update_callback_message_calls()

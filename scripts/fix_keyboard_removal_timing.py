#!/usr/bin/env python3
"""
Script to fix keyboard removal timing in bot.py
This script will update all handlers to remove keyboard before sending new messages instead of after.
"""

import re

def fix_keyboard_removal_timing():
    """Fix keyboard removal timing in all handlers"""
    
    # Read the bot.py file
    with open('bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patterns to fix
    fixes = [
        # Fix handlers that use _send_callback_message
        (
            r'(\s+)# Create keyboard for compare command\n(\s+)keyboard = self\._create_compare_command_keyboard\([^)]+\)\n(\s+)await self\._send_callback_message\([^)]+\)\n(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)',
            r'\1# Remove keyboard from previous message before sending new message\n\2await self._remove_keyboard_before_new_message(update, context)\n\2\n\2# Create keyboard for compare command\n\2keyboard = self._create_compare_command_keyboard(symbols, currency)\n\2await self._send_callback_message(update, context, \3)'
        ),
        # Fix handlers that use context.bot.send_photo
        (
            r'(\s+)# Create keyboard for compare command\n(\s+)keyboard = self\._create_compare_command_keyboard\([^)]+\)\n(\s+)\n(\s+)# Send image with keyboard\n(\s+)await context\.bot\.send_photo\([^)]+\)\n(\s+)\n(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)',
            r'\1# Remove keyboard from previous message before sending new message\n\2await self._remove_keyboard_before_new_message(update, context)\n\2\n\2# Create keyboard for compare command\n\2keyboard = self._create_compare_command_keyboard(symbols, currency)\n\2\n\2# Send image with keyboard\n\2await context.bot.send_photo(\5)'
        ),
        # Fix handlers that use context.bot.send_document
        (
            r'(\s+)# Create keyboard for compare command\n(\s+)keyboard = self\._create_compare_command_keyboard\([^)]+\)\n(\s+)\n(\s+)# Send Excel file with keyboard\n(\s+)await context\.bot\.send_document\([^)]+\)\n(\s+)\n(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)',
            r'\1# Remove keyboard from previous message before sending new message\n\2await self._remove_keyboard_before_new_message(update, context)\n\2\n\2# Create keyboard for compare command\n\2keyboard = self._create_compare_command_keyboard(symbols, currency)\n\2\n\2# Send Excel file with keyboard\n\2await context.bot.send_document(\5)'
        )
    ]
    
    # Apply fixes
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write the updated content back
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Successfully fixed keyboard removal timing in all handlers")
    print("📋 Fixed patterns:")
    for i, (pattern, _) in enumerate(fixes, 1):
        print(f"   {i}. Fixed keyboard removal timing for different message types")

if __name__ == "__main__":
    fix_keyboard_removal_timing()

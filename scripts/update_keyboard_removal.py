#!/usr/bin/env python3
"""
Script to update all compare button handlers with improved keyboard removal logic.
This script will automatically update all remaining handlers to remove keyboard only after successful message creation.
"""

import re

def update_keyboard_removal_logic():
    """Update all compare button handlers with improved keyboard removal logic"""
    
    # Read the bot.py file
    with open('bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # List of handlers to update
    handlers_to_update = [
        '_handle_yandexgpt_analysis_compare_button',
        '_handle_metrics_compare_button',
        '_handle_drawdowns_button',
        '_handle_dividends_button',
        '_handle_correlation_button'
    ]
    
    # Pattern to find and replace keyboard removal calls
    patterns_to_replace = [
        # Replace early keyboard removal with comment
        (
            r'(\s+)# Remove keyboard from previous message for better UX\n(\s+)await self\._remove_keyboard_from_previous_message\(update, context\)',
            r'\1# Don\'t remove keyboard yet - wait for successful message creation\n\2'
        ),
        # Add keyboard removal after successful message creation
        (
            r'(await self\._send_callback_message\([^)]+\))\n(\s+)(except|else|return)',
            r'\1\n\2# Remove keyboard from previous message only after successful message creation\n\2await self._remove_keyboard_after_successful_message(update, context)\n\2\3'
        ),
        # Add keyboard removal after successful photo sending
        (
            r'(await context\.bot\.send_photo\([^)]+\))\n(\s+)(except|else|return)',
            r'\1\n\2# Remove keyboard from previous message only after successful message creation\n\2await self._remove_keyboard_after_successful_message(update, context)\n\2\3'
        ),
        # Add keyboard removal after successful document sending
        (
            r'(await context\.bot\.send_document\([^)]+\))\n(\s+)(except|else|return)',
            r'\1\n\2# Remove keyboard from previous message only after successful message creation\n\2await self._remove_keyboard_after_successful_message(update, context)\n\2\3'
        )
    ]
    
    # Apply patterns
    for pattern, replacement in patterns_to_replace:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write the updated content back
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Successfully updated keyboard removal logic in all compare button handlers")
    print("📋 Updated handlers:")
    for handler in handlers_to_update:
        print(f"   - {handler}")

if __name__ == "__main__":
    update_keyboard_removal_logic()

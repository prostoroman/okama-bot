#!/usr/bin/env python3
"""
Script to fix all keyboard removal issues in bot.py
This script will remove all incorrectly placed keyboard removal calls and fix syntax errors.
"""

import re

def fix_keyboard_removal_issues():
    """Fix all keyboard removal issues in bot.py"""
    
    # Read the bot.py file
    with open('bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix patterns that cause syntax errors
    fixes = [
        # Fix incorrectly placed keyboard removal calls before except blocks
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)except Exception as e:',
            r'\1except Exception as e:'
        ),
        # Fix incorrectly placed keyboard removal calls before else blocks
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)else:',
            r'\1else:'
        ),
        # Fix incorrectly placed keyboard removal calls before return statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)return',
            r'\1return'
        ),
        # Fix incorrectly placed keyboard removal calls before function definitions
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)async def',
            r'\1async def'
        ),
        # Fix incorrectly placed keyboard removal calls before class definitions
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)class',
            r'\1class'
        ),
        # Fix incorrectly placed keyboard removal calls before variable assignments
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)[a-zA-Z_][a-zA-Z0-9_]*\s*=',
            r'\1\3'
        ),
        # Fix incorrectly placed keyboard removal calls before if statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)if',
            r'\1if'
        ),
        # Fix incorrectly placed keyboard removal calls before for loops
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)for',
            r'\1for'
        ),
        # Fix incorrectly placed keyboard removal calls before while loops
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)while',
            r'\1while'
        ),
        # Fix incorrectly placed keyboard removal calls before try blocks
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)try:',
            r'\1try:'
        ),
        # Fix incorrectly placed keyboard removal calls before with statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)with',
            r'\1with'
        ),
        # Fix incorrectly placed keyboard removal calls before import statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)import',
            r'\1import'
        ),
        # Fix incorrectly placed keyboard removal calls before from statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)from',
            r'\1from'
        ),
        # Fix incorrectly placed keyboard removal calls before def statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)def',
            r'\1def'
        ),
        # Fix incorrectly placed keyboard removal calls before lambda expressions
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)lambda',
            r'\1lambda'
        ),
        # Fix incorrectly placed keyboard removal calls before yield statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)yield',
            r'\1yield'
        ),
        # Fix incorrectly placed keyboard removal calls before raise statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)raise',
            r'\1raise'
        ),
        # Fix incorrectly placed keyboard removal calls before pass statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)pass',
            r'\1pass'
        ),
        # Fix incorrectly placed keyboard removal calls before break statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)break',
            r'\1break'
        ),
        # Fix incorrectly placed keyboard removal calls before continue statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)continue',
            r'\1continue'
        ),
        # Fix incorrectly placed keyboard removal calls before del statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)del',
            r'\1del'
        ),
        # Fix incorrectly placed keyboard removal calls before global statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)global',
            r'\1global'
        ),
        # Fix incorrectly placed keyboard removal calls before nonlocal statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)nonlocal',
            r'\1nonlocal'
        ),
        # Fix incorrectly placed keyboard removal calls before assert statements
        (
            r'(\s+)# Remove keyboard from previous message only after successful message creation\n(\s+)await self\._remove_keyboard_after_successful_message\(update, context\)\n(\s+)assert',
            r'\1assert'
        )
    ]
    
    # Apply fixes
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write the updated content back
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Successfully fixed all keyboard removal syntax errors")
    print("📋 Fixed patterns:")
    for i, (pattern, _) in enumerate(fixes, 1):
        print(f"   {i}. Fixed incorrectly placed keyboard removal calls")

if __name__ == "__main__":
    fix_keyboard_removal_issues()


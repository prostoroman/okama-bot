#!/usr/bin/env python3
"""
Security check script for API keys and sensitive data
"""

import os
import re
import sys
from pathlib import Path


def check_for_secrets():
    """Check for potential secrets in the codebase"""
    print("🔍 Checking for potential secrets...")
    
    # Patterns to look for
    secret_patterns = [
        r'AIzaSy[A-Za-z0-9_-]{35}',  # Google API keys
        r'sk-[A-Za-z0-9]{48}',       # OpenAI API keys
        r'[A-Za-z0-9]{32,}',         # Generic long strings
        r'Bearer [A-Za-z0-9_-]+',    # Bearer tokens
        r'api[_-]?key["\']?\s*[:=]\s*["\'][A-Za-z0-9_-]+["\']',  # API key patterns
        r'token["\']?\s*[:=]\s*["\'][A-Za-z0-9_-]+["\']',        # Token patterns
    ]
    
    # Files to check
    files_to_check = [
        'bot.py',
        'config.py',
        'services/',
        'tests/',
        'scripts/',
    ]
    
    issues_found = []
    
    for pattern_name in files_to_check:
        if os.path.isfile(pattern_name):
            check_file(pattern_name, secret_patterns, issues_found)
        elif os.path.isdir(pattern_name):
            for root, dirs, files in os.walk(pattern_name):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        check_file(file_path, secret_patterns, issues_found)
    
    if issues_found:
        print("❌ Potential secrets found:")
        for issue in issues_found:
            print(f"  - {issue}")
        return False
    else:
        print("✅ No secrets found")
        return True


def check_file(file_path, patterns, issues_found):
    """Check a single file for secrets"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Skip test files with obvious test patterns
                        if any(test_pattern in line.lower() for test_pattern in ['test', 'example', 'mock', 'fake', 'valid_key', 'test_key']):
                            continue
                        
                        # Skip comments and documentation
                        if line.strip().startswith('#') or line.strip().startswith('"""') or line.strip().startswith("'''"):
                            continue
                        
                        # Skip regex patterns in security check script itself
                        if 'security_check.py' in file_path and 'r\'' in line:
                            continue
                        
                        issues_found.append(f"{file_path}:{i} - {line.strip()}")
                        
    except Exception as e:
        print(f"Warning: Could not check {file_path}: {e}")


def check_gitignore():
    """Check if .gitignore has proper security patterns"""
    print("🔍 Checking .gitignore security patterns...")
    
    gitignore_path = '.gitignore'
    if not os.path.exists(gitignore_path):
        print("❌ .gitignore not found")
        return False
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    required_patterns = [
        'config.env',
        '*.env',
        '*api_key*',
        '*token*',
        '*secret*',
        '*.json',
    ]
    
    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"❌ Missing patterns in .gitignore: {missing_patterns}")
        return False
    else:
        print("✅ .gitignore has proper security patterns")
        return True


def check_config_files():
    """Check if config files contain real secrets"""
    print("🔍 Checking config files...")
    
    config_files = ['config.env', 'config_files/config.env.example']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
                
                # Check for real API keys (not example ones)
                if 'AIzaSy' in content and 'example' not in content and 'test' not in content:
                    print(f"❌ Real API key found in {config_file}")
                    return False
    
    print("✅ Config files are safe")
    return True


def main():
    """Main security check function"""
    print("🛡️  Security Check for okama-bot")
    print("=" * 40)
    
    checks = [
        check_gitignore,
        check_config_files,
        check_for_secrets,
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All security checks passed!")
        sys.exit(0)
    else:
        print("❌ Security issues found!")
        sys.exit(1)


if __name__ == '__main__':
    main()

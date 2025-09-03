#!/usr/bin/env python3
"""
Python Command Helper Script
This script ensures the correct Python command is used from the virtual environment.
"""

import sys
import os
import subprocess
from pathlib import Path

def get_python_command():
    """Get the correct Python command to use."""
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # We're in a virtual environment, use the current Python
        return sys.executable
    
    # Check if .venv exists and use it
    venv_python = Path('.venv/Scripts/python.exe')
    if venv_python.exists():
        return str(venv_python)
    
    # Fallback to system Python
    return 'python'

def run_command(command_args):
    """Run a Python command with the correct interpreter."""
    python_cmd = get_python_command()
    full_command = [python_cmd] + command_args
    
    print(f"Running: {' '.join(full_command)}")
    print(f"Using Python: {python_cmd}")
    
    try:
        result = subprocess.run(full_command, check=True, capture_output=True, text=True)
        print(result.stdout)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"stderr: {e.stderr}")
        return e.returncode

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_python.py <command> [args...]")
        print("Examples:")
        print("  python scripts/run_python.py bot.py")
        print("  python scripts/run_python.py -m unittest discover tests/ -v")
        print("  python scripts/run_python.py scripts/start_bot.py")
        return 1
    
    command_args = sys.argv[1:]
    return run_command(command_args)

if __name__ == "__main__":
    sys.exit(main())

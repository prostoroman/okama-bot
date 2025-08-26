# Tests for Okama Finance Bot

This directory contains tests for the Okama Finance Bot project.

## Running Tests

### Local Development

To run tests locally, use one of these commands:

```bash
# Run all tests with unittest
python3 -m unittest discover tests/ -v

# Run specific test file
python3 -m unittest tests.test_bot -v

# Run specific test class
python3 -m unittest tests.test_bot.TestBotImports -v

# Run specific test method
python3 -m unittest tests.test_bot.TestBotImports.test_bot_import -v
```

### GitHub Actions

Tests are automatically run on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

## Test Structure

- `test_bot.py` - Tests for bot imports and basic functionality
- `test_config.py` - Tests for configuration module
- `__init__.py` - Package initialization

## Test Coverage

Current tests cover:
- ✅ Module imports
- ✅ Basic class instantiation
- ✅ Configuration loading
- ✅ Health check functionality

## Adding New Tests

When adding new tests:

1. Create a new file `test_*.py` in the `tests/` directory
2. Follow the naming convention: `test_*.py` for files, `Test*` for classes, `test_*` for methods
3. Import the modules you want to test
4. Use `unittest.TestCase` as the base class
5. Add meaningful test method names and docstrings

## Example Test

```python
import unittest
from your_module import YourClass

class TestYourClass(unittest.TestCase):
    """Test YourClass functionality"""
    
    def test_something(self):
        """Test that something works correctly"""
        instance = YourClass()
        result = instance.do_something()
        self.assertEqual(result, expected_value)
```

## Notes

- Tests use `unittest` instead of `pytest` for better compatibility
- Tests are designed to run without external dependencies (like actual API keys)
- Import tests verify that all required modules can be loaded
- Tests are lightweight and fast to run

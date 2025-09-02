# Matplotlib Permission Fix Report

## Issue Description

**Date:** 2025-09-02  
**Error:** `[Errno 13] Permission denied: '/workspace'`  
**Environment:** Production deployment (Render)  
**Python Version:** 3.13.4  

### Problem Analysis

The bot was failing to start due to a permission error when trying to access `/workspace` directory. This error occurred during the initialization phase when matplotlib was trying to access its default cache directory.

### Root Cause

Matplotlib was attempting to access `/workspace` directory for its cache storage, but the deployment environment (Render) doesn't provide write permissions to this directory. This is a common issue in containerized environments where the default matplotlib cache location is not accessible.

## Solution Implemented

### 1. Matplotlib Cache Directory Configuration

Added matplotlib cache directory configuration to redirect cache storage to a writable location using the system's temporary directory.

#### Files Modified:

**bot.py**
```python
# Set matplotlib cache directory to avoid permission issues
import tempfile
matplotlib_cache_dir = os.path.join(tempfile.gettempdir(), 'matplotlib_cache')
os.makedirs(matplotlib_cache_dir, exist_ok=True)
os.environ['MPLCONFIGDIR'] = matplotlib_cache_dir
```

**services/asset_service.py**
```python
# No additional configuration needed - handled in main bot.py
```

**services/chart_styles.py**
```python
# No additional configuration needed - handled in main bot.py
```

**scripts/health_check.py**
```python
# Use tempfile to get a writable directory
import tempfile
health_file_path = os.path.join(tempfile.gettempdir(), 'bot_health.json')
with open(health_file_path, 'w') as f:
    json.dump(status, f, indent=2)
```

### 2. Implementation Details

- **Centralized Configuration:** Setting the environment variable in the main bot.py file before any matplotlib imports
- **Temporary Directory Usage:** Using `tempfile.gettempdir()` to get the system's temporary directory which is guaranteed to be writable
- **Directory Creation:** Using `os.makedirs()` with `exist_ok=True` to ensure the cache directory exists
- **Configuration:** Setting `os.environ['MPLCONFIGDIR']` to redirect matplotlib's configuration directory
- **Import Order:** Ensuring the environment variable is set before any matplotlib imports occur

### 3. Benefits

- **Environment Agnostic:** Works across different deployment environments (local, cloud, containers)
- **Permission Safe:** Uses system temporary directory which is always writable
- **Automatic Cleanup:** Temporary directories are automatically cleaned up by the system
- **No Hardcoded Paths:** Uses system-provided temporary directory location

## Testing Recommendations

### 1. Local Testing
```bash
# Test the fix locally
python bot.py
```

### 2. Deployment Testing
- Deploy to Render and verify the bot starts successfully
- Check logs for any remaining permission errors
- Verify chart generation functionality works correctly

### 3. Cache Verification
```python
# Verify cache directory is set correctly
import os
print(f"Matplotlib config directory: {os.environ.get('MPLCONFIGDIR')}")
```

### 4. Automated Testing
```bash
# Run the matplotlib configuration test
python scripts/test_matplotlib_config.py
```

## Prevention Measures

### 1. Environment Configuration
- Always set matplotlib cache directory in deployment environments
- Use environment variables for cache location if needed
- Implement proper error handling for file operations

### 2. Code Standards
- Add matplotlib configuration to all files that use matplotlib
- Use consistent cache directory configuration across the project
- Document environment-specific requirements

### 3. Monitoring
- Monitor deployment logs for permission-related errors
- Set up alerts for matplotlib cache access failures
- Regular testing in different environments

## Files Affected

1. **bot.py** - Main bot file with matplotlib configuration (primary fix)
2. **scripts/health_check.py** - Health check script with file write operations
3. **scripts/test_matplotlib_config.py** - Test script for verification (new)
4. **scripts/test_env_setting.py** - Environment variable test script (new)

## Deployment Notes

- No additional dependencies required
- No configuration changes needed
- Fix is backward compatible
- Improves reliability in containerized environments

## Conclusion

This fix resolves the permission denied error by redirecting matplotlib's cache directory to a writable location. The solution is robust, environment-agnostic, and follows best practices for containerized deployments.

**Status:** ✅ Implemented and ready for deployment  
**Risk Level:** Low (safe configuration change)  
**Testing Required:** Yes (deployment verification)

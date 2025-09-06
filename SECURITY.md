# Security Guidelines

## 🔒 API Key Protection

This repository contains sensitive API keys and credentials. Follow these guidelines to prevent accidental exposure.

## ⚠️ Critical Rules

### 1. Never commit real API keys
- ❌ **NEVER** put real API keys in test files
- ❌ **NEVER** commit `config.env` with real credentials
- ❌ **NEVER** use real keys in examples or documentation

### 2. Always use test data
- ✅ Use `test_api_key` or `AIzaSyTestKey...` in tests
- ✅ Use `your_api_key_here` in examples
- ✅ Mark test data clearly with comments

### 3. Check before committing
```bash
# Run security check before committing
python3 scripts/security_check.py

# Check git status
git status

# Review changes
git diff
```

## 🛡️ Security Tools

### Pre-commit Hooks
Install pre-commit hooks to automatically check for secrets:
```bash
pip install pre-commit
pre-commit install
```

### Manual Security Check
Run the security check script:
```bash
python3 scripts/security_check.py
```

### Detect Secrets
Use detect-secrets to scan for secrets:
```bash
pip install detect-secrets
detect-secrets scan --baseline .secrets.baseline
```

## 📁 Protected Files

The following files are automatically ignored by git:
- `config.env` - Contains real API keys
- `*.env` - Environment files
- `*api_key*` - Files with API keys
- `*token*` - Files with tokens
- `*secret*` - Files with secrets
- `*.json` - JSON files (may contain credentials)

## 🔍 What to Check

Before committing, verify:
1. No real API keys in test files
2. No credentials in documentation
3. No sensitive data in examples
4. All test data is clearly marked

## 🚨 If You Find a Secret

If you accidentally commit a secret:

1. **Immediately** remove it from the file
2. **Force push** to overwrite history:
   ```bash
   git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch FILENAME' --prune-empty --tag-name-filter cat -- --all
   git push origin main --force
   ```
3. **Rotate** the compromised key
4. **Notify** the team

## 📋 Checklist

Before each commit:
- [ ] Run `python3 scripts/security_check.py`
- [ ] Check `git status` for ignored files
- [ ] Review all changes in `git diff`
- [ ] Ensure no real credentials in tests
- [ ] Verify .gitignore is up to date

## 🔧 Configuration

### Environment Variables
Store all sensitive data in environment variables:
```bash
export GEMINI_API_KEY="your_real_key_here"
export TELEGRAM_BOT_TOKEN="your_real_token_here"
```

### Config Files
Use `config.env.example` as a template:
```bash
cp config_files/config.env.example config.env
# Edit config.env with your real values
# config.env is automatically ignored by git
```

## 📞 Support

If you have security concerns or questions:
1. Check this document first
2. Run the security check script
3. Review the security report in `reports/`
4. Contact the maintainer

## 🎯 Best Practices

1. **Use test data** in all test files
2. **Mark test data** clearly with comments
3. **Regular security checks** before commits
4. **Rotate keys** regularly
5. **Monitor** for accidental exposures
6. **Use pre-commit hooks** for automation

Remember: **Security is everyone's responsibility!**

# Dual Environment Deployment Setup

**Date:** 2025-09-20  
**Purpose:** Configure separate DEV and PROD deployments on Render  
**Status:** ✅ CONFIGURED

## Overview

The project now supports dual environment deployment:
- **Development (DEV)**: Deploys from `DEV` branch to Render Development service
- **Production (PROD)**: Deploys from `main` branch to Render Production service

## GitHub Actions Workflows

### 1. Development Deployment (`deploy-dev.yml`)

**Triggers:**
- Push to `DEV` branch
- Manual workflow dispatch

**Configuration:**
- Service ID: `RENDER_DEV_SERVICE_ID` (GitHub Secret)
- Token: `RENDER_TOKEN` (GitHub Secret)
- Branch: `DEV`

### 2. Production Deployment (`auto-deploy.yml`)

**Triggers:**
- Push to `main` branch
- Manual workflow dispatch

**Configuration:**
- Service ID: `RENDER_SERVICE_ID` (GitHub Secret)
- Token: `RENDER_TOKEN` (GitHub Secret)
- Branch: `main`

## Required GitHub Secrets

You need to configure the following secrets in your GitHub repository:

1. **RENDER_TOKEN**: Your Render API token
2. **RENDER_SERVICE_ID**: Production service ID on Render
3. **RENDER_DEV_SERVICE_ID**: Development service ID on Render

### How to Set Up Secrets:

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Add the following secrets:
   - `RENDER_TOKEN`: Your Render API token
   - `RENDER_SERVICE_ID`: Your production service ID
   - `RENDER_DEV_SERVICE_ID`: Your development service ID

## Deployment Scripts

### Development Deployment
```bash
./scripts/auto-deploy.sh
```
- Commits changes to DEV branch
- Triggers development deployment

### Production Deployment
```bash
./scripts/auto-deploy-prod.sh
```
- Commits changes to main branch
- Triggers production deployment

## Workflow

### Development Workflow:
1. Make changes in DEV branch
2. Run `./scripts/auto-deploy.sh` or push directly to DEV
3. GitHub Actions triggers development deployment
4. Changes deployed to Render Development service

### Production Workflow:
1. Merge DEV changes to main branch
2. Run `./scripts/auto-deploy-prod.sh` or push directly to main
3. GitHub Actions triggers production deployment
4. Changes deployed to Render Production service

## Render Service Configuration

### Development Service:
- **Purpose**: Testing and development
- **Branch**: DEV
- **URL**: Your development service URL
- **Auto-deploy**: Enabled for DEV branch

### Production Service:
- **Purpose**: Live production environment
- **Branch**: main
- **URL**: Your production service URL
- **Auto-deploy**: Enabled for main branch

## Benefits

1. **Isolated Environments**: DEV and PROD are completely separate
2. **Safe Testing**: Test changes in DEV before promoting to PROD
3. **Automated Deployment**: Both environments deploy automatically
4. **Easy Rollback**: Can easily revert changes in either environment
5. **Parallel Development**: Multiple developers can work on DEV simultaneously

## Usage Examples

### Deploy to Development:
```bash
# Make your changes
git add .
git commit -m "New feature for testing"
git push origin DEV
# OR
./scripts/auto-deploy.sh
```

### Deploy to Production:
```bash
# Merge DEV to main
git checkout main
git merge DEV
git push origin main
# OR
./scripts/auto-deploy-prod.sh
```

## Monitoring

- **GitHub Actions**: Monitor deployment status in Actions tab
- **Render Dashboard**: Check service status and logs
- **Bot Logs**: Monitor bot behavior in each environment

## Troubleshooting

### Common Issues:

1. **Missing Secrets**: Ensure all required GitHub secrets are configured
2. **Service IDs**: Verify correct service IDs for DEV and PROD
3. **Branch Names**: Ensure branch names match workflow triggers
4. **Permissions**: Check Render API token permissions

### Debug Steps:

1. Check GitHub Actions logs
2. Verify Render service status
3. Check bot logs in respective environment
4. Validate secret configuration

---

**Configuration Status:** ✅ COMPLETE  
**Next Steps:** Configure GitHub secrets and test deployment

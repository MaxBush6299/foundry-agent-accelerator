# Troubleshooting Guide

This guide provides solutions to common issues you may encounter when running the Foundry Agent Accelerator.

---

## Authentication Issues

### "AzureCliCredential authentication failed"

**Problem**: The app can't authenticate with Azure.

**Solutions**:
1. Make sure you're logged in: `az login`
2. If you have multiple tenants, set `AZURE_TENANT_ID` in your `.env` file
3. Verify your Azure CLI is up to date: `az upgrade`

### "DefaultAzureCredential failed"

**Problem**: None of the credential types could authenticate.

**Solution**: For local development, use Azure CLI authentication:
```bash
az login
```

---

## Agent Creation Issues

### "Agent not found" or "create_version failed"

**Problem**: The agent couldn't be created in Foundry.

**Solutions**:
1. Verify `AZURE_EXISTING_AIPROJECT_ENDPOINT` is correct
2. Check that your Azure account has access to the Foundry project
3. Ensure the model deployment name (`AZURE_AI_CHAT_DEPLOYMENT_NAME`) exists

### "Model deployment not found"

**Problem**: The specified chat model doesn't exist.

**Solution**: 
1. Go to your Azure AI Foundry project
2. Click "Deployments" 
3. Verify the model name matches your `AZURE_AI_CHAT_DEPLOYMENT_NAME`

---

## Frontend Issues

### 404 errors for `/static/react/assets/*`

**Problem**: The React frontend hasn't been built.

**Solution**:
```bash
cd src/frontend
npm install --legacy-peer-deps
npm run build
```

### Chat not responding / Spinning forever

**Problem**: The backend isn't running or can't reach Foundry.

**Solutions**:
1. Check the terminal for error messages
2. Verify the backend is running on http://127.0.0.1:8000
3. Open browser dev tools (F12) → Network tab to see failed requests

---

## Environment Issues

### "Missing required environment variable"

**Problem**: A required `.env` variable isn't set.

**Solution**: Make sure these are set in `src/.env`:
```
AZURE_EXISTING_AIPROJECT_ENDPOINT=https://...
AZURE_AI_CHAT_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_AI_AGENT_NAME=my-agent
```

### Changes to system.txt not taking effect

**Problem**: The agent isn't updating when you change the prompt.

**Solution**: Restart the server - a new agent version is only created on startup.

---

## Getting Help

If you continue to experience issues:

1. Check the [Azure AI Foundry documentation](https://learn.microsoft.com/azure/ai-foundry/)
2. Review the server logs in your terminal
3. Use browser dev tools (F12) to inspect network requests

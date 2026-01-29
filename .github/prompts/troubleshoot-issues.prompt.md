---
description: Debug and troubleshoot common issues in the Foundry Agent Accelerator
name: troubleshoot
agent: agent
tools:
  - terminal
  - codebase
  - problems
---

# Troubleshoot Common Issues

Debug and fix common issues in the Foundry Agent Accelerator.

## Quick Diagnostics

Run these commands to gather diagnostic information:

```bash
# Check Python version
python --version  # Should be 3.10+

# Check if environment variables are set
cd src
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Endpoint:', os.getenv('AZURE_EXISTING_AIPROJECT_ENDPOINT', 'NOT SET'))"

# Test Azure authentication
az account show

# Check if the app starts
cd src
uvicorn api.main:app --reload
```

## Common Issues

### 1. Agent Not Found / Not Creating

**Symptoms:**
- Error: "Agent not found"
- Agent doesn't appear in Foundry portal

**Solutions:**

```bash
# 1. Check agent name is set
echo $AZURE_AI_AGENT_NAME

# 2. Verify endpoint is correct
echo $AZURE_EXISTING_AIPROJECT_ENDPOINT

# 3. Check AGENT_CONFIG_SOURCE
# If "portal", the agent must already exist in Foundry
echo $AGENT_CONFIG_SOURCE

# 4. Check logs for creation errors
# Look for "CREATING/UPDATING AGENT" in startup logs
```

### 2. Authentication Errors

**Symptoms:**
- "DefaultAzureCredential failed"
- "AuthenticationError"

**Solutions:**

```bash
# 1. Login to Azure CLI
az login

# 2. Set correct subscription
az account set --subscription <your-subscription-id>

# 3. Verify you have access to the Foundry project
az ai project show --name <project-name> --resource-group <rg>

# 4. For local development, try explicit CLI credential
# In main.py, temporarily use:
# credential = AzureCliCredential()
```

### 3. Model Deployment Not Found

**Symptoms:**
- Error: "Deployment not found"
- "Model deployment does not exist"

**Solutions:**

```bash
# 1. Verify deployment name
echo $AZURE_AI_CHAT_DEPLOYMENT_NAME

# 2. Check deployment exists in Foundry portal
# Go to: Azure AI Foundry > Your Project > Deployments

# 3. Ensure model is deployed (not just selected)
# Deployment should show "Succeeded" status
```

### 4. Streaming Not Working

**Symptoms:**
- Response appears all at once (not word-by-word)
- Frontend shows loading forever

**Solutions:**

```python
# 1. Check backend is using StreamingResponse
# In routes.py, verify the /chat endpoint returns:
return StreamingResponse(generate(), media_type="text/event-stream")

# 2. Check frontend is processing stream correctly
# In AgentPreview.tsx, verify ReadableStream handling

# 3. Check for proxy issues (if behind reverse proxy)
# May need to disable response buffering
```

### 5. Tools Not Working

**Symptoms:**
- Agent doesn't use code interpreter
- Bing search not returning results

**Solutions:**

```yaml
# 1. Verify tool is enabled in agent.yaml
tools:
  code_interpreter:
    enabled: true  # Must be true

# 2. For connection-based tools, verify connection name
bing_search:
  enabled: true
  connection_name: "exact-connection-name"  # Must match Foundry

# 3. Check Foundry connections
# Go to: Azure AI Foundry > Your Project > Connections
```

### 6. Frontend Build Errors

**Symptoms:**
- TypeScript errors
- Module not found

**Solutions:**

```bash
# 1. Clean install dependencies
cd src/frontend
rm -rf node_modules pnpm-lock.yaml
pnpm install

# 2. Check TypeScript version
pnpm exec tsc --version

# 3. Rebuild
pnpm build

# 4. Check for missing types
pnpm add -D @types/react @types/react-dom
```

### 7. CORS Errors

**Symptoms:**
- "CORS policy" errors in browser console
- API calls blocked

**Solutions:**

```python
# 1. Check CORS middleware in main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 8. Agent Version Spam

**Symptoms:**
- New version created on every restart
- Many versions in Foundry portal

**Solutions:**

```python
# The accelerator uses hash-based detection
# Check if config files have hidden changes:

# 1. Check for trailing whitespace/newlines
cat -A src/api/prompts/system.txt

# 2. Verify agent.yaml is consistent
git diff src/agent.yaml

# 3. Check hash computation in logs
# Look for "Config hash:" in startup logs
```

### 9. Container Deployment Issues

**Symptoms:**
- Container won't start
- Health checks failing

**Solutions:**

```bash
# 1. Check container logs
az containerapp logs show --name <app> --resource-group <rg> --follow

# 2. Verify environment variables are set
az containerapp show --name <app> --resource-group <rg> \
  --query "properties.template.containers[0].env"

# 3. Check managed identity permissions
az role assignment list --assignee <identity-principal-id>

# 4. Test image locally first
docker run -p 8000:8000 \
  -e AZURE_EXISTING_AIPROJECT_ENDPOINT=... \
  -e AZURE_AI_CHAT_DEPLOYMENT_NAME=... \
  foundry-agent-accelerator:latest
```

## Logging

Enable debug logging for more information:

```python
# In main.py or routes.py
import logging
logging.getLogger("azure").setLevel(logging.DEBUG)
logging.getLogger("foundry-agent").setLevel(logging.DEBUG)
```

## Getting Help

1. Check the [troubleshooting docs](docs/troubleshooting.md)
2. Review startup logs for error messages
3. Check Azure AI Foundry portal for agent status
4. Verify all environment variables are set correctly

## Checklist

- [ ] Python 3.10+ installed
- [ ] Azure CLI logged in
- [ ] Environment variables set in `.env`
- [ ] Model deployed in Foundry
- [ ] Agent name configured
- [ ] Connections set up (if using tools)
- [ ] Frontend dependencies installed
- [ ] No TypeScript errors

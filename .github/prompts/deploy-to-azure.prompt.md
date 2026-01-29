---
description: Deploy the Foundry Agent Accelerator to Azure Container Apps
name: deploy-to-azure
agent: agent
tools:
  - terminal
  - changes
---

# Deploy to Azure

Deploy the Foundry Agent Accelerator to Azure Container Apps.

## Prerequisites

- Azure CLI installed and logged in (`az login`)
- Azure subscription with appropriate permissions
- Azure AI Foundry project created
- Container registry (ACR) for storing the Docker image

## Deployment Options

### Option 1: Azure Developer CLI (azd)

The fastest way to deploy if you have `azd` installed:

```bash
# Initialize (first time only)
azd init

# Deploy
azd up
```

### Option 2: Manual Deployment

#### Step 1: Build Docker Image

```bash
cd src

# Build the image
docker build -t foundry-agent-accelerator:latest .

# Tag for your registry
docker tag foundry-agent-accelerator:latest <your-acr>.azurecr.io/foundry-agent-accelerator:latest
```

#### Step 2: Push to Azure Container Registry

```bash
# Login to ACR
az acr login --name <your-acr>

# Push image
docker push <your-acr>.azurecr.io/foundry-agent-accelerator:latest
```

#### Step 3: Deploy to Container Apps

```bash
# Create Container App
az containerapp create \
  --name foundry-agent \
  --resource-group <your-rg> \
  --environment <your-container-app-env> \
  --image <your-acr>.azurecr.io/foundry-agent-accelerator:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server <your-acr>.azurecr.io \
  --env-vars \
    AZURE_EXISTING_AIPROJECT_ENDPOINT=<your-endpoint> \
    AZURE_AI_CHAT_DEPLOYMENT_NAME=<your-model> \
    AZURE_AI_AGENT_NAME=<agent-name> \
    AGENT_CONFIG_SOURCE=local
```

## Environment Variables for Production

Set these environment variables in your Container App:

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_EXISTING_AIPROJECT_ENDPOINT` | Foundry project connection string | Yes |
| `AZURE_AI_CHAT_DEPLOYMENT_NAME` | Deployed model name (e.g., gpt-4o) | Yes |
| `AZURE_AI_AGENT_NAME` | Name for your agent | Yes |
| `AGENT_CONFIG_SOURCE` | `local` or `portal` | No (default: local) |
| `WEB_APP_USERNAME` | Basic auth username | No |
| `WEB_APP_PASSWORD` | Basic auth password | No |

## Managed Identity Setup

For production, use Managed Identity instead of connection strings:

1. Enable system-assigned managed identity on Container App
2. Grant the identity access to:
   - Azure AI Foundry project (Contributor)
   - Any connected resources (Search, Bing, etc.)

```bash
# Enable managed identity
az containerapp identity assign \
  --name foundry-agent \
  --resource-group <your-rg> \
  --system-assigned

# Get identity principal ID
PRINCIPAL_ID=$(az containerapp identity show \
  --name foundry-agent \
  --resource-group <your-rg> \
  --query principalId -o tsv)

# Assign role to Foundry project
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Contributor" \
  --scope <foundry-project-resource-id>
```

## Production Configuration

### Enable Basic Auth

For public deployments, enable basic authentication:

```bash
az containerapp update \
  --name foundry-agent \
  --resource-group <your-rg> \
  --set-env-vars \
    WEB_APP_USERNAME=admin \
    WEB_APP_PASSWORD=<secure-password>
```

### Use Portal Mode

For production where business users manage the agent:

```bash
az containerapp update \
  --name foundry-agent \
  --resource-group <your-rg> \
  --set-env-vars \
    AGENT_CONFIG_SOURCE=portal
```

### Scale Configuration

```bash
# Set min/max replicas
az containerapp update \
  --name foundry-agent \
  --resource-group <your-rg> \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 0.5 \
  --memory 1Gi
```

## Updating the Deployment

```bash
# Build new image
docker build -t <your-acr>.azurecr.io/foundry-agent-accelerator:v2 .

# Push
docker push <your-acr>.azurecr.io/foundry-agent-accelerator:v2

# Update Container App
az containerapp update \
  --name foundry-agent \
  --resource-group <your-rg> \
  --image <your-acr>.azurecr.io/foundry-agent-accelerator:v2
```

## Monitoring

### View Logs

```bash
az containerapp logs show \
  --name foundry-agent \
  --resource-group <your-rg> \
  --follow
```

### Check Health

```bash
# Get the app URL
URL=$(az containerapp show \
  --name foundry-agent \
  --resource-group <your-rg> \
  --query properties.configuration.ingress.fqdn -o tsv)

# Test the endpoint
curl https://$URL/
```

## Checklist

- [ ] Docker image built and tested locally
- [ ] Image pushed to Azure Container Registry
- [ ] Container App created with correct settings
- [ ] Environment variables configured
- [ ] Managed Identity enabled and granted permissions
- [ ] Basic auth enabled (if public)
- [ ] Logs showing successful startup
- [ ] Endpoint accessible and working

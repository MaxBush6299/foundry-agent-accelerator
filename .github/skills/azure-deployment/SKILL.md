---
name: azure-deployment
description: Skill for deploying the Foundry Agent Accelerator to Azure. Use when deploying to Azure Container Apps, configuring managed identity, setting up CI/CD, or troubleshooting deployment issues.
---

# Azure Deployment Skill

This skill provides guidance for deploying the Foundry Agent Accelerator to Azure.

## Deployment Options

### Option 1: Azure Developer CLI (Recommended)

```bash
# Initialize (first time only)
azd init

# Deploy everything
azd up
```

### Option 2: Manual Docker Deployment

## Step 1: Build Docker Image

```bash
cd src

# Build the image
docker build -t foundry-agent-accelerator:latest .

# Tag for your registry
docker tag foundry-agent-accelerator:latest <your-acr>.azurecr.io/foundry-agent-accelerator:latest
```

## Step 2: Push to Azure Container Registry

```bash
# Login to ACR
az acr login --name <your-acr>

# Push image
docker push <your-acr>.azurecr.io/foundry-agent-accelerator:latest
```

## Step 3: Deploy to Container Apps

```bash
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

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_EXISTING_AIPROJECT_ENDPOINT` | Foundry project connection string | Yes |
| `AZURE_AI_CHAT_DEPLOYMENT_NAME` | Deployed model name | Yes |
| `AZURE_AI_AGENT_NAME` | Name for your agent | Yes |
| `AGENT_CONFIG_SOURCE` | `local` or `portal` | No |
| `WEB_APP_USERNAME` | Basic auth username | No |
| `WEB_APP_PASSWORD` | Basic auth password | No |

## Managed Identity Setup

For production, use Managed Identity:

```bash
# Enable system-assigned managed identity
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

```bash
az containerapp update \
  --name foundry-agent \
  --resource-group <your-rg> \
  --set-env-vars \
    WEB_APP_USERNAME=admin \
    WEB_APP_PASSWORD=<secure-password>
```

### Use Portal Mode

```bash
az containerapp update \
  --name foundry-agent \
  --resource-group <your-rg> \
  --set-env-vars \
    AGENT_CONFIG_SOURCE=portal
```

### Scale Configuration

```bash
az containerapp update \
  --name foundry-agent \
  --resource-group <your-rg> \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 0.5 \
  --memory 1Gi
```

## Updating Deployments

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
URL=$(az containerapp show \
  --name foundry-agent \
  --resource-group <your-rg> \
  --query properties.configuration.ingress.fqdn -o tsv)

curl https://$URL/
```

## Troubleshooting

### Container won't start
- Check logs: `az containerapp logs show ...`
- Verify environment variables are set correctly
- Test image locally first with `docker run`

### Authentication errors
- Enable managed identity
- Grant identity proper RBAC roles on Foundry project
- Verify network connectivity to Azure services

### Health checks failing
- Ensure port 8000 is exposed
- Check the app starts successfully in logs
- Verify ingress is configured as external

# Environment Variables Reference

This document explains all the environment variables used by the Foundry Agent Accelerator.

## Quick Reference Table

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_EXISTING_AIPROJECT_ENDPOINT` | ✅ Yes | - | Azure AI Foundry project endpoint |
| `AZURE_AI_CHAT_DEPLOYMENT_NAME` | ✅ Yes | - | Name of your chat model deployment |
| `AZURE_AI_AGENT_NAME` | ✅ Yes | `foundry-accelerator-agent` | Name for your agent in Foundry |
| `AZURE_TENANT_ID` | ❌ No | Auto | Azure tenant ID (usually auto-detected) |
| `AZURE_CLIENT_ID` | ❌ No | Auto | Managed identity client ID (production only) |
| `WEB_APP_USERNAME` | ❌ No | - | Basic auth username |
| `WEB_APP_PASSWORD` | ❌ No | - | Basic auth password |
| `APP_LOG_FILE` | ❌ No | - | Optional log file path |

---

## Required Variables

### `AZURE_EXISTING_AIPROJECT_ENDPOINT`

**Required:** Yes

The URL of your Azure AI Foundry project. This is where your agent will be created and managed.

**Format:** `https://<account-name>.services.ai.azure.com/api/projects/<project-name>`

**How to find it:**
1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Open your project
3. Click on "Overview"
4. Copy the "Project endpoint" value

**Example:**
```
AZURE_EXISTING_AIPROJECT_ENDPOINT=https://myaccount.services.ai.azure.com/api/projects/my-agent-project
```

---

### `AZURE_AI_CHAT_DEPLOYMENT_NAME`

**Required:** Yes

The name of your deployed chat model. This is the AI model that your agent will use.

**How to find it:**
1. Go to your Azure AI Foundry project
2. Click on "Deployments"
3. Copy the name of your chat model deployment

**Common values:**
- `gpt-4o-mini` (recommended for development - lower cost)
- `gpt-4o` (more capable, higher cost)
- `gpt-35-turbo` (legacy, lower cost)

**Example:**
```
AZURE_AI_CHAT_DEPLOYMENT_NAME=gpt-4o-mini
```

---

### `AZURE_AI_AGENT_NAME`

**Required:** Yes (has default)

The name for your agent in Azure AI Foundry. This is how your agent appears in the Foundry portal.

**Default:** `foundry-accelerator-agent`

**Naming tips:**
- Use lowercase with hyphens (e.g., `customer-support-agent`)
- Make it descriptive of the agent's purpose
- Keep it unique within your project

**Example:**
```
AZURE_AI_AGENT_NAME=sales-assistant
```

**What happens:**
- On first run: Agent is created with this name
- On subsequent runs: A new VERSION is created (preserving history)
- In portal: You'll see the agent under "Agents" with version history

---

## Authentication Variables

### `AZURE_TENANT_ID`

**Required:** No (usually auto-detected)

Your Azure Active Directory tenant ID. Only set this if you have multiple Azure tenants and need to specify which one to use.

**When to set:**
- You have access to multiple Azure tenants
- Auto-detection isn't working
- You're getting authentication errors

**Example:**
```
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
```

---

### `AZURE_CLIENT_ID`

**Required:** No (production only)

The client ID of the managed identity used in production deployments. This is automatically set when deploying to Azure and should not be manually configured for local development.

---

### `WEB_APP_USERNAME` and `WEB_APP_PASSWORD`

**Required:** No

Enable basic HTTP authentication to protect your agent. Both must be set for authentication to work.

**Example:**
```
WEB_APP_USERNAME=admin
WEB_APP_PASSWORD=your-secure-password-here
```

**Note:** For production, consider using Azure App Service authentication instead of basic auth.

---

## Logging Variables

### `APP_LOG_FILE`

**Required:** No

Path to a file for logging output. If not set, logs only go to the console.

**Example:**
```
APP_LOG_FILE=/var/log/foundry-agent.log
```

---

## Example `.env` File

Here's a complete example for local development:

```bash
# Required - Your Foundry project
AZURE_EXISTING_AIPROJECT_ENDPOINT=https://myaccount.services.ai.azure.com/api/projects/my-project

# Required - Your deployed model
AZURE_AI_CHAT_DEPLOYMENT_NAME=gpt-4o-mini

# Required - Your agent name (appears in Foundry portal)
AZURE_AI_AGENT_NAME=my-customer-agent

# Optional - Uncomment if needed
# AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
# WEB_APP_USERNAME=admin
# WEB_APP_PASSWORD=secure-password
```

---

## How Variables Are Used

```
┌─────────────────────────────────────────────────────────────┐
│                    ON STARTUP                                │
│                                                              │
│  AZURE_EXISTING_AIPROJECT_ENDPOINT                          │
│         └──▶ Connect to your Foundry project                │
│                                                              │
│  AZURE_AI_AGENT_NAME + AZURE_AI_CHAT_DEPLOYMENT_NAME        │
│         └──▶ Create/update agent with this model            │
│                                                              │
│  prompts/system.txt                                          │
│         └──▶ Agent's instructions (from file, not env var)  │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### "Environment variable not set" error

Make sure you:
1. Created a `.env` file (copy from `.env.template`)
2. Set all required variables
3. Saved the file
4. Restarted the application

### "401 Unauthorized" error

Your Azure credentials may have expired:
```bash
# Re-authenticate
az login
# or
azd auth login
```

### "Agent not found in portal"

Check that:
1. `AZURE_EXISTING_AIPROJECT_ENDPOINT` points to the correct project
2. The app started without errors (check logs)
3. You're looking in the right project in the portal

### Agent exists but has wrong instructions

The instructions come from `prompts/system.txt`, not an environment variable. Edit that file and restart the app to create a new version.

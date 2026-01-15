# Local Development Guide

This guide helps you set up a local development environment to test and modify the Foundry Agent Accelerator.

## Prerequisites

- Python 3.8 or later
- [Node.js](https://nodejs.org/) (v20 or later)
- [pnpm](https://pnpm.io/installation)
- An Azure AI Foundry project with a deployed chat model
- Azure CLI logged in (`az login` or `azd auth login`)

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/MaxBush6299/foundry-agent-accelerator.git
cd foundry-agent-accelerator

# 2. Create and configure environment
cp .env.template src/.env
# Edit src/.env with your Azure details

# 3. Install dependencies
cd src
pip install -r requirements.txt

# 4. Run the server
python -m uvicorn api.main:app --reload
```

Open http://127.0.0.1:8000 in your browser.

---

## Detailed Setup

### 1. Python Environment

Create a [Python virtual environment](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments) and activate it:

**On Windows:**
```shell
python -m venv .venv
.venv\scripts\activate
```

**On Linux/Mac:**
```shell
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

Navigate to the `src` directory and install Python packages:

```shell
cd src
python -m pip install -r requirements.txt
```

**Note:** The `azure-ai-projects` package requires pre-release version `>=2.0.0b1` for agent support.

### 3. Environment Configuration

Copy the template and fill in your values:

```shell
cp .env.template src/.env
```

Edit `src/.env`:

```bash
# Required - Your Foundry project endpoint
AZURE_EXISTING_AIPROJECT_ENDPOINT=https://your-account.services.ai.azure.com/api/projects/your-project

# Required - Your deployed model name
AZURE_AI_CHAT_DEPLOYMENT_NAME=gpt-4o-mini

# Required - Name for your agent in Foundry
AZURE_AI_AGENT_NAME=my-dev-agent

# Optional - If you have multiple Azure tenants
# AZURE_TENANT_ID=your-tenant-id
```

### 4. Frontend Setup (Optional)

If you want to modify the React frontend:

```shell
cd src/frontend
pnpm install
pnpm run setup
```

---

## Running the Development Server

### Start the Server

```shell
cd src
python -m uvicorn api.main:app --reload
```

### What Happens on Startup

When you start the server, you'll see:

```
============================================================
STARTING FOUNDRY AGENT ACCELERATOR
============================================================
Running in LOCAL DEVELOPMENT mode
Using AzureDeveloperCliCredential (default tenant)
Connecting to Azure AI Foundry project: https://...
----------------------------------------
CREATING/UPDATING AGENT IN FOUNDRY
  Agent Name: my-dev-agent
  Model: gpt-4o-mini
  Instructions: You are a helpful assistant...
----------------------------------------
✅ Agent ready!
   ID: asst_abc123xyz
   Name: my-dev-agent
   Version: 1
============================================================
AGENT READY - my-dev-agent (v1)
Agent is visible in Azure AI Foundry portal!
============================================================
```

### Access the Application

Open http://127.0.0.1:8000 in your browser.

---

## Development Workflow

### Updating Your Agent

1. Edit `src/api/prompts/system.txt` with your new instructions
2. Save the file
3. The server will auto-reload (if using `--reload`)
4. A **new version** of your agent is created in Foundry!

### Viewing Agent Versions

1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Open your project
3. Click "Agents" in the sidebar
4. Click on your agent to see version history

### Testing Changes

1. Make changes to `system.txt`
2. Server reloads automatically
3. New agent version created
4. Test in the chat interface
5. Check Foundry portal to see the new version

---

## Frontend Development

### Build the Frontend

If you've modified files in `src/frontend`:

```shell
cd src/frontend
pnpm build
```

The build output goes to `../api/static/react`.

### Key Files for Customization

| File | What to Customize |
|------|-------------------|
| `src/frontend/src/components/App.tsx` | Agent name, description, logo |
| `src/frontend/src/components/agents/AgentPreview.tsx` | Chat behavior and API calls |
| `src/frontend/src/components/agents/chatbot/ChatInput.tsx` | Input field styling |

---

## Troubleshooting

### "DefaultAzureCredential failed"

You need to authenticate with Azure:

```bash
az login
# or
azd auth login
```

### "Agent creation failed"

Check that:
1. `AZURE_EXISTING_AIPROJECT_ENDPOINT` is correct
2. `AZURE_AI_CHAT_DEPLOYMENT_NAME` matches a deployed model in your project
3. You have permissions to create agents in the project

### "Module not found" errors

Make sure you installed the correct package versions:

```bash
pip install --pre azure-ai-projects>=2.0.0b1
```

### Agent not appearing in portal

1. Check the startup logs for errors
2. Verify `AZURE_EXISTING_AIPROJECT_ENDPOINT` points to the right project
3. Make sure the agent name doesn't have invalid characters

---

## Tips for Development

### Use a Separate Agent Name

During development, use a different agent name to avoid affecting your production agent:

```bash
AZURE_AI_AGENT_NAME=my-dev-agent  # Development
AZURE_AI_AGENT_NAME=my-prod-agent # Production
```

### Check Logs

The app logs helpful information:
- Connection status
- Agent creation/version details
- Chat request processing
- Errors and warnings

### Test with Simple Prompts

Start with a simple `system.txt`:

```
You are a helpful assistant.
```

Then gradually add complexity once you confirm the basics work.


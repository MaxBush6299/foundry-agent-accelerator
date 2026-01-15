# Foundry Agent Accelerator

A **beginner-friendly starting point** for building AI agents with Azure AI Foundry. This accelerator creates a **persistent agent** in Foundry that you can customize, version, and manage through both code AND the Azure portal.

> **Perfect for:** Product managers, business analysts, and developers who want to quickly deploy and customize an AI agent without deep Python expertise.

## 🎯 What This Does

This accelerator gives you a **working AI agent** that:
- **Lives in Azure AI Foundry** - Visible and manageable in the portal
- **Has version history** - Every change creates a new version (both in Git AND Foundry)
- **Deploys to Azure** in minutes
- **Customizable** by editing simple text files (no coding required for basic changes)

![Screenshot of the chat interface](docs/images/webapp_screenshot.png)

## ✨ Key Feature: Persistent Agents with Versioning

Unlike simple chat apps, this accelerator creates a **real agent** in Azure AI Foundry:

```
┌─────────────────────────────────────────────────────────────┐
│                    THE FLOW                                  │
│                                                              │
│  Edit system.txt → Restart app → New agent version created  │
│                                                              │
│  ✅ Version history in Git (your code)                       │
│  ✅ Version history in Foundry (operational)                 │
│  ✅ Agent visible in Azure AI Foundry portal                 │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [How to Customize Your Agent](#-how-to-customize-your-agent)
- [Understanding the Architecture](#-understanding-the-architecture)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

- Azure subscription with Azure AI Foundry access
- A deployed chat model (like gpt-4o) in your Foundry project
- Azure CLI or Azure Developer CLI installed

### Option 1: Deploy to Azure (Recommended)

```bash
# 1. Clone this repository
git clone https://github.com/MaxBush6299/foundry-agent-accelerator.git
cd foundry-agent-accelerator

# 2. Login to Azure
azd auth login

# 3. Deploy everything to Azure
azd up
```

After deployment (~10-15 minutes), you'll get a URL to your running agent!

### Option 2: Run Locally

```bash
# 1. Clone and navigate to the project
git clone https://github.com/MaxBush6299/foundry-agent-accelerator.git
cd foundry-agent-accelerator

# 2. Copy and configure environment variables
cp .env.template src/.env
# Edit src/.env with your Azure AI Foundry details

# 3. Install dependencies
cd src
pip install -r requirements.txt

# 4. Run the application
uvicorn api.main:app --reload
```

Open http://localhost:8000 in your browser.

**On startup, you'll see:**
```
============================================================
STARTING FOUNDRY AGENT ACCELERATOR
============================================================
Connecting to Azure AI Foundry project...
----------------------------------------
CREATING/UPDATING AGENT IN FOUNDRY
  Agent Name: my-agent
  Model: gpt-4o-mini
  Instructions: You are a helpful assistant...
----------------------------------------
✅ Agent ready!
   ID: asst_abc123...
   Name: my-agent
   Version: 1
============================================================
AGENT READY - my-agent (v1)
Agent is visible in Azure AI Foundry portal!
============================================================
```

---

## 📁 Project Structure

```
foundry-agent-accelerator/
│
├── src/                          # 🎯 MAIN APPLICATION CODE
│   ├── api/                      # Backend Python code
│   │   ├── main.py              # Creates/updates agent in Foundry on startup
│   │   ├── routes.py            # Chat endpoint (sends messages to agent)
│   │   └── prompts/             # ⭐ EDIT THIS to customize your agent
│   │       └── system.txt       # Your agent's personality & instructions
│   │
│   ├── frontend/                 # Chat interface (React)
│   │   └── src/components/      # UI components
│   │
│   ├── .env.sample              # Template for configuration
│   └── requirements.txt         # Python packages needed
│
├── .env.template                 # Environment variable template
├── infra/                        # Azure infrastructure (Bicep)
└── docs/                         # Documentation
```

---

## ✏️ How to Customize Your Agent

### Change Your Agent's Behavior (No Coding!)

1. Open `src/api/prompts/system.txt`
2. Replace the text with your own instructions
3. Restart the application
4. **A new version of your agent is created in Foundry!**

**Example prompts:**

```
You are a friendly customer support agent for Contoso Electronics.
Help customers with product questions, troubleshooting, and returns.
Always be polite and empathetic. If you don't know something, say so.
```

```
You are a technical documentation assistant. Help developers
understand our API and provide code examples when helpful.
Be concise but thorough. Use markdown formatting in responses.
```

### Change the Agent Name

Set `AZURE_AI_AGENT_NAME` in your `.env` file:

```
AZURE_AI_AGENT_NAME=customer-support-agent
```

This is the name that appears in the Azure AI Foundry portal.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_EXISTING_AIPROJECT_ENDPOINT` | ✅ Yes | Your Azure AI Foundry project URL |
| `AZURE_AI_CHAT_DEPLOYMENT_NAME` | ✅ Yes | Model name (e.g., "gpt-4o-mini") |
| `AZURE_AI_AGENT_NAME` | ✅ Yes | Name for your agent in Foundry |
| `AZURE_TENANT_ID` | ❌ No | Only if you have multiple tenants |

---

## 🧠 Understanding the Architecture

### How It Works

```
┌────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   system.txt   │────▶│   main.py    │────▶│  Foundry Agent  │
│  (your code)   │     │  (creates    │     │  (persistent,   │
│                │     │   version)   │     │   versioned)    │
└────────────────┘     └──────────────┘     └─────────────────┘
                                                     │
┌────────────────┐     ┌──────────────┐              │
│    Frontend    │────▶│  routes.py   │◀─────────────┘
│  (chat UI)     │     │  (sends to   │
│                │     │   agent)     │
└────────────────┘     └──────────────┘
```

### What Happens on Startup

1. **Load instructions** from `prompts/system.txt`
2. **Call `create_version()`** to create/update the agent in Foundry
3. **Agent is now live** and visible in the Foundry portal
4. **Ready to chat** - messages are routed to your agent

### What Happens When You Chat

1. User types a message
2. Frontend sends it to `/chat` endpoint
3. Backend forwards to Foundry Agent (by name)
4. Agent responds using its configured model and instructions
5. Response streams back word-by-word

### Versioning Flow

```
You edit system.txt
        ↓
Commit to Git (code version history)
        ↓
Restart/redeploy app
        ↓
create_version() called
        ↓
New version created in Foundry
        ↓
Both Git AND Foundry have history!
```

---

## 🚢 Deployment

### Deploy to Azure

```bash
azd up
```

This creates:
- Azure Container App (runs your agent)
- Azure AI Services (provides the AI model)
- Container Registry (stores your app)

### Update Your Agent

```bash
# 1. Edit src/api/prompts/system.txt
# 2. Redeploy
azd up
# A new version is created in Foundry!
```

### Clean Up Resources

```bash
azd down
```

---

## ❓ Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| "Agent not created" | Check `AZURE_AI_AGENT_NAME` is set |
| "401 Unauthorized" | Run `azd auth login` or `az login` |
| "Model not found" | Verify `AZURE_AI_CHAT_DEPLOYMENT_NAME` matches your deployment |
| Agent not in portal | Check `AZURE_EXISTING_AIPROJECT_ENDPOINT` is correct |

### Viewing Your Agent in the Portal

1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Open your project
3. Click "Agents" in the sidebar
4. You should see your agent with version history!

---

## 📚 Additional Documentation

- [Environment Variables](docs/environment_variables.md) - All configuration options
- [Code Walkthrough](docs/code_walkthrough.md) - How the code works
- [Deployment Guide](docs/deployment.md) - Detailed deployment instructions
- [Local Development](docs/local_development.md) - Setting up your dev environment

---

## 💰 Resources & Costs

| Resource | Purpose | Pricing |
|----------|---------|---------|
| Azure Container App | Runs your agent | ~$0.03/hour when active |
| Azure AI Services | AI model access | Per-token pricing |
| Container Registry | Stores app image | ~$5/month |

**Tip:** Use `gpt-4o-mini` for lower costs during development.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Based on the [Azure Samples - Get Started with AI Chat](https://github.com/Azure-Samples/get-started-with-ai-chat) template.

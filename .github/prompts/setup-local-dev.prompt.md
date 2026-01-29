---
description: Set up your local development environment for the Foundry Agent Accelerator
name: setup-local-dev
agent: agent
tools:
  - terminal
  - changes
---

# Setup Local Development Environment

Set up your local environment to develop and test the Foundry Agent Accelerator.

## Prerequisites

| Tool | Version | Installation |
|------|---------|--------------|
| Python | 3.10+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| pnpm | 10.6+ | `npm install -g pnpm` |
| Azure CLI | Latest | [Install Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) |
| Git | Latest | [git-scm.com](https://git-scm.com) |

## Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/foundry-agent-accelerator.git
cd foundry-agent-accelerator
```

## Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
cd src
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

```bash
# Copy template
cp .env.template .env

# Edit .env with your values
```

### Required Environment Variables

Create `src/.env` with:

```bash
# Azure AI Foundry Project Connection
# Format: Find this in Azure AI Foundry > Project > Settings > Properties
AZURE_EXISTING_AIPROJECT_ENDPOINT=https://your-project.services.ai.azure.com/discovery

# Your deployed chat model name
AZURE_AI_CHAT_DEPLOYMENT_NAME=gpt-4o-mini

# Name for your agent (visible in Foundry portal)
AZURE_AI_AGENT_NAME=my-dev-agent

# Configuration mode (local = use local files, portal = use Foundry portal)
AGENT_CONFIG_SOURCE=local

# Optional: Basic auth for the web interface
# WEB_APP_USERNAME=admin
# WEB_APP_PASSWORD=your-password
```

## Step 4: Azure Authentication

```bash
# Login to Azure
az login

# Set the correct subscription
az account set --subscription "Your Subscription Name"

# Verify access to your Foundry project
az account show
```

## Step 5: Set Up Frontend (Optional for development)

If you want to modify the React frontend:

```bash
cd src/frontend

# Install dependencies
pnpm install

# Build frontend (outputs to src/api/static/react/)
pnpm build

# Or run in dev mode with hot reload
pnpm dev
```

## Step 6: Run the Application

```bash
cd src

# Run with auto-reload for development
uvicorn api.main:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

## Development Workflow

### Backend Development (Python)

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Run with auto-reload
cd src
uvicorn api.main:app --reload

# The server restarts automatically when you change Python files
```

### Frontend Development (React)

```bash
cd src/frontend

# Run Vite dev server (hot reload)
pnpm dev

# Access frontend at http://localhost:5173
# API proxied to http://localhost:8000
```

### Testing Agent Changes

1. Edit `src/api/prompts/system.txt` for personality changes
2. Edit `src/agent.yaml` for tool configuration
3. Restart the server (Ctrl+C, then run again)
4. Check logs for "CREATING/UPDATING AGENT" to confirm new version

## Directory Structure After Setup

```
foundry-agent-accelerator/
├── .venv/                    # Python virtual environment
├── src/
│   ├── .env                  # Your environment config (not in git)
│   ├── api/
│   │   ├── main.py
│   │   ├── routes.py
│   │   ├── util.py
│   │   └── prompts/
│   │       └── system.txt    # Edit this to change agent personality
│   ├── frontend/
│   │   └── node_modules/     # Frontend dependencies
│   ├── agent.yaml            # Edit this to configure tools
│   └── requirements.txt
└── docs/
```

## VS Code Recommended Extensions

Install these extensions for the best development experience:

- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **ESLint** (dbaeumer.vscode-eslint)
- **Prettier** (esbenp.prettier-vscode)
- **YAML** (redhat.vscode-yaml)
- **Azure Tools** (ms-vscode.vscode-node-azure-pack)

## Troubleshooting Setup

### "Module not found" errors

```bash
# Ensure virtual environment is activated
pip install -r requirements.txt
```

### Azure authentication fails

```bash
# Clear cached credentials
az logout
az login
az account set --subscription "Your Subscription"
```

### Frontend build fails

```bash
# Clear and reinstall
cd src/frontend
rm -rf node_modules pnpm-lock.yaml
pnpm install
pnpm build
```

### Port 8000 already in use

```bash
# Kill process on port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Kill process on port 8000 (macOS/Linux)
lsof -i :8000
kill -9 <pid>
```

## Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] Python dependencies installed
- [ ] `.env` file created with correct values
- [ ] Azure CLI logged in
- [ ] Node.js and pnpm installed (if developing frontend)
- [ ] Frontend dependencies installed (if developing frontend)
- [ ] Application runs at http://localhost:8000
- [ ] Agent appears in Azure AI Foundry portal

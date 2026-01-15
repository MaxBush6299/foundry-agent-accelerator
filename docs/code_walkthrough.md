# Code Walkthrough for Non-Developers

This guide explains how the Foundry Agent Accelerator code works in plain language. No programming experience required!

## The Big Picture

Think of this application like a restaurant with a celebrity chef:

- **Frontend (React)** = The dining room where customers interact
- **Backend (Python)** = The kitchen staff who coordinate everything
- **Foundry Agent** = The celebrity chef who has their own signature style
- **System Prompt** = The chef's recipe book that defines their style

The key difference from a regular chat app: **The chef (agent) is a real person who persists between meals, not just a recipe that gets followed.**

---

## How It All Connects

```
┌─────────────────────────────────────────────────────────────┐
│                    ON STARTUP                                │
│                                                              │
│  1. Read system.txt (the recipe book)                       │
│  2. Register chef with Foundry (create_version)             │
│  3. Chef now exists in Foundry with version history!        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    WHEN CHATTING                             │
│                                                              │
│  1. Customer (user) places order (sends message)            │
│  2. Kitchen (backend) routes to the chef (agent)            │
│  3. Chef prepares dish (generates response)                 │
│  4. Dish served (streamed back to user)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Files and What They Do

### 1. `src/api/prompts/system.txt` - The Recipe Book

**What it is:** A plain text file that defines your agent's personality.

**Why it matters:** This is the easiest thing to change! Edit this file and restart the app to update your agent.

**The magic:** When you restart, a NEW VERSION of your agent is created in Foundry. You get version history both in Git AND in the Foundry portal!

**Example:**
```
You are a helpful customer support agent for Acme Corp.
Be friendly and professional. If you don't know something, 
say "I'll need to check on that for you."
```

---

### 2. `src/api/main.py` - The Kitchen Setup

**What it is:** Code that runs when the application starts.

**What happens:**
1. Loads settings from the `.env` file
2. Logs into Azure using your credentials
3. **Creates or updates the agent in Foundry** ← This is the key step!
4. Gets ready to route messages to the agent

**The important part:**
```python
# This creates a PERSISTENT agent in Foundry
agent = project_client.agents.create_version(
    agent_name="my-agent",
    definition=PromptAgentDefinition(
        model="gpt-4o-mini",
        instructions=load_system_prompt(),  # From system.txt
    ),
)
```

Every time this runs, if you've changed `system.txt`, a new version is created!

---

### 3. `src/api/routes.py` - The Order Processor

**What it is:** Code that handles incoming chat messages.

**The flow:**
```
User message arrives
        ↓
Format message for the agent
        ↓
Send to Foundry Agent (by name)
        ↓
Agent generates response
        ↓
Stream response back to user word-by-word
```

**Key difference from before:** We don't send to a "model" directly. We send to the **agent** which uses the model with its configured instructions.

---

### 4. `src/frontend/src/components/App.tsx` - The Dining Room

**What it is:** The React chat interface that users interact with.

**What you can customize:**
- `name`: The name shown in the chat header
- `description`: A short description of your agent
- `logo`: The avatar image for your agent

---

### 5. `.env.template` and `src/.env` - The Settings

**What it is:** Configuration files that store your Azure connection details.

**Key settings:**
```
AZURE_EXISTING_AIPROJECT_ENDPOINT=https://...  # Your Foundry project
AZURE_AI_CHAT_DEPLOYMENT_NAME=gpt-4o-mini      # Which model to use
AZURE_AI_AGENT_NAME=my-support-agent           # Your agent's name
```

---

## How a Message Goes From User to Agent and Back

### Step 1: User Types a Message

The user types "What are your business hours?" and clicks send.

### Step 2: Frontend Sends the Request

The React frontend:
1. Packages the message
2. Sends it to the `/chat` endpoint
3. Opens a streaming connection to receive the response

### Step 3: Backend Routes to Agent

The Python backend (`routes.py`):
1. Receives the request
2. Formats it for the Foundry Agent
3. Sends to the agent using `openai_client.responses.create()`

### Step 4: Foundry Agent Processes

The agent in Foundry:
1. Receives the message
2. Uses its configured instructions (from your `system.txt`)
3. Generates a response using its model (e.g., gpt-4o-mini)

### Step 5: Response Streams Back

Instead of waiting for the complete response:
1. Foundry sends back words as they're generated
2. The backend forwards each piece immediately
3. The frontend displays each piece as it arrives
4. The user sees the response "typing out" in real-time

---

## The Version History Magic

Here's what makes this accelerator special:

```
You edit system.txt
        ↓
"You are a friendly support agent..."
        ↓
Restart app / Redeploy
        ↓
create_version() is called
        ↓
┌─────────────────────────────────────────┐
│         FOUNDRY PORTAL                   │
│                                          │
│  my-agent                                │
│  ├── Version 3 (current) ← NEW!         │
│  ├── Version 2                           │
│  └── Version 1                           │
└─────────────────────────────────────────┘
        +
┌─────────────────────────────────────────┐
│         GIT HISTORY                      │
│                                          │
│  commit abc123 - "Updated agent prompt"  │
│  commit def456 - "Initial agent setup"   │
└─────────────────────────────────────────┘
```

You get version history in TWO places:
1. **Git** - Your code repository (system.txt changes)
2. **Foundry** - The agent versions in the portal

---

## Common Customization Scenarios

### "I want to change what my agent says"

Edit `src/api/prompts/system.txt` and restart. A new version is created!

### "I want to change the agent's name"

Edit `AZURE_AI_AGENT_NAME` in your `.env` file. This creates a NEW agent (not a new version of the old one).

### "I want to use a different AI model"

Change `AZURE_AI_CHAT_DEPLOYMENT_NAME` in your `.env` file and restart.

### "I want to see my agent in the Foundry portal"

1. Go to [Azure AI Foundry](https://ai.azure.com)
2. Open your project
3. Click "Agents" in the sidebar
4. Your agent appears with its version history!

### "I want to add new features"

Use GitHub Copilot! It can help you add features by reading the existing code patterns.

---

## Glossary

| Term | Definition |
|------|------------|
| **Agent** | A persistent AI entity in Foundry with its own identity and version history |
| **create_version()** | SDK method that creates or updates an agent in Foundry |
| **Endpoint** | A URL that accepts requests (like `/chat`) |
| **Foundry** | Azure AI Foundry - Microsoft's platform for building AI apps |
| **Instructions** | The system prompt that defines agent behavior |
| **SSE** | Server-Sent Events - streaming data from server to browser |
| **Version** | A snapshot of the agent's configuration at a point in time |

---

## Still Confused?

That's okay! Here are your options:

1. **Start simple** - Just edit `system.txt` and restart
2. **Check the portal** - See your agent and its versions in Azure AI Foundry
3. **Ask GitHub Copilot** - It can explain any part of the code
4. **Read the logs** - The app prints helpful messages on startup

Remember: The most important file is `system.txt`. Start there!

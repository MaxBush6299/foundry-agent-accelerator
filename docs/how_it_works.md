# How It Works: A Non-Technical Guide

This guide explains how the Foundry Agent Accelerator works in plain language. No programming experience required!

---

## What Is This Project?

This project is a **chat application** that lets you talk to an AI assistant. Think of it like a custom ChatGPT that you control and can customize for your specific needs.

The AI assistant (called an "agent") lives in **Azure AI Foundry**, which is Microsoft's platform for building AI applications. This project gives you:

- A **chat interface** (the webpage where you type messages)
- A **backend server** (the behind-the-scenes code that talks to Azure)
- A **persistent AI agent** (your customized assistant stored in Azure)

---

## The Big Picture

Here's what happens when you use this application:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│   Your Browser  │ ───► │  Backend Server │ ───► │  Azure AI       │
│   (Chat UI)     │ ◄─── │  (Python)       │ ◄─── │  Foundry        │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
     You type              Routes your            Where the AI
     messages              messages               actually lives
```

1. **You** type a message in your web browser
2. **The backend** receives your message and sends it to Azure
3. **Azure AI Foundry** processes your message using your AI agent
4. **The response** flows back through the same path to your screen

---

## Key Concepts Explained

### What is an "Agent"?

An **agent** is a customized AI assistant. It's like giving ChatGPT a specific personality and job description. Your agent has:

- **A name** - How it's identified (e.g., "customer-support-agent")
- **Instructions** - Rules that tell it how to behave (stored in `prompts/system.txt`)
- **A model** - The underlying AI brain (like GPT-4o)
- **Tools** - Special capabilities like running code or searching the web

### What is Azure AI Foundry?

**Azure AI Foundry** is Microsoft's cloud platform for AI. Think of it as a home for your AI agents. Benefits include:

- Your agent is stored safely in the cloud
- You can see and manage it through a web portal
- It keeps track of different versions as you make changes
- It handles all the complex AI stuff behind the scenes

### What is a "System Prompt"?

The **system prompt** is like a job description for your AI agent. It tells the agent:

- What its role is ("You are a helpful customer service agent")
- How it should behave ("Be friendly and professional")
- What it should and shouldn't do ("Don't discuss competitors")

You can find and edit this in the `src/api/prompts/system.txt` file.

### What are "Tools"?

**Tools** give your agent special capabilities beyond just chatting. Think of them as superpowers:

| Tool | What It Does | Example Use Case |
|------|--------------|------------------|
| **Code Interpreter** | Run Python code | Calculate complex math, analyze data |
| **Bing Search** | Search the web | Answer questions about current events |
| **File Search** | Search uploaded documents | Find information in your PDFs |
| **Azure AI Search** | Query your databases | Look up product information |

You can enable/disable tools in the `src/agent.yaml` file (in local mode) or through the portal (in portal mode).

### What is "Streaming"?

When you chat with the AI, you'll notice the response appears word-by-word rather than all at once. This is called **streaming**. It makes the conversation feel more natural and responsive, like watching someone type.

---

## What Happens When You Send a Message

Let's walk through exactly what happens when you type "Hello!" and press send:

### Step 1: Your Message Leaves the Browser

When you click send, your browser packages up your message and sends it to the backend server. If you attached any images or files, those get converted to a special format (base64) and included too.

### Step 2: The Backend Receives Your Message

The backend server (running Python) receives your message at the `/chat` endpoint. It:

1. Reads your message and any attachments
2. Adds it to the conversation history
3. Formats everything in a way Azure understands

### Step 3: Azure AI Foundry Processes the Request

The backend sends your message to Azure AI Foundry, which:

1. Finds your agent (by name)
2. Loads the agent's instructions (system prompt)
3. Sends everything to the AI model (e.g., GPT-4o)
4. The model generates a response

### Step 4: The Response Streams Back

Instead of waiting for the complete response, Azure sends it back piece by piece:

1. Each word (or few words) arrives as a small packet
2. The backend immediately forwards each packet to your browser
3. Your browser displays each piece as it arrives
4. You see the response "typing out" in real-time

### Step 5: Conversation Complete

Once the full response has arrived, the conversation is updated and you can send another message. The cycle repeats!

---

## Understanding the Files

Here's what the main files and folders do:

### `/src/api/` - The Backend (Python)

| File | What It Does |
|------|--------------|
| `main.py` | Starts the application and creates/updates your AI agent |
| `routes.py` | Handles incoming messages and sends responses back |
| `prompts/system.txt` | Contains your agent's personality and instructions |
| `util.py` | Helper functions used by other files |

### `/src/` - Configuration Files

| File | What It Does |
|------|--------------|
| `agent.yaml` | Enables/disables tools like Code Interpreter, Bing Search |
| `.env` | Your Azure credentials and settings |

### `/src/frontend/` - The Chat Interface (React)

| Folder/File | What It Does |
|-------------|--------------|
| `src/components/` | The visual elements you see on screen |
| `src/components/agents/` | The chat messages, input box, etc. |

### `/docs/` - Documentation

| File | What It Does |
|------|--------------|
| `README.md` | Project overview and getting started guide |
| `environment_variables.md` | Explains configuration settings |
| `code_walkthrough.md` | Technical details for developers |
| `how_it_works.md` | This file! Non-technical explanation |

---

## How Versioning Works

One powerful feature of this project is **smart version history**. The application automatically detects when your agent configuration has changed:

### Smart Change Detection

When the application starts (in `local` mode), it:

1. Computes a "fingerprint" (hash) of your current configuration
   - Agent name
   - Model name  
   - System prompt instructions
   - Enabled tools
2. Compares it to the fingerprint from the last deployment
3. **If unchanged** → Uses the existing agent (no new version)
4. **If changed** → Creates a new version in Azure

This means:
- ✅ Restarting the app doesn't spam new versions
- ✅ Changing `system.txt` automatically triggers a new version
- ✅ Changing the model or agent name triggers a new version
- ✅ Enabling/disabling tools triggers a new version
- ✅ Old versions are kept (you can see them in the Azure portal)
- ✅ Your code changes are tracked in Git

```
Version 1: "You are a helpful assistant."
    ↓ (system.txt changed)
Version 2: "You are a friendly customer service agent..."
    ↓ (restart - no change, same version kept)
Version 2: (still current)
    ↓ (enabled Code Interpreter tool)
Version 3: Same prompt, now with code execution!
```

---

## Two Ways to Configure Your Agent

This accelerator supports two configuration modes, controlled by the `AGENT_CONFIG_SOURCE` environment variable:

### Local Mode (Default) - For Developers

```
AGENT_CONFIG_SOURCE=local
```

In local mode, your agent is configured through files in your codebase:
- `src/api/prompts/system.txt` - Agent personality and instructions
- `src/agent.yaml` - Tools and capabilities

**Benefits:**
- ✅ Version control (changes tracked in Git)
- ✅ Easy testing and iteration
- ✅ Smart hash detection (no version spam)
- ✅ Infrastructure as code

### Portal Mode - For Business Users

```
AGENT_CONFIG_SOURCE=portal
```

In portal mode, your agent is configured entirely through the Azure AI Foundry web portal:
- Local config files (`system.txt`, `agent.yaml`) are ignored
- The app simply connects to the named agent

**Benefits:**
- ✅ No code editing required
- ✅ Point-and-click configuration
- ✅ Easier for non-technical users
- ✅ Changes take effect immediately in the portal

**When to use each:**
| Scenario | Recommended Mode |
|----------|-----------------|
| Development and testing | `local` |
| Business user customization | `portal` |
| Production with strict version control | `local` |
| Quick experimentation | `portal` |

---

## Customizing Your Agent

### Changing the Agent's Behavior

1. Open `src/api/prompts/system.txt`
2. Edit the instructions to match what you want
3. Restart the application
4. A new version is created automatically (only when changes are detected!)

### Changing the Agent's Appearance

1. Open `src/frontend/src/components/App.tsx`
2. Find the `agentDetails` section
3. Change the `name` and `description` values
4. Rebuild the frontend (`npm run build`)

### Adding File Attachment Support

The application supports attaching images and documents to your messages. The AI can "see" images and understand documents you share. Supported formats:

- **Images**: JPEG, PNG, GIF, WebP
- **Documents**: PDF, TXT, Markdown, JSON, CSV

---

## Common Questions

### Why do I need Azure?

Azure AI Foundry is where your AI agent lives. It provides:
- The AI model (the "brain")
- Secure storage for your agent
- Version history
- A portal to view and manage agents

### Can I use this offline?

No, the AI processing happens in Azure's cloud. You need an internet connection to use the chat.

### How much does it cost?

Costs depend on your Azure subscription and how much you use the AI. Check Azure's pricing for AI services.

### Is my data secure?

Your conversations are processed through Azure, which has enterprise-grade security. The data flows through your Azure subscription, so you control it.

### Can I share this with others?

Yes! Once deployed, anyone with access to your URL can use the chat. You can also add password protection using the `WEB_APP_USERNAME` and `WEB_APP_PASSWORD` settings.

---

## Glossary

| Term | Definition |
|------|------------|
| **Agent** | A customized AI assistant with specific instructions |
| **API** | Application Programming Interface - how different software talks to each other |
| **Azure** | Microsoft's cloud computing platform |
| **Backend** | The server-side code that runs behind the scenes |
| **Base64** | A way to encode files (like images) as text |
| **Endpoint** | A URL where the server listens for requests |
| **Frontend** | The user interface you see in your browser |
| **Model** | The AI "brain" (like GPT-4o) that generates responses |
| **SSE** | Server-Sent Events - technology for streaming responses |
| **Streaming** | Sending data piece by piece instead of all at once |
| **System Prompt** | Instructions that define your agent's behavior |
| **Version** | A snapshot of your agent at a point in time |

---

## Visual: Message Flow Diagram

```
YOU                    BROWSER                 BACKEND                 AZURE
 │                        │                       │                      │
 │  Type "Hello!"         │                       │                      │
 │───────────────────────►│                       │                      │
 │                        │  POST /chat           │                      │
 │                        │  {message: "Hello!"}  │                      │
 │                        │──────────────────────►│                      │
 │                        │                       │  Send to agent       │
 │                        │                       │─────────────────────►│
 │                        │                       │                      │
 │                        │                       │     AI processes     │
 │                        │                       │     your message     │
 │                        │                       │                      │
 │                        │                       │  "Hi" (streaming)    │
 │                        │  data: {"content":    │◄─────────────────────│
 │                        │         "Hi"}         │                      │
 │                        │◄──────────────────────│                      │
 │  See "Hi"              │                       │  " there!" (stream)  │
 │◄───────────────────────│                       │◄─────────────────────│
 │                        │  data: {"content":    │                      │
 │                        │         " there!"}    │                      │
 │                        │◄──────────────────────│                      │
 │  See "Hi there!"       │                       │                      │
 │◄───────────────────────│                       │  [stream end]        │
 │                        │                       │◄─────────────────────│
 │                        │  data: {"type":       │                      │
 │                        │         "stream_end"} │                      │
 │                        │◄──────────────────────│                      │
 │  Ready for next        │                       │                      │
 │  message               │                       │                      │
 │                        │                       │                      │
```

---

## Next Steps

Now that you understand how everything works:

1. **Try it out** - Send some messages and see the streaming in action
2. **Customize the prompt** - Edit `system.txt` to change your agent's personality
3. **Attach files** - Try sending an image and asking the AI to describe it
4. **Explore the portal** - Log into Azure AI Foundry to see your agent

Happy chatting! 🎉

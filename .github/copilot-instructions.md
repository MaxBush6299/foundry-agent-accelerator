# GitHub Copilot Instructions for Foundry Agent Accelerator

This document provides guidance for GitHub Copilot and developers working on the Foundry Agent Accelerator project.

## ⚠️ IMPORTANT: Agent Configuration Requests

**When a user asks about creating, configuring, or customizing an agent**, you MUST:
1. Read `.github/instructions/agent-configuration.instructions.md` FIRST
2. Follow the patterns and best practices defined there
3. Only edit `src/api/prompts/system.txt` and `src/agent.yaml`

Common user requests that require this file:
- "Create a [type] agent" (e.g., customer support, image analysis, research)
- "Change the agent's personality"
- "Enable/disable tools"
- "What tools are available?"
- "How do I customize the agent?"

---

## Project Overview

The Foundry Agent Accelerator is a starter project for building AI agents with **Azure AI Foundry**. It creates persistent agents that are visible and manageable in the Azure portal with version history.

### Tech Stack

- **Backend**: Python 3.10+ with FastAPI, Azure AI Projects SDK, OpenAI client
- **Frontend**: React 19 with TypeScript, Fluent UI Copilot components, Vite
- **Infrastructure**: Azure AI Foundry, Azure Container Apps (deployment)
- **Package Managers**: pip (Python), pnpm (frontend)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PROJECT STRUCTURE                         │
│                                                              │
│  src/                                                        │
│  ├── api/                 # Python FastAPI backend           │
│  │   ├── main.py         # App entry point, agent setup     │
│  │   ├── routes.py       # API endpoints (/chat, /)         │
│  │   ├── util.py         # Shared utilities (logger, models)│
│  │   └── prompts/        # System prompt files              │
│  │                                                          │
│  ├── frontend/           # React TypeScript frontend        │
│  │   └── src/components/ # UI components                    │
│  │                                                          │
│  └── agent.yaml          # Agent tools configuration        │
└─────────────────────────────────────────────────────────────┘
```

---

## Code Style Guidelines

### Python (Backend)

1. **Module Documentation**: Every Python file MUST start with a docstring block explaining:
   - What the file does
   - Key concepts for beginners
   - Important functions/classes

   ```python
   """
   =============================================================================
   MODULE NAME - Brief Description
   =============================================================================
   
   WHAT THIS FILE DOES:
   --------------------
   1. First responsibility
   2. Second responsibility
   
   KEY CONCEPTS:
   -------------
   Explain any non-obvious concepts for beginners.
   
   =============================================================================
   """
   ```

2. **Function Documentation**: Use descriptive docstrings with parameters and return types:

   ```python
   def get_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
       """
       Return a configured logger instance.
       
       :param name: The name of the logger
       :param log_level: The logging verbosity level
       :returns: The configured logger object
       """
   ```

3. **Type Hints**: Always use type hints for function parameters and return values:

   ```python
   def load_system_prompt() -> str:
   def get_openai_client(request: Request) -> Any:
   ```

4. **Pydantic Models**: Use Pydantic for request/response models:

   ```python
   class Message(pydantic.BaseModel):
       content: str
       role: str = "user"
       attachments: list[FileAttachment] = []
   ```

5. **Environment Variables**: Load from `.env` file using `python-dotenv`:

   ```python
   from dotenv import load_dotenv
   load_dotenv()
   model_name = os.getenv("AZURE_AI_CHAT_DEPLOYMENT_NAME")
   ```

6. **Section Comments**: Use visual separators for code sections:

   ```python
   # =============================================================================
   # IMPORTS
   # =============================================================================
   
   # =============================================================================
   # HELPER FUNCTIONS
   # =============================================================================
   ```

### TypeScript/React (Frontend)

1. **Component Documentation**: Every component file MUST start with a JSDoc block:

   ```tsx
   /**
    * =============================================================================
    * COMPONENT NAME - Brief Description
    * =============================================================================
    * 
    * WHAT THIS FILE DOES:
    * --------------------
    * 1. First responsibility
    * 2. Second responsibility
    * 
    * HOW TO CUSTOMIZE:
    * -----------------
    * Instructions for common customizations
    * 
    * =============================================================================
    */
   ```

2. **Component Definition**: Use `React.FC` with explicit prop interfaces:

   ```tsx
   interface IComponentProps {
     resourceId: string;
     agentDetails: IAgent;
   }
   
   export function ComponentName({ resourceId, agentDetails }: IComponentProps): ReactNode {
     // ...
   }
   ```

3. **CSS Modules**: Use CSS modules for component styling:
   - File naming: `ComponentName.module.css`
   - Import as: `import styles from "./ComponentName.module.css"`

4. **Fluent UI Components**: Use Fluent UI Copilot components:

   ```tsx
   import { Body1, Button, Title2 } from "@fluentui/react-components";
   import { ChatRegular } from "@fluentui/react-icons";
   ```

5. **TypeScript Interfaces**: Prefix interface names with `I`:

   ```tsx
   interface IAgent { }
   interface IChatItem { }
   interface IMessage { }
   ```

---

## Key Patterns

### Configuration Modes

The app supports two modes controlled by `AGENT_CONFIG_SOURCE`:

1. **LOCAL mode** (default): Agent configured via `prompts/system.txt` and `agent.yaml`
2. **PORTAL mode**: Agent configured entirely in Azure AI Foundry portal

### Streaming Responses (SSE)

Chat responses use Server-Sent Events for real-time streaming:

```python
# Backend: Use StreamingResponse with async generator
async def generate_response():
    async for chunk in agent_response:
        yield f"data: {json.dumps({'type': 'message', 'content': chunk})}\n\n"

return StreamingResponse(generate_response(), media_type="text/event-stream")
```

```tsx
// Frontend: Process SSE stream
const reader = response.body?.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  // Process chunk...
}
```

### Agent Version Management

When in LOCAL mode, agent versions are created based on config hash:

```python
# Hash of system prompt + agent.yaml determines if new version needed
config_hash = hashlib.md5(json.dumps(config).encode()).hexdigest()
# Only create_version if hash changed from last deployment
```

---

## File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python modules | snake_case | `main.py`, `util.py` |
| React components | PascalCase | `AgentPreview.tsx` |
| CSS modules | PascalCase.module.css | `AgentPreview.module.css` |
| TypeScript types | PascalCase | `chat.ts` |
| Config files | lowercase | `agent.yaml`, `vite.config.ts` |

---

## Common Tasks

### Adding a New API Endpoint

1. Add the route function in `src/api/routes.py`
2. Use the existing patterns for authentication and logging
3. Follow the docstring format for documentation

### Adding a New React Component

1. Create `ComponentName.tsx` in appropriate `components/` subdirectory
2. Create `ComponentName.module.css` for styles
3. Export from component and import where needed
4. Use Fluent UI components for UI elements

### Modifying Agent Behavior

1. Edit `src/api/prompts/system.txt` for personality/instructions
2. Edit `src/agent.yaml` to enable/disable tools
3. Restart the app - a new agent version is created automatically

---

## Azure AI Foundry Patterns

### Using the Project Client

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

client = AIProjectClient.from_connection_string(
    conn_str=os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT"),
    credential=DefaultAzureCredential()
)
```

### Creating Agent Tools

```python
from azure.ai.projects.models import (
    CodeInterpreterTool,
    BingGroundingAgentTool,
    AzureAISearchAgentTool,
)

tools = []
if config["tools"]["code_interpreter"]["enabled"]:
    tools.append(CodeInterpreterTool())
```

---

## Testing Guidelines

- Backend: Use pytest for Python tests
- Frontend: Use React Testing Library with Vitest
- Always test streaming functionality with mock SSE responses

---

## Security Considerations

1. **Never commit `.env` files** - Use `.env.template` as reference
2. **Use DefaultAzureCredential** - Supports multiple auth methods
3. **Optional Basic Auth** - Configured via `WEB_APP_USERNAME`/`WEB_APP_PASSWORD`
4. **Validate user input** - Use Pydantic models for request validation

---

## Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-foundry/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Fluent UI Copilot](https://aka.ms/fluent-copilot-react)
- [Azure AI Projects SDK](https://learn.microsoft.com/python/api/azure-ai-projects/)

---
name: foundry-agent-development
description: Specialized skill for developing Azure AI Foundry agents. Use when creating, configuring, or troubleshooting Foundry agents, modifying system prompts, enabling agent tools, or working with the Azure AI Projects SDK.
---

# Foundry Agent Development Skill

This skill provides guidance for developing AI agents using Azure AI Foundry within the Foundry Agent Accelerator project.

## Project Context

This is a FastAPI + React application that creates persistent AI agents in Azure AI Foundry. Agents are:
- Visible in the Azure AI Foundry portal
- Version-controlled (new versions created on config changes)
- Configurable via local files OR the portal

## Key Files

- [System Prompt](../../../src/api/prompts/system.txt) - Agent personality and instructions
- [Agent Configuration](../../../src/agent.yaml) - Tools and capabilities
- [Main Application](../../../src/api/main.py) - Agent initialization
- [API Routes](../../../src/api/routes.py) - Chat endpoint

## Configuration Modes

### LOCAL Mode (default)
Agent configured via local files:
```bash
AGENT_CONFIG_SOURCE=local
```
- Edit `src/api/prompts/system.txt` for personality
- Edit `src/agent.yaml` for tools
- Restart creates new version if config changed

### PORTAL Mode
Agent configured in Azure portal:
```bash
AGENT_CONFIG_SOURCE=portal
```
- Local files ignored
- Manage agent entirely in Foundry portal

## Available Agent Tools

| Tool | Purpose | Setup |
|------|---------|-------|
| `code_interpreter` | Run Python code | None |
| `bing_search` | Web search | Bing connection required |
| `file_search` | RAG over documents | Vector store required |
| `azure_ai_search` | Query search indexes | Search connection required |
| `image_generation` | Create images | Image model deployment |
| `web_search_preview` | Web with citations | None (preview) |

## Tool Configuration Pattern

```yaml
# src/agent.yaml
tools:
  code_interpreter:
    enabled: true
  
  bing_search:
    enabled: true
    connection_name: "my-bing-connection"  # Must match Foundry
```

## System Prompt Best Practices

1. **Define identity clearly**: "You are [name], a [role] for [purpose]"
2. **Specify personality traits**: Friendly, professional, technical, etc.
3. **List capabilities**: What the agent CAN do
4. **Set boundaries**: What the agent should NOT do
5. **Include response format guidelines**

## Azure AI SDK Patterns

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    CodeInterpreterTool,
    BingGroundingAgentTool,
)
from azure.identity import DefaultAzureCredential

# Initialize client
credential = DefaultAzureCredential()
project_client = AIProjectClient.from_connection_string(
    conn_str=os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT"),
    credential=credential
)

# Create/update agent with versioning
agent = project_client.agents.create_version(
    definition=PromptAgentDefinition(
        name=agent_name,
        model=model_name,
        instructions=system_prompt,
        tools=tools_list
    )
)
```

## Streaming Response Pattern

The chat endpoint uses Server-Sent Events (SSE):

```python
async def generate_response():
    async for chunk in agent_response:
        yield f"data: {json.dumps({'type': 'message', 'content': chunk})}\n\n"
    yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"

return StreamingResponse(generate_response(), media_type="text/event-stream")
```

## Version Management

Changes to config create new agent versions:

```python
# Hash detection prevents version spam
config_hash = hashlib.md5(json.dumps({
    "instructions": system_prompt,
    "tools": tools_config,
    "model": model_name
}).encode()).hexdigest()

# Only create_version if hash changed
if config_hash != previous_deployment_hash:
    agent = project_client.agents.create_version(...)
```

## Troubleshooting

- **Agent not creating**: Check `AZURE_AI_AGENT_NAME` and endpoint
- **Tools not working**: Verify connection names in Foundry portal
- **Version spam**: Check for hidden whitespace changes in config files
- **Auth errors**: Run `az login` and verify subscription access

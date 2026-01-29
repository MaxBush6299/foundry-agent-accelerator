---
description: Enable a new tool capability for the Foundry AI Agent (code interpreter, search, etc.)
name: add-agent-tool
agent: agent
tools:
  - changes
  - codebase
---

# Add New Agent Tool

Enable a new tool capability for the Foundry AI Agent.

## Available Built-in Tools

| Tool | Description | Setup Required |
|------|-------------|----------------|
| `code_interpreter` | Run Python code | None |
| `bing_search` | Web search via Bing | Bing Search connection |
| `file_search` | Search uploaded documents | Vector store |
| `azure_ai_search` | Query Azure Search | Search connection |
| `image_generation` | Create images | Image model deployment |
| `web_search_preview` | Web search with citations | None (preview) |

## Steps to Enable a Tool

### 1. Update `src/agent.yaml`

```yaml
tools:
  # Add or enable the tool
  tool_name:
    enabled: true
    # Add any required parameters
    connection_name: "your-connection"  # If needed
```

### 2. Update `src/api/main.py` Tool Loading

If adding a new tool type, update the `build_tools_from_config()` function:

```python
def build_tools_from_config(config: dict, project_client: AIProjectClient) -> list:
    """Build tool list from agent.yaml configuration."""
    tools = []
    
    tool_config = config.get("tools", {})
    
    # Add your new tool
    if tool_config.get("new_tool", {}).get("enabled"):
        from azure.ai.projects.models import NewToolType
        
        connection_name = tool_config["new_tool"].get("connection_name")
        if connection_name:
            # Get connection from Foundry
            connection = project_client.connections.get(connection_name)
            tools.append(NewToolType(
                connection_id=connection.id,
                # other parameters...
            ))
        else:
            tools.append(NewToolType())
    
    return tools
```

### 3. Add Required Imports

```python
from azure.ai.projects.models import (
    CodeInterpreterTool,
    BingGroundingAgentTool,
    AzureAISearchAgentTool,
    ImageGenTool,
    WebSearchPreviewTool,
    # Add new tool import
    NewToolType,
)
```

## Tool-Specific Setup

### Code Interpreter

```yaml
# agent.yaml
code_interpreter:
  enabled: true
```

No Azure setup required.

### Bing Search

1. Create Bing Search resource in Azure
2. Add connection in Foundry project:
   - Go to Project > Connections
   - Add Bing Search connection
3. Configure in agent.yaml:

```yaml
bing_search:
  enabled: true
  connection_name: "my-bing-connection"
```

### File Search (RAG)

1. Upload documents in Foundry portal
2. Create a vector store
3. Copy vector store ID
4. Configure:

```yaml
file_search:
  enabled: true
  vector_store_ids:
    - "vs_abc123"
```

### Azure AI Search

1. Create Azure AI Search resource
2. Create and populate an index
3. Add connection in Foundry
4. Configure:

```yaml
azure_ai_search:
  enabled: true
  connection_name: "search-connection"
  index_name: "my-index"
```

## Testing the Tool

1. Restart the application
2. Check startup logs for tool initialization
3. Ask the agent to use the tool:
   - Code Interpreter: "Calculate the fibonacci sequence"
   - Bing Search: "What happened in the news today?"
   - File Search: "What does the documentation say about..."

## Checklist

- [ ] Tool enabled in `agent.yaml`
- [ ] Azure resources created (if required)
- [ ] Connection added in Foundry portal (if required)
- [ ] Connection name matches in config
- [ ] Tool loading code added to `main.py` (if new type)
- [ ] Application restarted to pick up changes
- [ ] Tool tested with appropriate prompt

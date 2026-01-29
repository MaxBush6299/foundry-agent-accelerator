---
description: |
  ALWAYS read this file when users ask about: creating an agent, configuring an agent, 
  changing agent behavior, updating the system prompt, enabling tools, agent setup, 
  agent personality, agent instructions, what tools are available, how to customize the agent,
  image analysis agent, customer support agent, research agent, or any agent-related questions.
  This is the PRIMARY guide for non-technical users to configure their AI agent.
applyTo: "**"
---

# 🤖 Agent Configuration Guide

> **For Non-Technical Users**: This guide helps you customize your AI agent's personality, 
> capabilities, and behavior. No coding required!

## Quick Start

| What you want to do | File to edit |
|---------------------|-------------|
| Change what the agent says/does | `src/api/prompts/system.txt` |
| Enable/disable agent tools | `src/agent.yaml` |

---

## Overview

The Foundry Agent Accelerator uses Azure AI Foundry's Agent API to create persistent, versioned AI agents. This file covers configuration and best practices.

## Configuration Files

### 1. System Prompt (`src/api/prompts/system.txt`)

The system prompt defines your agent's personality, behavior, and capabilities:

```text
You are a helpful customer support agent for [Company Name].

PERSONALITY:
- Be friendly and professional
- Use clear, concise language
- Acknowledge uncertainty when you don't know something

CAPABILITIES:
- Answer questions about [product/service]
- Help troubleshoot common issues
- Escalate complex issues to human support

RESTRICTIONS:
- Never provide medical, legal, or financial advice
- Do not share internal company information
- Always respect user privacy
```

### 2. Agent Tools (`src/agent.yaml`)

Configure which tools your agent can use:

```yaml
# =============================================================================
# AGENT CONFIGURATION
# =============================================================================
#
# This file configures your AI agent when AGENT_CONFIG_SOURCE=local
# Changes here create a new agent version on restart.
#
# =============================================================================

tools:
  # Code Interpreter - Agent can write and run Python code
  code_interpreter:
    enabled: true
  
  # Bing Search - Agent can search the web
  # Requires: Bing Search connection in Foundry project
  bing_search:
    enabled: false
    connection_name: "my-bing-connection"
  
  # File Search - Agent can search uploaded documents
  # Requires: Vector store in Foundry project
  file_search:
    enabled: false
    vector_store_ids:
      - "vs_abc123"
  
  # Azure AI Search - Query Azure Search indexes
  # Requires: Azure AI Search connection
  azure_ai_search:
    enabled: false
    connection_name: "my-search-connection"
    index_name: "my-index"
  
  # Image Generation - Create images with DALL-E
  # Requires: Image generation model deployment
  image_generation:
    enabled: false
    deployment_name: "dall-e-3"
  
  # Web Search Preview - Real-time web search with citations
  web_search_preview:
    enabled: false
```

## Configuration Modes

### LOCAL Mode (Default)

```bash
AGENT_CONFIG_SOURCE=local
```

- Agent is configured via `prompts/system.txt` and `agent.yaml`
- Changes create new agent versions automatically
- Hash detection prevents version spam on restarts
- Good for development and Git-tracked configuration

### PORTAL Mode

```bash
AGENT_CONFIG_SOURCE=portal
```

- Agent is configured entirely in Azure AI Foundry portal
- Local config files are ignored
- Changes in portal are live immediately
- Good for production when business users manage the agent

## Version Management

When in LOCAL mode, the accelerator uses hash-based version detection:

```python
# The hash is computed from:
# 1. System prompt content
# 2. agent.yaml configuration
# 3. Enabled tools and their settings

config_hash = hashlib.md5(json.dumps({
    "instructions": system_prompt,
    "tools": tools_config,
    "model": model_name
}).encode()).hexdigest()

# New version only created if hash changed
if config_hash != previous_hash:
    agent = project_client.agents.create_version(...)
```

## Tool Configuration Patterns

### Code Interpreter

```yaml
code_interpreter:
  enabled: true
```

No additional configuration needed. The agent can:
- Write and execute Python code
- Create charts and visualizations
- Perform data analysis
- Process uploaded files

### Bing Search (Grounding)

```yaml
bing_search:
  enabled: true
  connection_name: "bing-search"  # Must match Foundry connection name
```

Setup in Azure:
1. Create a Bing Search resource
2. Add Bing Search connection in Foundry project
3. Use the connection name in config

### File Search (RAG)

```yaml
file_search:
  enabled: true
  vector_store_ids:
    - "vs_abc123"  # Get from Foundry portal after uploading files
```

Setup:
1. Upload documents in Foundry portal
2. Create a vector store
3. Copy the vector store ID to config

### Azure AI Search

```yaml
azure_ai_search:
  enabled: true
  connection_name: "my-ai-search"
  index_name: "knowledge-base"
```

Setup:
1. Create Azure AI Search resource
2. Create and populate an index
3. Add connection in Foundry project
4. Configure in agent.yaml

## Foundry IQ (Knowledge Base)

For Foundry IQ agents with grounded responses:

```yaml
# The agent will automatically include citations
# Format: [doc_title](url) or inline citations

# To enable Foundry IQ features:
file_search:
  enabled: true
  vector_store_ids:
    - "vs_your_knowledge_base"
```

The frontend automatically formats citations from `[doc]` references.

## Environment Variables

Required environment variables for agent operation:

```bash
# Azure AI Foundry project connection
AZURE_EXISTING_AIPROJECT_ENDPOINT=https://your-project.azure.com/...

# Model deployment name
AZURE_AI_CHAT_DEPLOYMENT_NAME=gpt-4o-mini

# Agent name (visible in Foundry portal)
AZURE_AI_AGENT_NAME=my-assistant

# Configuration mode
AGENT_CONFIG_SOURCE=local  # or "portal"
```

## Best Practices

### System Prompt Best Practices

1. **Be specific about personality and tone**
2. **Define clear boundaries** - what the agent should NOT do
3. **Provide examples** of expected responses
4. **Include escalation paths** for complex issues
5. **Keep it concise** - lengthy prompts can reduce performance

### Tool Configuration Best Practices

1. **Only enable tools you need** - each tool adds latency
2. **Test tools individually** before combining
3. **Use specific indexes** for Azure AI Search rather than broad searches
4. **Monitor token usage** - tools increase prompt size

### Version Management Best Practices

1. **Use Git for version control** - commit system.txt and agent.yaml changes
2. **Test locally before deploying** - use LOCAL mode for development
3. **Document major changes** - update README when changing agent behavior
4. **Use meaningful agent names** - helps identify versions in portal

## Troubleshooting

### Agent Not Updating

```bash
# Force a new version by modifying the config
# Add a comment or whitespace change to system.txt
```

### Tool Not Working

1. Check the tool is enabled in `agent.yaml`
2. Verify connection names match Foundry portal
3. Check Azure resource permissions
4. Review logs for error messages

### Portal Mode Not Reflecting Changes

1. Ensure `AGENT_CONFIG_SOURCE=portal`
2. Check agent name matches `AZURE_AI_AGENT_NAME`
3. Restart the application
4. Verify agent exists in Foundry portal

## Example Configurations

### Customer Support Agent

```yaml
tools:
  code_interpreter:
    enabled: false
  
  file_search:
    enabled: true
    vector_store_ids:
      - "vs_support_docs"
  
  azure_ai_search:
    enabled: true
    connection_name: "faq-search"
    index_name: "customer-faq"
```

### Data Analysis Agent

```yaml
tools:
  code_interpreter:
    enabled: true
  
  bing_search:
    enabled: false
  
  file_search:
    enabled: true
    vector_store_ids:
      - "vs_data_files"
```

### Research Agent

```yaml
tools:
  code_interpreter:
    enabled: true
  
  bing_search:
    enabled: true
    connection_name: "bing-search"
  
  web_search_preview:
    enabled: true
```

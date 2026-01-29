---
description: Guidelines for modifying or creating Python backend code in the FastAPI API
globs:
  - "src/api/**/*.py"
  - "src/*.py"
---

# Python Backend Development Guidelines

## File Structure

All Python backend code lives in `src/api/`. Follow this structure:

```
src/api/
├── main.py          # App entry point, agent initialization
├── routes.py        # API endpoint definitions
├── util.py          # Shared utilities (logger, Pydantic models)
├── prompts/         # System prompt text files
│   └── system.txt   # Agent personality/instructions
└── templates/       # Jinja2 HTML templates
```

## Required Documentation Format

Every Python file MUST start with this documentation block:

```python
"""
=============================================================================
MODULE NAME - Brief Description
=============================================================================

This module handles [primary responsibility].

WHAT THIS FILE DOES:
--------------------
1. First key responsibility
2. Second key responsibility
3. Additional responsibilities...

KEY CONCEPTS FOR BEGINNERS:
---------------------------
- Concept 1: Explanation
- Concept 2: Explanation

ENVIRONMENT VARIABLES:
----------------------
- VAR_NAME: Description of what it configures

=============================================================================
"""
```

## Code Section Headers

Use visual separators to organize code sections:

```python
# =============================================================================
# IMPORTS - Libraries this file needs
# =============================================================================

import os
import logging

# =============================================================================
# CONFIGURATION
# =============================================================================

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# =============================================================================
# API ROUTES
# =============================================================================
```

## Type Hints

Always use type hints for function signatures:

```python
from typing import Optional, Dict, List, Any

def get_agent_config(name: str, version: Optional[int] = None) -> Dict[str, Any]:
    """Get the agent configuration."""
    pass
```

## Pydantic Models

Define request/response models using Pydantic:

```python
import pydantic

class FileAttachment(pydantic.BaseModel):
    """Represents a file attached to a message."""
    name: str
    type: str
    data: str  # Base64-encoded

class Message(pydantic.BaseModel):
    """Represents a chat message."""
    content: str
    role: str = "user"
    attachments: list[FileAttachment] = []

class ChatRequest(pydantic.BaseModel):
    """Request body for the /chat endpoint."""
    messages: list[Message]
```

## Environment Variables

Load environment variables using python-dotenv:

```python
from dotenv import load_dotenv
import os

load_dotenv()

# Always provide descriptions for required env vars
model_name = os.getenv("AZURE_AI_CHAT_DEPLOYMENT_NAME")  # The deployed model name
project_endpoint = os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT")  # Foundry project URL
```

## Logging

Use the centralized logger from util.py:

```python
from .util import get_logger
import logging
import os

logger = get_logger(
    name="foundry-agent-module-name",
    log_level=logging.INFO,
    log_file_name=os.getenv("APP_LOG_FILE"),
    log_to_console=True
)

# Usage
logger.info("Starting operation...")
logger.error(f"Failed to process: {error}")
```

## FastAPI Route Patterns

Follow these patterns for API routes:

```python
import fastapi
from fastapi import Request, Depends, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse

router = fastapi.APIRouter()

@router.get("/", response_class=HTMLResponse)
async def serve_homepage(request: Request):
    """
    Serve the main chat interface.
    
    This endpoint renders the HTML template that loads the React frontend.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/chat")
async def chat_endpoint(
    request: Request,
    chat_request: ChatRequest
) -> StreamingResponse:
    """
    Handle chat messages and stream AI responses.
    
    This endpoint:
    1. Receives chat messages from the frontend
    2. Sends them to the Foundry Agent
    3. Streams the response back using SSE
    """
    async def generate():
        # Streaming logic here
        yield f"data: {json.dumps({'type': 'message', 'content': chunk})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Azure AI Foundry Integration

When working with Azure AI Foundry:

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

# Create or update agent
agent = project_client.agents.create_version(
    definition=PromptAgentDefinition(
        name=agent_name,
        model=model_name,
        instructions=system_prompt,
        tools=tools_list
    )
)

# Get OpenAI client for chat
openai_client = project_client.get_openai_client()
```

## Error Handling

Handle errors gracefully with proper HTTP status codes:

```python
from fastapi import HTTPException, status

def validate_config(config: dict) -> None:
    if not config.get("model"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model configuration is required"
        )

try:
    result = await process_request(data)
except AzureError as e:
    logger.error(f"Azure error: {e}")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Azure service temporarily unavailable"
    )
```

## Authentication Pattern

Use the existing optional basic auth pattern:

```python
from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()
username = os.getenv("WEB_APP_USERNAME")
password = os.getenv("WEB_APP_PASSWORD")
basic_auth_enabled = username and password

def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    """Verify credentials if basic auth is enabled."""
    if not basic_auth_enabled:
        return
    
    if not (secrets.compare_digest(credentials.username, username) and
            secrets.compare_digest(credentials.password, password)):
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Use in routes
@router.get("/protected")
async def protected_route(auth: None = Depends(authenticate)):
    pass
```

## Common Imports

```python
# Standard library
import contextlib
import hashlib
import json
import logging
import os
from typing import Optional, Dict, List, Any, Union
from pathlib import Path

# Third-party
import yaml
import pydantic
from dotenv import load_dotenv

# FastAPI
import fastapi
from fastapi import Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# Azure
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import *
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError
```

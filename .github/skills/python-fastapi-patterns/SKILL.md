---
name: python-fastapi-patterns
description: Skill for Python FastAPI backend development in this project. Use when creating API endpoints, working with Pydantic models, handling streaming responses, or implementing Azure authentication patterns.
---

# Python FastAPI Development Skill

This skill provides patterns and guidance for developing the Python FastAPI backend in the Foundry Agent Accelerator.

## Project Structure

```
src/api/
├── main.py          # App entry point, agent initialization
├── routes.py        # API endpoint definitions
├── util.py          # Shared utilities (logger, Pydantic models)
├── prompts/         # System prompt text files
└── templates/       # Jinja2 HTML templates
```

## Required Documentation Format

Every Python file MUST start with this header:

```python
"""
=============================================================================
MODULE NAME - Brief Description
=============================================================================

WHAT THIS FILE DOES:
--------------------
1. First key responsibility
2. Second key responsibility

KEY CONCEPTS:
-------------
Explanation of important concepts for beginners.

=============================================================================
"""
```

## Code Section Headers

Use visual separators:

```python
# =============================================================================
# IMPORTS
# =============================================================================

import os
import logging

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
```

## Type Hints (Required)

Always use type hints:

```python
from typing import Optional, Dict, List, Any

def get_agent_config(name: str, version: Optional[int] = None) -> Dict[str, Any]:
    """Get the agent configuration."""
    pass
```

## Pydantic Models

Use Pydantic for request/response validation:

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

## Route Patterns

### Basic GET Endpoint

```python
@router.get("/", response_class=HTMLResponse)
async def serve_homepage(request: Request):
    """
    Serve the main chat interface.
    
    This endpoint renders the HTML template that loads the React frontend.
    """
    return templates.TemplateResponse("index.html", {"request": request})
```

### Streaming POST Endpoint

```python
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
        async for chunk in agent_response:
            yield f"data: {json.dumps({'type': 'message', 'content': chunk})}\n\n"
        yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Logging Pattern

Use the centralized logger:

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

## Authentication Pattern

```python
from fastapi import Depends, HTTPException
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
```

## Error Handling

```python
from fastapi import HTTPException, status

try:
    result = await process_request(data)
except ValidationError as e:
    logger.warning(f"Validation error: {e}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e)
    )
except AzureError as e:
    logger.error(f"Azure error: {e}")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Azure service temporarily unavailable"
    )
```

## Environment Variables

```python
from dotenv import load_dotenv
import os

load_dotenv()

# Required variables
project_endpoint = os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT")
model_name = os.getenv("AZURE_AI_CHAT_DEPLOYMENT_NAME")
agent_name = os.getenv("AZURE_AI_AGENT_NAME")

# Optional with defaults
config_source = os.getenv("AGENT_CONFIG_SOURCE", "local")
```

## Common Imports

```python
# Standard library
import json
import logging
import os
from typing import Optional, Dict, List, Any
from pathlib import Path

# Third-party
import yaml
import pydantic
from dotenv import load_dotenv

# FastAPI
import fastapi
from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# Azure
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
```

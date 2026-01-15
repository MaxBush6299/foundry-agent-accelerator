"""
=============================================================================
FOUNDRY AGENT ACCELERATOR - API Routes Module
=============================================================================

This file defines the API endpoints (URLs) that the application responds to.
It handles chat interactions using Azure AI Foundry's Agent API.

WHAT THIS FILE DOES:
--------------------
1. Defines the GET "/" endpoint - Serves the web chat interface
2. Defines the POST "/chat" endpoint - Sends messages to the Foundry Agent

KEY CONCEPTS FOR BEGINNERS:
---------------------------
- Endpoint: A URL that the app responds to (like "/" or "/chat")
- GET request: When the browser loads a page
- POST request: When the browser sends data (like a chat message)
- SSE (Server-Sent Events): A way to stream the AI's response word-by-word

HOW THE AGENT CHAT FLOW WORKS:
------------------------------
1. User types a message in the chat interface
2. Frontend sends a POST request to /chat with the message
3. This file sends the message to the Foundry Agent via OpenAI client
4. The agent processes the message and generates a response
5. Response is streamed back to the frontend word-by-word (SSE)
6. Frontend displays the response as it arrives

DIFFERENCE FROM DIRECT CHAT COMPLETION:
---------------------------------------
- Old way: Send messages directly to a model (like GPT-4o)
- New way: Send messages to an AGENT that uses the model
- Benefits: Agent persists in Foundry, has version history, visible in portal

=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

# Python standard library
import json      # For converting Python objects to JSON strings
import logging   # For logging messages to console
import os        # For reading environment variables and file paths
import secrets   # For secure string comparison (authentication)
from typing import Dict, Optional  # Type hints for better code readability

# FastAPI - Web framework components
import fastapi
from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# Local imports
from .util import get_logger, ChatRequest  # Logger and request model


# =============================================================================
# AUTHENTICATION SETUP (Optional)
# =============================================================================

security = HTTPBasic()

# Check if basic auth credentials are configured
username = os.getenv("WEB_APP_USERNAME")
password = os.getenv("WEB_APP_PASSWORD")
basic_auth_enabled = username and password


def authenticate(credentials: Optional[HTTPBasicCredentials] = Depends(security)) -> None:
    """
    Verify the user's credentials for basic HTTP authentication.
    """
    if not basic_auth_enabled or not username or not password:
        return
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    correct_username = secrets.compare_digest(credentials.username, username)
    correct_password = secrets.compare_digest(credentials.password, password)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


auth_dependency = Depends(authenticate) if basic_auth_enabled else None


# =============================================================================
# LOGGING SETUP
# =============================================================================

logger = get_logger(
    name="foundry-agent-routes",
    log_level=logging.INFO,
    log_file_name=os.getenv("APP_LOG_FILE"),
    log_to_console=True
)


# =============================================================================
# FASTAPI ROUTER SETUP
# =============================================================================

router = fastapi.APIRouter()
templates = Jinja2Templates(directory="api/templates")


# =============================================================================
# HELPER FUNCTIONS - App State Accessors
# =============================================================================

def get_openai_client(request: Request):
    """
    Get the OpenAI client from app state.
    
    The OpenAI client is created in main.py via project_client.get_openai_client()
    and is used to interact with the Foundry Agent.
    """
    return request.app.state.openai_client


def get_agent(request: Request):
    """
    Get the Foundry Agent from app state.
    
    The agent is created/updated in main.py during startup using
    project_client.agents.create_version().
    """
    return request.app.state.agent


# =============================================================================
# SSE (Server-Sent Events) HELPER
# =============================================================================

def serialize_sse_event(data: Dict) -> str:
    """
    Convert a Python dictionary to SSE (Server-Sent Events) format.
    
    SSE is a standard for streaming data from server to browser.
    Each message must be formatted as: "data: {json}\n\n"
    """
    return f"data: {json.dumps(data)}\n\n"


# =============================================================================
# ENDPOINT: GET "/" - Serve the Chat Interface
# =============================================================================

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, _ = auth_dependency):
    """
    Serve the main chat interface HTML page.
    
    URL: GET /
    """
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )


# =============================================================================
# ENDPOINT: POST "/chat" - Handle Chat Messages via Foundry Agent
# =============================================================================

@router.post("/chat")
async def chat_stream_handler(
    chat_request: ChatRequest,
    openai_client = Depends(get_openai_client),
    agent = Depends(get_agent),
    _ = auth_dependency
) -> fastapi.responses.StreamingResponse:
    """
    Handle incoming chat messages and stream AI responses from the Foundry Agent.
    
    This endpoint:
    1. Receives chat messages from the frontend
    2. Sends them to the Foundry Agent via the OpenAI responses API
    3. Streams the response back using SSE (Server-Sent Events)
    
    Args:
        chat_request: Contains the list of messages in the conversation
        openai_client: OpenAI client for agent interaction (injected)
        agent: The Foundry Agent instance (injected)
        
    Returns:
        StreamingResponse: SSE stream of the agent's response
    """
    
    # -------------------------------------------------------------------------
    # SET UP SSE RESPONSE HEADERS
    # -------------------------------------------------------------------------
    
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream"
    }
    
    # -------------------------------------------------------------------------
    # RESPONSE STREAM GENERATOR
    # -------------------------------------------------------------------------
    
    async def response_stream():
        """
        Generate streaming SSE response from the Foundry Agent.
        """
        
        # ---------------------------------------------------------------------
        # STEP 1: PREPARE MESSAGES FOR THE AGENT
        # ---------------------------------------------------------------------
        # Convert the incoming chat request into the format the agent expects.
        # For the responses API, we use the "input" format with message objects.
        # ---------------------------------------------------------------------
        
        logger.info(f"Processing chat request with {len(chat_request.messages)} message(s)")
        
        # Build the input messages for the agent
        # The responses API expects a specific format
        # Messages can include text and/or file attachments (images, documents)
        input_messages = []
        for message in chat_request.messages:
            # Build the content array for this message
            content_items = []
            
            # Add text content if present
            if message.content:
                content_items.append({
                    "type": "input_text",
                    "text": message.content
                })
            
            # Add file attachments (images, documents)
            for attachment in message.attachments:
                mime_type = attachment.type
                base64_data = attachment.data
                
                if mime_type.startswith("image/"):
                    # Image attachments use input_image type
                    content_items.append({
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{base64_data}",
                        "detail": "auto"
                    })
                    logger.info(f"Added image attachment: {attachment.name} ({mime_type})")
                else:
                    # For documents (PDF, text, etc.), include as text with file info
                    # Note: For more complex document handling, you might want to use
                    # file search or other tools in the agent
                    content_items.append({
                        "type": "input_file",
                        "file_data": f"data:{mime_type};base64,{base64_data}",
                        "filename": attachment.name
                    })
                    logger.info(f"Added file attachment: {attachment.name} ({mime_type})")
            
            input_messages.append({
                "type": "message",
                "role": message.role,
                "content": content_items
            })
        
        # ---------------------------------------------------------------------
        # STEP 2: SEND TO FOUNDRY AGENT AND STREAM RESPONSE
        # ---------------------------------------------------------------------
        # We use the OpenAI responses API with agent_reference to route
        # the request to our Foundry Agent. This allows the agent's
        # configuration (instructions, model, etc.) to be applied.
        # ---------------------------------------------------------------------
        
        try:
            accumulated_message = ""
            
            logger.info(f"Sending request to agent: {agent.name}")
            
            # Call the agent using the responses API with streaming
            # The extra_body specifies which agent to use
            response = openai_client.responses.create(
                input=input_messages,
                stream=True,
                extra_body={
                    "agent": {
                        "name": agent.name,
                        "type": "agent_reference"
                    }
                },
            )
            
            # Process the streaming response
            for event in response:
                # Check for text content in the response
                if hasattr(event, 'output_text') and event.output_text:
                    # For non-streaming chunks, get the full text
                    chunk_text = event.output_text
                    if chunk_text and chunk_text != accumulated_message:
                        # Calculate the new content (delta)
                        new_content = chunk_text[len(accumulated_message):]
                        if new_content:
                            accumulated_message = chunk_text
                            yield serialize_sse_event({
                                "content": new_content,
                                "type": "message",
                            })
                
                # Handle delta-style streaming (if available)
                elif hasattr(event, 'delta') and event.delta:
                    delta_text = event.delta
                    if delta_text:
                        accumulated_message += delta_text
                        yield serialize_sse_event({
                            "content": delta_text,
                            "type": "message",
                        })
            
            # Send the complete message at the end
            logger.info(f"Response complete: {len(accumulated_message)} characters")
            yield serialize_sse_event({
                "content": accumulated_message,
                "type": "completed_message",
            })
            
        except Exception as e:
            # -----------------------------------------------------------------
            # ERROR HANDLING
            # -----------------------------------------------------------------
            
            error_text = str(e)
            logger.error(f"Agent chat error: {error_text}")
            
            # Check for content filter errors
            if 'content_filter' in error_text.lower():
                response = "Content was filtered for safety reasons."
            else:
                response = f"An error occurred: {error_text}"
            
            yield serialize_sse_event({
                "content": response,
                "type": "completed_message",
            })
        
        # ---------------------------------------------------------------------
        # STEP 3: END THE STREAM
        # ---------------------------------------------------------------------
        
        yield serialize_sse_event({
            "type": "stream_end"
        })
    
    return StreamingResponse(response_stream(), headers=headers)


# =============================================================================
# ENDPOINT: GET "/agent-info" - Get Agent Information
# =============================================================================

@router.get("/agent-info")
async def get_agent_info(
    request: Request,
    agent = Depends(get_agent),
    _ = auth_dependency
):
    """
    Return information about the current Foundry Agent.
    
    Useful for debugging and showing agent details in the UI.
    """
    return {
        "name": agent.name,
        "id": agent.id,
        "version": agent.version,
        "description": getattr(agent, 'description', None),
    }

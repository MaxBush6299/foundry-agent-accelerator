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
import re        # For regex pattern matching
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


def get_image_generation_deployment(request: Request) -> str | None:
    """
    Get the image generation deployment name from app state.
    
    This is needed to pass the x-ms-oai-image-generation-deployment header
    when image generation tool is enabled.
    """
    return getattr(request.app.state, 'image_generation_deployment', None)


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


def clean_citation_markers(content: str) -> str:
    """
    Convert citation markers from Foundry IQ/knowledge base responses into 
    functional footnote-style references.
    
    Citation markers look like: 【4:6†source】, 【4:0†MMC_P7_Safety.md】, etc.
    These are converted to superscript references like [1], [2] with a 
    sources list at the bottom.
    
    Args:
        content: The raw response content with citation markers
        
    Returns:
        str: Content with citation markers converted to footnotes
    """
    # Pattern matches: 【digits:digits†text】
    # Examples: 【4:6†source】, 【4:0†MMC_P7_Safety_Program_Overview.md】
    citation_pattern = r'【(\d+):(\d+)†([^】]*)】'
    
    # Find all citations and track unique sources
    citations = re.findall(citation_pattern, content)
    
    if not citations:
        return content
    
    # Build a map of unique sources to reference numbers
    source_map = {}  # source_name -> reference_number
    source_list = []  # ordered list of unique sources
    
    for doc_id, chunk_id, source_name in citations:
        # Create a unique key for this source
        source_key = source_name.strip()
        if source_key and source_key not in source_map:
            ref_num = len(source_list) + 1
            source_map[source_key] = ref_num
            source_list.append(source_key)
    
    # Replace citations with superscript-style references
    def replace_citation(match):
        doc_id, chunk_id, source_name = match.groups()
        source_key = source_name.strip()
        if source_key and source_key in source_map:
            ref_num = source_map[source_key]
            return f'<sup>[{ref_num}]</sup>'
        return ''  # Remove if source is empty
    
    cleaned = re.sub(citation_pattern, replace_citation, content)
    
    # Clean up any double spaces left behind
    cleaned = re.sub(r'  +', ' ', cleaned)
    
    # Add sources section at the bottom if we have any
    if source_list:
        sources_section = "\n\n---\n\n**📚 Sources:**\n"
        for i, source in enumerate(source_list, 1):
            # Clean up the source name for display
            display_name = source.replace('_', ' ').replace('.md', '')
            sources_section += f"\n[{i}] *{display_name}*"
        cleaned += sources_section
    
    return cleaned


def format_code_interpreter_output(content: str) -> str:
    """
    Detect and wrap raw code interpreter output in markdown code fences.
    
    Code interpreter output typically starts with import statements and
    contains Python code that should be formatted nicely in the UI.
    
    Args:
        content: The raw response content from the agent
        
    Returns:
        str: Content with code interpreter blocks wrapped in ```python fences
    """
    lines = content.split('\n')
    result_lines = []
    code_block = []
    in_code_block = False
    
    def is_code_line(line: str) -> bool:
        """Check if a line looks like Python code."""
        stripped = line.strip()
        if not stripped:
            return in_code_block  # Empty lines continue code blocks
        
        # NEVER treat markdown syntax as code
        # Markdown headings (## Heading)
        if re.match(r'^#{1,6}\s+\S', stripped):
            return False
        # Markdown images ![alt](url)
        if re.match(r'^!\[.*?\]\(.*?\)$', stripped):
            return False
        # Base64 data URIs
        if 'data:image/' in stripped:
            return False
        # Markdown bold/italic at start of line
        if re.match(r'^\*{1,2}\w', stripped) or re.match(r'^_{1,2}\w', stripped):
            return False
        # Numbered lists with text (1. **Something**)
        if re.match(r'^\d+\.\s+\*{0,2}\w', stripped):
            return False
        
        # Definite code patterns - must be actual Python code
        code_patterns = [
            stripped.startswith(('import ', 'from ')),
            # Python comments start with # followed by space, but exclude markdown headings
            stripped.startswith('# ') and not re.match(r'^#\s+[A-Z][a-z]+', stripped),
            stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'with ', 'try:', 'except')),
            '=' in stripped and not stripped.endswith(':') and not stripped.startswith(('**', '*', '-', '•')),
            stripped.startswith(('plt.', 'img.', 'df.', 'np.', 'pd.')),
            '/mnt/data/' in stripped,
            re.match(r'^[a-z_][a-z0-9_]*\.[a-z_]+\(', stripped),  # method calls like img.size()
            re.match(r'^[a-z_][a-z0-9_]*\(', stripped),  # function calls like print()
        ]
        return any(code_patterns)
    
    def is_prose_line(line: str) -> bool:
        """Check if a line looks like natural language prose."""
        stripped = line.strip()
        if not stripped:
            return False
        # Prose typically starts with capital letter and contains spaces/words
        if re.match(r'^[A-Z][a-z]+.*\s+\w+', stripped):
            # But exclude things that look like code
            if not any(c in stripped for c in ['(', ')', '=', '.', '/']):
                return True
            # Check if it's a sentence (ends with punctuation or contains common words)
            if re.search(r'(the |is |are |a |an |this |that |hazard|visible|image|worker)', stripped, re.IGNORECASE):
                return True
        # Bullet points are prose
        if stripped.startswith(('- ', '* ', '• ')):
            return True
        return False
    
    for line in lines:
        if is_prose_line(line) and in_code_block:
            # End the code block
            if code_block:
                result_lines.append('```python')
                result_lines.extend(code_block)
                result_lines.append('```')
                code_block = []
            in_code_block = False
            result_lines.append(line)
        elif is_code_line(line):
            in_code_block = True
            code_block.append(line)
        elif in_code_block and line.strip():
            # Continue code block with non-empty lines that might be code
            code_block.append(line)
        else:
            if in_code_block and code_block:
                # End code block on empty line if we have content
                result_lines.append('```python')
                result_lines.extend(code_block)
                result_lines.append('```')
                code_block = []
                in_code_block = False
            result_lines.append(line)
    
    # Handle any remaining code block
    if code_block:
        result_lines.append('```python')
        result_lines.extend(code_block)
        result_lines.append('```')
    
    return '\n'.join(result_lines)


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
    request: Request,
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
            
            # Check if image generation is enabled (requires special header)
            image_gen_deployment = get_image_generation_deployment(request)
            extra_headers = {}
            if image_gen_deployment:
                extra_headers["x-ms-oai-image-generation-deployment"] = image_gen_deployment
            
            # -----------------------------------------------------------------
            # MCP AUTO-APPROVAL LOOP
            # -----------------------------------------------------------------
            # Some agents use MCP tools that require approval. When an
            # mcp_approval_request is received, we automatically approve it
            # and continue the conversation. This loop handles multiple
            # rounds of approval if needed.
            # -----------------------------------------------------------------
            
            current_input = input_messages
            max_approval_rounds = 10  # Prevent infinite loops
            approval_round = 0
            
            while approval_round < max_approval_rounds:
                approval_round += 1
                pending_approvals = []
                response_id = None
                
                # Call the agent using the responses API with streaming
                # The extra_body specifies which agent to use
                response = openai_client.responses.create(
                    input=current_input,
                    stream=True,
                    extra_headers=extra_headers if extra_headers else None,
                    extra_body={
                        "agent": {
                            "name": agent.name,
                            "type": "agent_reference"
                        }
                    },
                )
                
                # Process the streaming response
                for event in response:
                    event_type = getattr(event, 'type', None)
                    
                    # Capture response ID for follow-up requests
                    if event_type == 'response.created':
                        if hasattr(event, 'response') and hasattr(event.response, 'id'):
                            response_id = event.response.id
                    
                    # Handle text output done event
                    elif event_type == 'response.output_text.done':
                        if hasattr(event, 'text') and event.text:
                            text_content = event.text
                            
                            # Check if this looks like MCP tool JSON data
                            # (internal agent data that shouldn't be shown raw)
                            stripped_text = text_content.strip()
                            if stripped_text.startswith('{') and stripped_text.endswith('}'):
                                try:
                                    # Try to parse as JSON - if successful, format it nicely
                                    parsed_json = json.loads(stripped_text)
                                    
                                    # Check if it's an MCP/tool request (has specific keys)
                                    if 'request' in parsed_json or 'knowledgeAgentIntents' in parsed_json:
                                        # Format as a visible tool call indicator with code block
                                        formatted_json = json.dumps(parsed_json, indent=2)
                                        text_content = f'\n\n> 🔍 **Querying knowledge base...**\n\n```json\n{formatted_json}\n```\n\n---\n\n'
                                        logger.info(f"Formatted MCP tool JSON for display")
                                except json.JSONDecodeError:
                                    # Not valid JSON, show as-is
                                    pass
                            
                            # Buffer content - don't stream to avoid duplication issues
                            accumulated_message += text_content
                            logger.info(f"Text output (buffered): {event.text[:100]}...")
                    
                    # Handle partial image event (streaming partial images)
                    elif event_type == 'response.image_generation_call.partial_image':
                        if hasattr(event, 'partial_image_b64') and event.partial_image_b64:
                            # Buffer partial image (will show final in completed_message)
                            logger.info("Partial image received (buffering)")
                    
                    # Handle output item done event (contains completed items including MCP approvals)
                    elif event_type == 'response.output_item.done':
                        if hasattr(event, 'item') and event.item:
                            item = event.item
                            item_type = getattr(item, 'type', None)
                            logger.info(f"Output item done - type: {item_type}")
                            
                            # Handle MCP approval requests - collect for auto-approval
                            if item_type == 'mcp_approval_request':
                                approval_id = getattr(item, 'id', None)
                                tool_name = getattr(item, 'name', 'unknown')
                                server_label = getattr(item, 'server_label', 'unknown')
                                arguments = getattr(item, 'arguments', '{}')
                                
                                if approval_id:
                                    pending_approvals.append({
                                        'id': approval_id,
                                        'name': tool_name,
                                        'server_label': server_label,
                                        'arguments': arguments
                                    })
                                    logger.info(f"MCP approval request collected: {tool_name} (server: {server_label})")
                                    
                                    # Buffer tool notification (will be included in final message)
                                    accumulated_message += f"\n\n🔧 *Using tool: {tool_name}...*\n\n"
                            
                            elif item_type == 'mcp_list_tools':
                                # MCP server is listing available tools - just log it
                                logger.info("MCP tools list received")
                            
                            elif item_type == 'image_generation_call':
                                # Get the result (base64 image data)
                                if hasattr(item, 'result') and item.result:
                                    image_base64 = item.result
                                    # Buffer image HTML (will be sent in completed_message)
                                    image_html = f'\n\n<img src="data:image/png;base64,{image_base64}" alt="Generated Image" style="max-width: 100%; border-radius: 8px; margin: 16px 0;" />\n\n'
                                    accumulated_message += image_html
                                    logger.info("Image generation completed (buffered)")
                    
                    # Handle response completed event (final response with all outputs)
                    elif event_type == 'response.completed':
                        if hasattr(event, 'response') and event.response:
                            resp = event.response
                            if hasattr(resp, 'output') and resp.output:
                                for output_item in resp.output:
                                    item_type = getattr(output_item, 'type', None)
                                    if item_type == 'image_generation_call' and hasattr(output_item, 'result') and output_item.result:
                                        # Only add if not already buffered
                                        if 'Generated Image' not in accumulated_message:
                                            image_base64 = output_item.result
                                            image_html = f'\n\n<img src="data:image/png;base64,{image_base64}" alt="Generated Image" style="max-width: 100%; border-radius: 8px; margin: 16px 0;" />\n\n'
                                            accumulated_message += image_html
                                            logger.info("Image from completed response (buffered)")
                                    # Note: We don't process 'message' type here anymore
                                    # because it was already buffered via response.output_text.done
                    
                    # Note: Legacy fallback handlers (output_text, delta) are disabled
                    # when using MCP agents to prevent duplicate output. The content
                    # is buffered and sent once via completed_message.
                
                # -----------------------------------------------------------------
                # CHECK FOR PENDING MCP APPROVALS
                # -----------------------------------------------------------------
                # If we collected any approval requests, send approvals and continue
                # -----------------------------------------------------------------
                
                if pending_approvals:
                    logger.info(f"Auto-approving {len(pending_approvals)} MCP tool request(s)")
                    
                    # Build approval responses
                    approval_responses = []
                    for approval in pending_approvals:
                        approval_responses.append({
                            "type": "mcp_approval_response",
                            "approval_request_id": approval['id'],
                            "approve": True,
                            "reason": "Auto-approved by Foundry Agent Accelerator"
                        })
                    
                    # Set up the next request with approval responses
                    current_input = approval_responses
                    logger.info(f"Sending approval responses, round {approval_round}")
                    
                    # Continue the loop to process the response after approval
                    continue
                else:
                    # No pending approvals, we're done
                    break
            
            if approval_round >= max_approval_rounds:
                logger.warning(f"Reached maximum approval rounds ({max_approval_rounds})")
            
            # Send the complete buffered message
            logger.info(f"Response complete: {len(accumulated_message)} characters")
            
            # Clean up citation markers and format code interpreter output
            cleaned_message = clean_citation_markers(accumulated_message)
            formatted_message = format_code_interpreter_output(cleaned_message)
            
            yield serialize_sse_event({
                "content": formatted_message,
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

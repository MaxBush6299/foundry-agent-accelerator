"""
=============================================================================
FOUNDRY AGENT ACCELERATOR - Main Application Module
=============================================================================

This is the main entry point for the Foundry Agent Accelerator application.
It sets up the FastAPI web server and connects to an AI Agent in Azure AI
Foundry.

WHAT THIS FILE DOES:
--------------------
1. Creates the web application (FastAPI)
2. Connects to Azure AI Foundry
3. Manages the AI Agent (local config OR portal-based)
4. Sets up authentication credentials for Azure

CONFIGURATION MODES:
--------------------
The app supports two configuration modes, controlled by AGENT_CONFIG_SOURCE:

LOCAL MODE (default):
  - Agent is configured via prompts/system.txt and agent.yaml
  - Tools are enabled via agent.yaml
  - Hash detection prevents version spam on restarts
  - Good for development and testing

PORTAL MODE:
  - Agent is configured entirely in Azure AI Foundry portal
  - Local config files (prompts/system.txt, agent.yaml) are ignored
  - Changes in portal are live immediately
  - Good for production when business users manage the agent

ENVIRONMENT VARIABLES REQUIRED:
-------------------------------
- AZURE_EXISTING_AIPROJECT_ENDPOINT: Your Azure AI Foundry project URL
- AZURE_AI_CHAT_DEPLOYMENT_NAME: The name of your deployed chat model
- AZURE_AI_AGENT_NAME: The name for your persistent agent in Foundry
- AGENT_CONFIG_SOURCE: "local" (default) or "portal"

=============================================================================
"""

# =============================================================================
# IMPORTS - Libraries this file needs to work
# =============================================================================

# Python standard library imports
import contextlib  # Helps manage resources that need cleanup
import hashlib     # For computing config hash to detect changes
import json        # For serializing config to hash
import logging     # For printing helpful messages to the console
import os          # For reading environment variables (configuration)
from typing import Union, Any  # For type hints
from pathlib import Path  # For handling file paths

# Third-party imports
import yaml  # For parsing agent.yaml configuration

# FastAPI - The web framework that handles HTTP requests
import fastapi
from fastapi.staticfiles import StaticFiles  # Serves static files (CSS, images, etc.)

# Azure AI SDK imports
from azure.ai.projects import AIProjectClient  # Connects to Azure AI Foundry
from azure.ai.projects.models import (
    PromptAgentDefinition,  # For defining agents
    CodeInterpreterTool,
    CodeInterpreterToolAuto,
    BingGroundingAgentTool,
    BingGroundingSearchToolParameters,
    BingGroundingSearchConfiguration,
    AzureAISearchAgentTool,
    AzureAISearchToolResource,
    AISearchIndexResource,
)

# Azure authentication - How we prove our identity to Azure
from azure.identity import DefaultAzureCredential, AzureCliCredential, ManagedIdentityCredential

# dotenv - Loads configuration from .env file during local development
from dotenv import load_dotenv

# Local imports - Other files in this project
from .util import get_logger  # Helper for logging messages

# =============================================================================
# GLOBAL VARIABLES
# =============================================================================

# Logger instance - will be initialized in create_app()
logger: logging.Logger


# =============================================================================
# SYSTEM PROMPT LOADING
# =============================================================================

def load_system_prompt() -> str:
    """
    Load the system prompt from the prompts/system.txt file.
    
    The system prompt defines your agent's personality and behavior.
    By keeping this in a separate file, you can customize the agent
    without modifying Python code.
    
    Returns:
        str: The contents of prompts/system.txt, or a default prompt
    """
    prompts_dir = Path(__file__).parent / "prompts"
    system_prompt_path = prompts_dir / "system.txt"
    
    try:
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract just the prompt part (before any instruction section)
        if '=====' in content:
            prompt = content.split('=====')[0].strip()
        else:
            prompt = content.strip()
            
        return prompt if prompt else "You are a helpful assistant."
            
    except FileNotFoundError:
        logger.warning(f"System prompt file not found at {system_prompt_path}")
        return "You are a helpful assistant."
    except Exception as e:
        logger.error(f"Error reading system prompt: {e}")
        return "You are a helpful assistant."


# =============================================================================
# CONFIG HASH MANAGEMENT
# =============================================================================
# We use a hash of the agent configuration to detect changes.
# This prevents creating a new version on every restart - we only
# create a new version when the config actually changes.
# =============================================================================

# Path to store the last deployed config hash
CONFIG_HASH_FILE = Path(__file__).parent / ".agent_config_hash"


def compute_config_hash(agent_name: str, model_name: str, instructions: str, tools_config: dict | None = None) -> str:
    """
    Compute a SHA-256 hash of the agent configuration.
    
    This hash is used to detect if the configuration has changed since
    the last deployment. If the hash matches, we skip creating a new version.
    
    Args:
        agent_name: The name of the agent
        model_name: The model deployment name
        instructions: The system prompt/instructions
        tools_config: The tools configuration from agent.yaml
        
    Returns:
        str: A hex-encoded SHA-256 hash of the configuration
    """
    config = {
        "agent_name": agent_name,
        "model_name": model_name,
        "instructions": instructions,
        "tools": tools_config or {},
    }
    config_json = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_json.encode()).hexdigest()


def get_stored_config_hash() -> str | None:
    """
    Retrieve the previously stored config hash.
    
    Returns:
        str | None: The stored hash, or None if no hash file exists
    """
    try:
        if CONFIG_HASH_FILE.exists():
            return CONFIG_HASH_FILE.read_text().strip()
    except Exception:
        pass
    return None


def store_config_hash(config_hash: str) -> None:
    """
    Store the config hash for future comparison.
    
    Args:
        config_hash: The hash to store
    """
    try:
        CONFIG_HASH_FILE.write_text(config_hash)
    except Exception as e:
        logger.warning(f"Could not store config hash: {e}")


# =============================================================================
# AGENT CONFIGURATION LOADING
# =============================================================================

# Path to the agent configuration file
AGENT_CONFIG_FILE = Path(__file__).parent.parent / "agent.yaml"


def load_agent_config() -> dict[str, Any]:
    """
    Load the agent configuration from agent.yaml.
    
    Returns:
        dict: The agent configuration, or empty dict if file doesn't exist
    """
    try:
        if AGENT_CONFIG_FILE.exists():
            with open(AGENT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config if config else {}
    except Exception as e:
        logger.warning(f"Could not load agent.yaml: {e}")
    return {}


def build_tools(agent_config: dict[str, Any], project_client: AIProjectClient) -> list:
    """
    Build the list of tools based on agent.yaml configuration.
    
    Args:
        agent_config: The loaded agent configuration
        project_client: The AIProjectClient for getting connections
        
    Returns:
        list: List of tool definitions to pass to create_version
    """
    tools = []
    tools_config = agent_config.get("tools", {})
    
    # Code Interpreter - use CodeInterpreterTool with container for PromptAgentDefinition
    code_interpreter = tools_config.get("code_interpreter", {})
    if code_interpreter.get("enabled", False):
        logger.info("  📦 Enabling Code Interpreter")
        tools.append(CodeInterpreterTool(container=CodeInterpreterToolAuto()))
    
    # Bing Search (Web Grounding)
    bing_search = tools_config.get("bing_search", {})
    if bing_search.get("enabled", False):
        connection_name = bing_search.get("connection_name")
        if connection_name:
            logger.info(f"  🔍 Enabling Bing Search (connection: {connection_name})")
            # Get connection ID from project
            try:
                connection = project_client.connections.get(name=connection_name)
                tools.append(BingGroundingAgentTool(
                    bing_grounding=BingGroundingSearchToolParameters(
                        search_configurations=[
                            BingGroundingSearchConfiguration(
                                project_connection_id=connection.id
                            )
                        ]
                    )
                ))
            except Exception as e:
                logger.warning(f"  ⚠️ Could not enable Bing Search: {e}")
        else:
            logger.warning("  ⚠️ Bing Search enabled but no connection_name specified")
    
    # File Search - use dictionary format
    file_search = tools_config.get("file_search", {})
    if file_search.get("enabled", False):
        vector_store_name = file_search.get("vector_store_name")
        if vector_store_name:
            logger.info(f"  📄 Enabling File Search (vector store: {vector_store_name})")
            tools.append({
                "type": "file_search",
                "vector_store_ids": [vector_store_name]
            })
        else:
            logger.warning("  ⚠️ File Search enabled but no vector_store_name specified")
    
    # Azure AI Search
    azure_ai_search = tools_config.get("azure_ai_search", {})
    if azure_ai_search.get("enabled", False):
        connection_name = azure_ai_search.get("connection_name")
        index_name = azure_ai_search.get("index_name")
        if connection_name and index_name:
            logger.info(f"  🔎 Enabling Azure AI Search (index: {index_name})")
            try:
                connection = project_client.connections.get(name=connection_name)
                tools.append(AzureAISearchAgentTool(
                    azure_ai_search=AzureAISearchToolResource(
                        indexes=[
                            AISearchIndexResource(
                                project_connection_id=connection.id,
                                index_name=index_name
                            )
                        ]
                    )
                ))
            except Exception as e:
                logger.warning(f"  ⚠️ Could not enable Azure AI Search: {e}")
        else:
            logger.warning("  ⚠️ Azure AI Search enabled but missing connection_name or index_name")
    
    return tools


def get_tools_config_for_hash(agent_config: dict[str, Any]) -> dict:
    """
    Extract just the tools configuration for hashing.
    
    We need a stable representation for the hash computation.
    
    Args:
        agent_config: The loaded agent configuration
        
    Returns:
        dict: Tools configuration suitable for hashing
    """
    return agent_config.get("tools", {})


# =============================================================================
# APPLICATION LIFESPAN
# =============================================================================

@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    """
    Application lifespan manager - runs on startup and shutdown.
    
    STARTUP (before yield):
    - Sets up Azure credentials
    - Connects to Azure AI Foundry
    - Creates or updates the persistent AI Agent
    
    SHUTDOWN (after yield):
    - Closes all connections cleanly
    """
    
    # -------------------------------------------------------------------------
    # STEP 1: SET UP AZURE CREDENTIALS
    # -------------------------------------------------------------------------
    
    logger.info("=" * 60)
    logger.info("STARTING FOUNDRY AGENT ACCELERATOR")
    logger.info("=" * 60)
    
    azure_credential: Union[AzureCliCredential, ManagedIdentityCredential]
    
    if not os.getenv("RUNNING_IN_PRODUCTION"):
        # LOCAL DEVELOPMENT MODE
        logger.info("Running in LOCAL DEVELOPMENT mode")
        
        if tenant_id := os.getenv("AZURE_TENANT_ID"):
            logger.info(f"Using AzureCliCredential with tenant_id: {tenant_id}")
            azure_credential = AzureCliCredential(tenant_id=tenant_id)
        else:
            logger.info("Using AzureCliCredential (default tenant)")
            azure_credential = AzureCliCredential()
    else:
        # PRODUCTION MODE (running in Azure)
        logger.info("Running in PRODUCTION mode (Azure)")
        user_identity_client_id = os.getenv("AZURE_CLIENT_ID")
        logger.info(f"Using ManagedIdentityCredential with client_id: {user_identity_client_id}")
        azure_credential = ManagedIdentityCredential(client_id=user_identity_client_id)
    
    # -------------------------------------------------------------------------
    # STEP 2: CONNECT TO AZURE AI FOUNDRY PROJECT
    # -------------------------------------------------------------------------
    
    endpoint = os.environ["AZURE_EXISTING_AIPROJECT_ENDPOINT"]
    logger.info(f"Connecting to Azure AI Foundry project: {endpoint}")
    
    # Create the project client - this is our main connection to Foundry
    project_client = AIProjectClient(
        credential=azure_credential,
        endpoint=endpoint,
    )
    
    # -------------------------------------------------------------------------
    # STEP 3: CONNECT TO OR CREATE AGENT (BASED ON CONFIG SOURCE)
    # -------------------------------------------------------------------------
    # Two modes are supported:
    # - LOCAL: Agent is configured via prompts/system.txt and agent.yaml
    # - PORTAL: Agent is configured entirely in Azure AI Foundry portal
    # -------------------------------------------------------------------------
    
    agent_name = os.environ.get("AZURE_AI_AGENT_NAME", "foundry-accelerator-agent")
    model_name = os.environ.get("AZURE_AI_CHAT_DEPLOYMENT_NAME", "")
    config_source = os.environ.get("AGENT_CONFIG_SOURCE", "local").lower()
    
    logger.info("-" * 60)
    
    if config_source == "portal":
        # ---------------------------------------------------------------------
        # PORTAL MODE: Agent is managed in Azure AI Foundry portal
        # ---------------------------------------------------------------------
        logger.info("CONFIG MODE: PORTAL")
        logger.info("-" * 60)
        logger.info("Agent configuration is managed in Azure AI Foundry portal.")
        logger.info("Local files (prompts/system.txt, agent.yaml) are IGNORED.")
        logger.info("Changes made in the portal take effect immediately.")
        logger.info("-" * 60)
        
        logger.info(f"Connecting to agent: {agent_name}")
        
        try:
            agent = project_client.agents.get(agent_name)
            agent_version = getattr(agent, 'version', 'latest')
            logger.info(f"✅ Connected to agent: {agent.name} (v{agent_version})")
        except Exception as e:
            logger.error(f"❌ Could not find agent '{agent_name}' in Foundry!")
            logger.error("   Create the agent in the Azure AI Foundry portal first,")
            logger.error("   or switch to local mode by setting AGENT_CONFIG_SOURCE=local")
            raise RuntimeError(f"Agent '{agent_name}' not found in Foundry: {e}")
    
    else:
        # ---------------------------------------------------------------------
        # LOCAL MODE: Agent is managed via local config files
        # ---------------------------------------------------------------------
        logger.info("CONFIG MODE: LOCAL")
        logger.info("-" * 60)
        logger.info("Agent configuration is managed via local files:")
        logger.info("  • prompts/system.txt - Agent instructions")
        logger.info("  • agent.yaml - Tool configuration")
        logger.info("Portal changes will be OVERWRITTEN on restart.")
        logger.info("-" * 60)
        
        if not model_name:
            raise RuntimeError("AZURE_AI_CHAT_DEPLOYMENT_NAME is required in local mode")
        
        # Load configuration from local files
        system_prompt = load_system_prompt()
        agent_config = load_agent_config()
        tools_config = get_tools_config_for_hash(agent_config)
        
        # Compute hash of current config (including tools)
        current_hash = compute_config_hash(agent_name, model_name, system_prompt, tools_config)
        stored_hash = get_stored_config_hash()
        
        logger.info("AGENT CONFIGURATION:")
        logger.info(f"  Agent Name: {agent_name}")
        logger.info(f"  Model: {model_name}")
        logger.info(f"  Instructions: {system_prompt[:80]}...")
        logger.info(f"  Config Hash: {current_hash[:16]}...")
        
        # Log enabled tools
        enabled_tools = [k for k, v in tools_config.items() if isinstance(v, dict) and v.get("enabled")]
        if enabled_tools:
            logger.info(f"  Tools: {', '.join(enabled_tools)}")
        else:
            logger.info("  Tools: None")
        
        logger.info("-" * 40)
        
        if current_hash == stored_hash:
            # Config unchanged - retrieve existing agent
            logger.info("✅ Config unchanged - using existing agent version")
            agent = project_client.agents.get(agent_name)
            agent_version = getattr(agent, 'version', 'latest')
            logger.info(f"   Retrieved: {agent.name} (v{agent_version})")
        else:
            # Config changed - create new version
            if stored_hash:
                logger.info("📝 Config changed - creating new agent version")
            else:
                logger.info("📝 First deployment - creating agent")
            
            # Build tools from agent.yaml
            logger.info("Building tools...")
            tools = build_tools(agent_config, project_client)
            
            # Create the agent with tools
            agent = project_client.agents.create_version(
                agent_name=agent_name,
                definition=PromptAgentDefinition(
                    model=model_name,
                    instructions=system_prompt,
                    tools=tools if tools else None,
                ),
                description="Agent created/updated by Foundry Agent Accelerator",
            )
            
            # Store the new hash
            store_config_hash(current_hash)
            
            logger.info(f"✅ New version created!")
            logger.info(f"   ID: {agent.id}")
            logger.info(f"   Name: {agent.name}")
            logger.info(f"   Version: {agent.version}")
    
    # -------------------------------------------------------------------------
    # STEP 4: GET THE OPENAI CLIENT FOR CHAT
    # -------------------------------------------------------------------------
    # The OpenAI client is used to interact with the agent via the
    # responses API, which supports streaming.
    # -------------------------------------------------------------------------
    
    openai_client = project_client.get_openai_client()
    
    # -------------------------------------------------------------------------
    # STEP 5: STORE CLIENTS IN APP STATE
    # -------------------------------------------------------------------------
    
    app.state.project_client = project_client
    app.state.openai_client = openai_client
    app.state.agent = agent
    app.state.agent_name = agent_name
    
    agent_version = getattr(agent, 'version', 'latest')
    logger.info("=" * 60)
    logger.info(f"AGENT READY - {agent.name} (v{agent_version})")
    logger.info("Agent is visible in Azure AI Foundry portal!")
    logger.info("=" * 60)
    
    # -------------------------------------------------------------------------
    # YIELD - Application runs here
    # -------------------------------------------------------------------------
    
    yield
    
    # -------------------------------------------------------------------------
    # SHUTDOWN: CLEAN UP RESOURCES
    # -------------------------------------------------------------------------
    
    logger.info("Shutting down Foundry Agent Accelerator...")
    
    # Note: We do NOT delete the agent on shutdown
    # The agent persists in Foundry and can be viewed in the portal
    
    project_client.close()
    
    logger.info("Shutdown complete. Agent remains in Foundry!")


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_app():
    """
    Create and configure the FastAPI application.
    
    Returns:
        fastapi.FastAPI: The configured application instance
    """
    
    # -------------------------------------------------------------------------
    # LOAD ENVIRONMENT VARIABLES
    # -------------------------------------------------------------------------
    
    if not os.getenv("RUNNING_IN_PRODUCTION"):
        load_dotenv(override=True)
    
    # -------------------------------------------------------------------------
    # SET UP LOGGING
    # -------------------------------------------------------------------------
    
    global logger
    logger = get_logger(
        name="foundry-agent",
        log_level=logging.INFO,
        log_file_name=os.getenv("APP_LOG_FILE"),
        log_to_console=True
    )
    
    logger.info("Initializing Foundry Agent Accelerator...")
    
    # -------------------------------------------------------------------------
    # CREATE THE FASTAPI APPLICATION
    # -------------------------------------------------------------------------
    
    app = fastapi.FastAPI(
        lifespan=lifespan,
        title="Foundry Agent Accelerator",
        description="A starting point for building AI agents with Azure AI Foundry",
        version="2.0.0"  # Updated version for agent-based architecture
    )
    
    # -------------------------------------------------------------------------
    # MOUNT STATIC FILES
    # -------------------------------------------------------------------------
    
    app.mount("/static", StaticFiles(directory="api/static"), name="static")
    
    # -------------------------------------------------------------------------
    # INCLUDE API ROUTES
    # -------------------------------------------------------------------------
    
    from . import routes
    app.include_router(routes.router)
    
    logger.info("Application created successfully")
    
    return app


# =============================================================================
# MODULE-LEVEL APP INSTANCE
# =============================================================================
# This creates the app when the module is imported, which is required
# for uvicorn to find it via "api.main:app"
# =============================================================================

app = create_app()

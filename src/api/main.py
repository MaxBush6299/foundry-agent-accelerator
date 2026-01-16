"""
=============================================================================
FOUNDRY AGENT ACCELERATOR - Main Application Module
=============================================================================

This is the main entry point for the Foundry Agent Accelerator application.
It sets up the FastAPI web server and creates/updates a persistent AI Agent
in Azure AI Foundry.

WHAT THIS FILE DOES:
--------------------
1. Creates the web application (FastAPI)
2. Connects to Azure AI Foundry
3. Creates or updates a persistent AI Agent (with version history)
4. Sets up authentication credentials for Azure

KEY CONCEPTS FOR BEGINNERS:
---------------------------
- FastAPI: A Python web framework that handles HTTP requests
- Azure AI Foundry: Microsoft's AI platform for building AI agents
- Persistent Agent: An AI agent stored in Foundry (visible in portal, has versions)
- Agent Version: Each time you update the agent, a new version is created

HOW AGENT VERSIONING WORKS:
---------------------------
1. You edit prompts/system.txt (your source of truth)
2. You deploy/restart the app
3. The app computes a hash of the config (model, instructions, tools)
4. If the hash matches the previous deployment → reuse existing agent
5. If the hash differs → create a new version in Foundry
6. Both Git and Foundry have version history!

This prevents creating a new version on every restart while still
automatically deploying changes when you modify the configuration.

ENVIRONMENT VARIABLES REQUIRED:
-------------------------------
- AZURE_EXISTING_AIPROJECT_ENDPOINT: Your Azure AI Foundry project URL
- AZURE_AI_CHAT_DEPLOYMENT_NAME: The name of your deployed chat model
- AZURE_AI_AGENT_NAME: The name for your persistent agent in Foundry

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
from typing import Union  # For type hints
from pathlib import Path  # For handling file paths

# FastAPI - The web framework that handles HTTP requests
import fastapi
from fastapi.staticfiles import StaticFiles  # Serves static files (CSS, images, etc.)

# Azure AI SDK imports
from azure.ai.projects import AIProjectClient  # Connects to Azure AI Foundry
from azure.ai.projects.models import PromptAgentDefinition  # For defining agents

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


def compute_config_hash(agent_name: str, model_name: str, instructions: str) -> str:
    """
    Compute a SHA-256 hash of the agent configuration.
    
    This hash is used to detect if the configuration has changed since
    the last deployment. If the hash matches, we skip creating a new version.
    
    Args:
        agent_name: The name of the agent
        model_name: The model deployment name
        instructions: The system prompt/instructions
        
    Returns:
        str: A hex-encoded SHA-256 hash of the configuration
    """
    config = {
        "agent_name": agent_name,
        "model_name": model_name,
        "instructions": instructions,
        # Future: add "tools" here when tool support is added
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
    # STEP 3: CREATE OR UPDATE THE PERSISTENT AGENT (WITH CHANGE DETECTION)
    # -------------------------------------------------------------------------
    # We use a hash of the config to detect changes. This prevents creating
    # a new version on every restart - we only create a new version when
    # the configuration (model, instructions, tools) actually changes.
    # -------------------------------------------------------------------------
    
    agent_name = os.environ.get("AZURE_AI_AGENT_NAME", "foundry-accelerator-agent")
    model_name = os.environ["AZURE_AI_CHAT_DEPLOYMENT_NAME"]
    
    # Load the system prompt from prompts/system.txt
    system_prompt = load_system_prompt()
    
    # Compute hash of current config
    current_hash = compute_config_hash(agent_name, model_name, system_prompt)
    stored_hash = get_stored_config_hash()
    
    logger.info("-" * 40)
    logger.info("CHECKING AGENT CONFIGURATION")
    logger.info(f"  Agent Name: {agent_name}")
    logger.info(f"  Model: {model_name}")
    logger.info(f"  Instructions: {system_prompt[:100]}...")
    logger.info(f"  Config Hash: {current_hash[:16]}...")
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
        
        agent = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=model_name,
                instructions=system_prompt,
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

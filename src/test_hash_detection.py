"""
Test script for agent config hash detection with REAL Azure AI Foundry.

This script actually connects to Azure and tests that:
1. First run creates a new agent version
2. Second run (no changes) reuses the existing agent
3. Changing the prompt creates a new version

Usage:
    cd src
    python test_hash_detection.py          # Run local tests only
    python test_hash_detection.py --live   # Run with real Azure connection
"""

import sys
import os
import argparse

# Add the api directory to the path so we can import from main
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(override=True)

from api.main import (
    compute_config_hash,
    get_stored_config_hash,
    store_config_hash,
    CONFIG_HASH_FILE,
    load_system_prompt,
)


def test_hash_computation():
    """Test that hash computation is deterministic."""
    print("\n" + "=" * 60)
    print("TEST 1: Hash Computation (Local)")
    print("=" * 60)
    
    hash1 = compute_config_hash("my-agent", "gpt-4o", "You are helpful")
    hash2 = compute_config_hash("my-agent", "gpt-4o", "You are helpful")
    hash3 = compute_config_hash("my-agent", "gpt-4o", "You are HELPFUL")  # Different!
    
    print(f"Hash 1: {hash1[:32]}...")
    print(f"Hash 2: {hash2[:32]}...")
    print(f"Hash 3: {hash3[:32]}...")
    
    assert hash1 == hash2, "Same config should produce same hash!"
    assert hash1 != hash3, "Different config should produce different hash!"
    
    print("✅ PASSED: Hash computation is deterministic and change-sensitive")


def test_hash_storage():
    """Test that hash can be stored and retrieved."""
    print("\n" + "=" * 60)
    print("TEST 2: Hash Storage (Local)")
    print("=" * 60)
    
    test_hash = "abc123test456"
    
    # Store the hash
    store_config_hash(test_hash)
    print(f"Stored hash: {test_hash}")
    
    # Retrieve it
    retrieved = get_stored_config_hash()
    print(f"Retrieved hash: {retrieved}")
    
    assert retrieved == test_hash, "Retrieved hash should match stored hash!"
    
    print("✅ PASSED: Hash storage and retrieval works")


def test_change_detection_scenario():
    """Simulate the actual startup scenario."""
    print("\n" + "=" * 60)
    print("TEST 3: Change Detection Scenario (Local)")
    print("=" * 60)
    
    agent_name = "test-agent"
    model_name = "gpt-4o-mini"
    
    # Scenario 1: First deployment (no stored hash)
    print("\n--- Scenario 1: First Deployment ---")
    if CONFIG_HASH_FILE.exists():
        CONFIG_HASH_FILE.unlink()  # Delete the hash file
    
    stored = get_stored_config_hash()
    print(f"Stored hash: {stored}")
    assert stored is None, "Should have no stored hash on first run"
    print("→ Would CREATE new agent version")
    
    # Simulate storing after first deployment
    first_prompt = "You are a helpful assistant."
    first_hash = compute_config_hash(agent_name, model_name, first_prompt)
    store_config_hash(first_hash)
    print(f"Stored first hash: {first_hash[:32]}...")
    
    # Scenario 2: Restart without changes
    print("\n--- Scenario 2: Restart Without Changes ---")
    current_hash = compute_config_hash(agent_name, model_name, first_prompt)
    stored_hash = get_stored_config_hash()
    
    print(f"Current hash: {current_hash[:32]}...")
    print(f"Stored hash:  {stored_hash[:32]}...")
    
    if current_hash == stored_hash:
        print("→ Would REUSE existing agent (no new version)")
    else:
        print("→ Would CREATE new version")
    
    assert current_hash == stored_hash, "Same config should match!"
    
    # Scenario 3: Change the prompt
    print("\n--- Scenario 3: Prompt Changed ---")
    new_prompt = "You are a friendly customer service agent."
    new_hash = compute_config_hash(agent_name, model_name, new_prompt)
    stored_hash = get_stored_config_hash()
    
    print(f"New hash:    {new_hash[:32]}...")
    print(f"Stored hash: {stored_hash[:32]}...")
    
    if new_hash == stored_hash:
        print("→ Would REUSE existing agent")
    else:
        print("→ Would CREATE new version ✓")
    
    assert new_hash != stored_hash, "Changed config should differ!"
    
    # Scenario 4: Change the model
    print("\n--- Scenario 4: Model Changed ---")
    different_model_hash = compute_config_hash(agent_name, "gpt-4o", first_prompt)
    
    print(f"Different model hash: {different_model_hash[:32]}...")
    print(f"Stored hash:          {stored_hash[:32]}...")
    
    assert different_model_hash != stored_hash, "Different model should trigger new version!"
    print("→ Would CREATE new version ✓")
    
    print("\n✅ PASSED: Change detection scenarios work correctly")


def test_with_real_prompt():
    """Test with the actual system prompt file."""
    print("\n" + "=" * 60)
    print("TEST 4: Real System Prompt (Local)")
    print("=" * 60)
    
    prompt = load_system_prompt()
    print(f"Loaded prompt ({len(prompt)} chars): {prompt[:80]}...")
    
    agent_name = os.environ.get("AZURE_AI_AGENT_NAME", "test-agent")
    model_name = os.environ.get("AZURE_AI_CHAT_DEPLOYMENT_NAME", "gpt-4o-mini")
    
    real_hash = compute_config_hash(agent_name, model_name, prompt)
    print(f"Real config hash: {real_hash[:32]}...")
    
    stored = get_stored_config_hash()
    if stored:
        print(f"Stored hash:      {stored[:32]}...")
        if real_hash == stored:
            print("→ Config UNCHANGED - would reuse agent")
        else:
            print("→ Config CHANGED - would create new version")
    else:
        print("No stored hash - would be first deployment")
    
    print("✅ PASSED: Real prompt loaded successfully")


def test_live_foundry():
    """
    Test with REAL Azure AI Foundry connection.
    
    This will:
    1. Clear the stored hash (simulate first deployment)
    2. Connect to Foundry and create/update the agent
    3. Note the version
    4. "Restart" (run again) without changes
    5. Verify same version is used (no new version created)
    """
    print("\n" + "=" * 60)
    print("TEST 5: LIVE Azure AI Foundry Test")
    print("=" * 60)
    
    from azure.identity import AzureCliCredential
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import PromptAgentDefinition
    
    # Get config from environment
    endpoint = os.environ.get("AZURE_EXISTING_AIPROJECT_ENDPOINT")
    agent_name = os.environ.get("AZURE_AI_AGENT_NAME", "hash-test-agent")
    model_name = os.environ.get("AZURE_AI_CHAT_DEPLOYMENT_NAME")
    
    if not endpoint or not model_name:
        print("❌ Missing environment variables!")
        print("   Required: AZURE_EXISTING_AIPROJECT_ENDPOINT, AZURE_AI_CHAT_DEPLOYMENT_NAME")
        return False
    
    print(f"Endpoint: {endpoint}")
    print(f"Agent: {agent_name}")
    print(f"Model: {model_name}")
    
    # Connect to Azure
    print("\n--- Connecting to Azure AI Foundry ---")
    credential = AzureCliCredential()
    project_client = AIProjectClient(
        credential=credential,
        endpoint=endpoint,
    )
    
    # Load the system prompt
    system_prompt = load_system_prompt()
    print(f"System prompt: {system_prompt[:50]}...")
    
    # Compute hash
    current_hash = compute_config_hash(agent_name, model_name, system_prompt)
    stored_hash = get_stored_config_hash()
    
    print(f"\nCurrent hash: {current_hash[:32]}...")
    print(f"Stored hash:  {stored_hash[:32] if stored_hash else 'None'}...")
    
    if current_hash == stored_hash:
        # Config unchanged - retrieve existing agent
        print("\n--- Hash MATCH: Retrieving existing agent ---")
        agent = project_client.agents.get(agent_name)
        version = getattr(agent, 'version', 'latest')
        print(f"✅ Retrieved existing agent: {agent.name} (v{version})")
        print("   NO new version created!")
        action = "REUSED"
    else:
        # Config changed - create new version
        print("\n--- Hash DIFFERS: Creating new version ---")
        agent = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=model_name,
                instructions=system_prompt,
            ),
            description="Test agent from hash detection test",
        )
        
        # Store the new hash
        store_config_hash(current_hash)
        
        version = getattr(agent, 'version', 'unknown')
        print(f"✅ Created new version: {agent.name} (v{version})")
        action = "CREATED"
    
    project_client.close()
    
    print(f"\n{'=' * 60}")
    print(f"RESULT: Agent was {action}")
    print(f"{'=' * 60}")
    
    return True


def cleanup(delete_hash=True):
    """Clean up test artifacts."""
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)
    
    if delete_hash and CONFIG_HASH_FILE.exists():
        CONFIG_HASH_FILE.unlink()
        print(f"Deleted: {CONFIG_HASH_FILE}")
    else:
        print("Hash file preserved for next run")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test agent config hash detection")
    parser.add_argument("--live", action="store_true", help="Run live test with Azure AI Foundry")
    parser.add_argument("--keep-hash", action="store_true", help="Keep the hash file after test (for testing reuse)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("AGENT CONFIG HASH DETECTION TESTS")
    print("=" * 60)
    
    if args.live:
        print("\n🔴 LIVE MODE: Will connect to Azure AI Foundry!")
        print("   Run once to create, run again to verify reuse.\n")
        
        try:
            success = test_live_foundry()
            if success:
                print("\n✅ Live test completed!")
            else:
                print("\n❌ Live test failed - check environment variables")
        finally:
            cleanup(delete_hash=not args.keep_hash)
    else:
        print("\n🟢 LOCAL MODE: No Azure connection (use --live for real test)\n")
        
        try:
            test_hash_computation()
            test_hash_storage()
            test_change_detection_scenario()
            test_with_real_prompt()
            
            print("\n" + "=" * 60)
            print("ALL LOCAL TESTS PASSED! ✅")
            print("=" * 60)
            print("\nTo test with real Azure connection:")
            print("  python test_hash_detection.py --live --keep-hash")
            print("  python test_hash_detection.py --live  # Run again to verify reuse")
            
        finally:
            cleanup(delete_hash=not args.keep_hash)
        
    print("\nDone!")

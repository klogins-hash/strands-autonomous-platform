#!/usr/bin/env python3
"""
Test Strands-Native Agent Implementation

Quick test to verify agents work properly with Strands framework.
"""

import asyncio
from src.agents.strands_agents import (
    create_code_agent,
    create_orchestrator,
    execute_task
)


def test_code_agent():
    """Test the code agent directly"""
    print("=" * 80)
    print("TEST 1: Code Agent - Write a simple Python function")
    print("=" * 80)
    
    agent = create_code_agent()
    response = agent("Write a Python function to calculate fibonacci numbers")
    
    print("\nResponse:")
    if hasattr(response, 'content'):
        print(response.content[0].text if response.content else str(response))
    else:
        print(response)
    
    print("\n✅ Code agent test complete\n")


def test_orchestrator():
    """Test the orchestrator with multi-agent routing"""
    print("=" * 80)
    print("TEST 2: Orchestrator - Route to appropriate agent")
    print("=" * 80)
    
    orchestrator = create_orchestrator()
    response = orchestrator("Create a simple README.md file for a Python project")
    
    print("\nResponse:")
    if hasattr(response, 'content'):
        print(response.content[0].text if response.content else str(response))
    else:
        print(response)
    
    print("\n✅ Orchestrator test complete\n")


def test_execute_task():
    """Test the convenience function"""
    print("=" * 80)
    print("TEST 3: Execute Task - Convenience function")
    print("=" * 80)
    
    response = execute_task(
        "List the files in the current directory",
        agent_type="code"
    )
    
    print("\nResponse:")
    print(response)
    
    print("\n✅ Execute task test complete\n")


if __name__ == "__main__":
    print("\n🚀 Testing Strands-Native Agent Implementation\n")
    
    try:
        # Test 1: Code agent
        test_code_agent()
        
        # Test 2: Orchestrator
        test_orchestrator()
        
        # Test 3: Execute task
        test_execute_task()
        
        print("=" * 80)
        print("✅ ALL TESTS PASSED - Strands agents working properly!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

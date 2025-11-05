"""
Utility functions for the Strands Autonomous Platform
"""

import json
import re
from typing import Any
from ..models.schemas import AgentRole


def extract_json_from_response(response_text: str) -> dict:
    """
    Extract JSON from Claude's response, handling markdown code blocks
    
    Args:
        response_text: Raw response text from Claude
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        json.JSONDecodeError: If JSON cannot be parsed
    """
    # Try to extract JSON from markdown code blocks if present
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    
    # Remove any leading/trailing whitespace
    response_text = response_text.strip()
    
    # Try to parse
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response:")
        print(f"   Response (first 500 chars): {response_text[:500]}")
        print(f"   Error: {str(e)}")
        raise


def clean_json_string(text: str) -> str:
    """Clean a string to make it valid JSON"""
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    return text


def normalize_agent_role(role_str: str) -> AgentRole:
    """
    Normalize various role string formats to AgentRole enum
    
    Args:
        role_str: Role string from Claude (e.g., "coding", "research", "code")
        
    Returns:
        Normalized AgentRole enum value
    """
    # Mapping of common variations to AgentRole
    role_mapping = {
        "coding": AgentRole.CODE,
        "code": AgentRole.CODE,
        "coder": AgentRole.CODE,
        "developer": AgentRole.CODE,
        "programming": AgentRole.CODE,
        
        "research": AgentRole.RESEARCH,
        "researcher": AgentRole.RESEARCH,
        "researching": AgentRole.RESEARCH,
        
        "writing": AgentRole.WRITER,
        "writer": AgentRole.WRITER,
        "content": AgentRole.WRITER,
        
        "design": AgentRole.DESIGNER,
        "designer": AgentRole.DESIGNER,
        "designing": AgentRole.DESIGNER,
        
        "analysis": AgentRole.ANALYST,
        "analyst": AgentRole.ANALYST,
        "analyzing": AgentRole.ANALYST,
        
        "qa": AgentRole.QA,
        "testing": AgentRole.QA,
        "tester": AgentRole.QA,
        "quality": AgentRole.QA,
        
        "tool_builder": AgentRole.TOOL_BUILDER,
        "tool-builder": AgentRole.TOOL_BUILDER,
        "toolbuilder": AgentRole.TOOL_BUILDER,
        "tools": AgentRole.TOOL_BUILDER,
        
        "orchestrator": AgentRole.ORCHESTRATOR,
        "orchestration": AgentRole.ORCHESTRATOR,
    }
    
    # Normalize the input
    normalized = role_str.lower().strip().replace("-", "_").replace(" ", "_")
    
    # Try direct mapping first
    if normalized in role_mapping:
        return role_mapping[normalized]
    
    # Try as AgentRole value directly
    try:
        return AgentRole(normalized)
    except ValueError:
        pass
    
    # Default to CODE if we can't determine
    print(f"⚠️  Unknown role '{role_str}', defaulting to CODE")
    return AgentRole.CODE

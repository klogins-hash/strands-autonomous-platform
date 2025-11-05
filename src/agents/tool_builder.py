"""
Autonomous Tool Building System

Allows agents to create new tools when they encounter capabilities
that don't exist in their current toolkit.
"""

import asyncio
import json
import uuid
import tempfile
import importlib.util
from typing import Dict, Any, List, Optional
from datetime import datetime

from strands import tool
from anthropic import AsyncAnthropic
from ..core.config import settings
from ..core.database import get_db_session
from ..models.database import Tool as ToolDB


class ToolBuilderMixin:
    """Mixin that gives agents the ability to build new tools"""
    
    def __init__(self):
        self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.built_tools: Dict[str, Any] = {}
    
    async def build_tool(self, tool_description: str, purpose: str, sandbox_id: str) -> str:
        """
        Build a new tool based on description and purpose
        
        Args:
            tool_description: What the tool should do
            purpose: Why the tool is needed (context)
            sandbox_id: E2B sandbox ID for testing
            
        Returns:
            Status message about tool creation
        """
        try:
            # Step 1: Analyze requirements
            requirements = await self._analyze_tool_requirements(tool_description, purpose)
            
            # Step 2: Design tool interface
            design = await self._design_tool_interface(requirements)
            
            # Step 3: Generate implementation
            implementation = await self._generate_tool_implementation(design)
            
            # Step 4: Create comprehensive tests
            tests = await self._generate_tool_tests(implementation, design)
            
            # Step 5: Test in sandbox
            test_results = await self._test_tool_in_sandbox(implementation, tests, sandbox_id)
            
            # Step 6: Validate and save if successful
            if test_results["success_rate"] > 0.9:
                await self._save_tool(design, implementation, test_results)
                return f"✅ Successfully built and saved tool: {design['name']}"
            else:
                return f"❌ Tool failed validation: {test_results['errors']}"
                
        except Exception as e:
            return f"❌ Tool building failed: {str(e)}"
    
    async def _analyze_tool_requirements(self, description: str, purpose: str) -> Dict[str, Any]:
        """Analyze what the tool needs to do"""
        prompt = f"""
        Analyze this tool requirement and create detailed specifications:
        
        Tool Description: {description}
        Purpose: {purpose}
        
        Determine:
        1. Primary function and capabilities
        2. Input parameters and their types
        3. Return value and its type
        4. Error conditions to handle
        5. Dependencies needed
        6. Performance requirements
        7. Security considerations
        
        Return as detailed JSON specification.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-04022",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
    
    async def _design_tool_interface(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Design the tool's interface and structure"""
        prompt = f"""
        Design a Python tool interface based on these requirements:
        
        Requirements: {json.dumps(requirements, indent=2)}
        
        Design:
        1. Function name (snake_case)
        2. Parameter names and types
        3. Return type
        4. Error handling strategy
        5. Docstring format
        6. Tool categorization
        
        The tool should use the @tool decorator from strands-agents.
        
        Return design as JSON.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-040222",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
    
    async def _generate_tool_implementation(self, design: Dict[str, Any]) -> str:
        """Generate the actual Python code for the tool"""
        prompt = f"""
        Write a complete, production-ready Python tool based on this design:
        
        Design: {json.dumps(design, indent=2)}
        
        Requirements:
        1. Use @tool decorator from strands-agents
        2. Include comprehensive type hints
        3. Add thorough error handling
        4. Write clear, efficient code
        5. Include detailed docstring with examples
        6. Handle edge cases gracefully
        7. Add logging where appropriate
        8. Follow Python best practices (PEP 8)
        
        The tool should be self-contained and robust.
        
        Return only the complete Python code.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-040222",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_tool_tests(self, implementation: str, design: Dict[str, Any]) -> str:
        """Generate comprehensive tests for the tool"""
        prompt = f"""
        Generate comprehensive pytest tests for this tool:
        
        Tool Code:
        {implementation}
        
        Design: {json.dumps(design, indent=2)}
        
        Create tests that cover:
        1. Normal operation with valid inputs
        2. Edge cases and boundary conditions
        3. Error handling and invalid inputs
        4. Performance with large inputs
        5. Integration scenarios
        6. Type validation
        
        Include:
        - Clear test descriptions
        - Assertions for all cases
        - Setup and teardown if needed
        - Mock external dependencies
        - Parameterized tests where appropriate
        
        Return complete pytest test code.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-040222",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _test_tool_in_sandbox(self, implementation: str, tests: str, sandbox_id: str) -> Dict[str, Any]:
        """Test the tool in an isolated sandbox environment"""
        from .sandbox_manager import SandboxManager
        
        sandbox = SandboxManager()
        
        try:
            # Save tool and tests to sandbox
            await sandbox.write_file(sandbox_id, "new_tool.py", implementation)
            await sandbox.write_file(sandbox_id, "test_new_tool.py", tests)
            
            # Install dependencies if needed
            install_result = await sandbox.execute_shell(
                sandbox_id, 
                "pip install pytest pytest-asyncio --quiet"
            )
            
            # Run the tests
            test_output = await sandbox.execute_shell(
                sandbox_id,
                "python -m pytest test_new_tool.py -v --tb=short"
            )
            
            # Analyze test results
            success_rate = self._analyze_test_results(test_output)
            
            return {
                "success_rate": success_rate,
                "test_output": test_output,
                "errors": [] if success_rate > 0.9 else ["Tests failed"]
            }
            
        except Exception as e:
            return {
                "success_rate": 0.0,
                "test_output": "",
                "errors": [str(e)]
            }
    
    def _analyze_test_results(self, test_output: str) -> float:
        """Analyze pytest output to calculate success rate"""
        if "passed" not in test_output:
            return 0.0
        
        # Extract passed/failed counts from pytest output
        lines = test_output.split('\n')
        for line in lines:
            if "passed" in line and "failed" in line:
                # Parse line like: "5 passed, 1 failed"
                parts = line.split()
                passed = failed = 0
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        passed = int(parts[i-1])
                    elif part == "failed" and i > 0:
                        failed = int(parts[i-1])
                
                total = passed + failed
                return passed / total if total > 0 else 0.0
        
        # If we can't parse, assume success if "passed" is in output
        return 0.8
    
    async def _save_tool(self, design: Dict[str, Any], implementation: str, test_results: Dict[str, Any]):
        """Save successful tool to database and storage"""
        async for session in get_db_session():
            # Save to database
            tool_record = ToolDB(
                name=design["name"],
                description=design.get("description", ""),
                code=implementation,
                success_rate=test_results["success_rate"],
                usage_count=0
            )
            session.add(tool_record)
            await session.commit()
            
            # TODO: Save to S3 for persistence
            # TODO: Create embedding for semantic search
            
            self.built_tools[design["name"]] = {
                "design": design,
                "implementation": implementation,
                "test_results": test_results
            }


class AutoToolBuilder:
    """Standalone tool builder for creating tools on demand"""
    
    def __init__(self):
        self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.mixin = ToolBuilderMixin()
    
    async def build_custom_tool(self, requirement: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Build a custom tool based on a natural language requirement
        
        Args:
            requirement: Natural language description of what tool is needed
            context: Additional context about why the tool is needed
            
        Returns:
            Tool creation result with code and tests
        """
        purpose = context.get("purpose", "General automation") if context else "General automation"
        
        # Create a temporary sandbox for testing
        from .sandbox_manager import SandboxManager
        sandbox = SandboxManager()
        sandbox_id = await sandbox.create_sandbox("tool_builder_temp")
        
        try:
            result = await self.mixin.build_tool(requirement, purpose, sandbox_id)
            
            # Clean up sandbox
            await sandbox.cleanup_sandbox(sandbox_id)
            
            return {
                "status": "success" if "✅" in result else "failed",
                "message": result,
                "tool_code": self.mixin.built_tools.get(list(self.mixin.built_tools.keys())[-1], {}).get("implementation"),
                "tool_design": self.mixin.built_tools.get(list(self.mixin.built_tools.keys())[-1], {}).get("design")
            }
            
        except Exception as e:
            await sandbox.cleanup_sandbox(sandbox_id)
            return {
                "status": "failed",
                "message": f"Tool creation failed: {str(e)}",
                "tool_code": None,
                "tool_design": None
            }


# Example specialized tool builders
class DataProcessingToolBuilder:
    """Builds tools for data processing tasks"""
    
    @staticmethod
    async def build_csv_processor(operation: str) -> str:
        """Build a CSV processing tool for specific operations"""
        # Implementation for CSV tool building
        pass


class APIIntegrationToolBuilder:
    """Builds tools for API integrations"""
    
    @staticmethod
    async def build_api_client(api_spec: Dict[str, Any]) -> str:
        """Build an API client tool based on OpenAPI spec"""
        # Implementation for API client building
        pass


class WebScrapingToolBuilder:
    """Builds tools for web scraping"""
    
    @staticmethod
    async def build_scraper(target_site: str, data_points: List[str]) -> str:
        """Build a web scraper for specific site and data points"""
        # Implementation for web scraper building
        pass

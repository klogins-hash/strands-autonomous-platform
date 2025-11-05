"""
Specialized Autonomous Agents for Different Domains

Each agent is designed to excel in their specific domain while maintaining
the ability to collaborate with other agents and build tools when needed.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import json

from strands import Agent, tool
from anthropic import AsyncAnthropic
from ..models.schemas import AgentSpec, AgentRole
from ..core.config import settings
from .tool_builder import ToolBuilderMixin
from .sandbox_manager import SandboxManager


class BaseSpecializedAgent:
    """Base class for all specialized agents with common capabilities"""
    
    def __init__(self, role: AgentRole):
        self.role = role
        self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.sandbox_manager = SandboxManager()
        self.tool_builder = ToolBuilderMixin()
        self.task_id: Optional[uuid.UUID] = None
        self.agent_instance: Optional[Agent] = None
        self.progress: float = 0.0
        
    async def create_instance(self, spec: AgentSpec, task_id: uuid.UUID) -> 'BaseSpecializedAgent':
        """Create a configured instance of this agent"""
        self.task_id = task_id
        
        # Create Strands agent with role-specific configuration
        self.agent_instance = Agent(
            system_prompt=spec.system_prompt,
            tools=await self._get_tools(spec.tools)
        )
        
        # Create sandbox environment
        self.sandbox_id = await self.sandbox_manager.create_sandbox(
            f"{self.role.value}_agent_{task_id}"
        )
        
        return self
    
    async def _get_tools(self, tool_names: List[str]) -> List[Any]:
        """Get tool instances by name"""
        tools = []
        
        # Add base tools available to all agents
        tools.extend([
            self.file_reader,
            self.file_writer,
            self.log_progress,
            self.request_tool,
            self.communicate_with_agent
        ])
        
        # Add role-specific tools
        for tool_name in tool_names:
            if hasattr(self, tool_name):
                tools.append(getattr(self, tool_name))
        
        return tools
    
    @tool
    async def execute_phase(self, phase_description: str, phase_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific phase of the overall task
        
        Args:
            phase_description: What this phase needs to accomplish
            phase_config: Configuration and requirements for this phase
            
        Returns:
            Results and artifacts from this phase
        """
        try:
            # Update status to executing
            await self._update_status("executing")
            
            # Analyze phase requirements
            requirements = await self._analyze_phase_requirements(phase_description, phase_config)
            
            # Check if we need additional tools
            await self._ensure_required_tools(requirements)
            
            # Execute the phase
            result = await self._perform_phase_work(requirements)
            
            # Validate results
            validated_result = await self._validate_results(result)
            
            # Update status to done
            await self._update_status("done")
            self.progress = 100.0
            
            return validated_result
            
        except Exception as e:
            await self._update_status("error")
            await self._log_error(f"Phase execution failed: {str(e)}")
            raise
    
    async def _analyze_phase_requirements(self, description: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze what the phase requires and create execution plan"""
        prompt = f"""
        As a {self.role.value} agent, analyze this phase requirement:
        
        Description: {description}
        Configuration: {json.dumps(config, indent=2)}
        
        Determine:
        1. Specific actions needed
        2. Tools required
        3. Expected outputs
        4. Success criteria
        5. Potential challenges
        
        Return as JSON.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-04022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
    
    async def _ensure_required_tools(self, requirements: Dict[str, Any]):
        """Ensure we have all necessary tools, build if needed"""
        required_tools = requirements.get("tools_required", [])
        
        for tool_name in required_tools:
            if not hasattr(self, tool_name):
                # Build the tool autonomously
                await self.tool_builder.build_tool(tool_name, requirements, self.sandbox_id)
    
    async def _perform_phase_work(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual work for this phase"""
        # This should be implemented by each specialized agent
        raise NotImplementedError("Each agent must implement _perform_phase_work")
    
    async def _validate_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that results meet requirements"""
        # Basic validation - can be extended by each agent type
        if not result:
            raise ValueError("No results produced")
        
        # Add metadata
        result["validation"] = {
            "agent_role": self.role.value,
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": str(self.task_id)
        }
        
        return result
    
    @tool
    async def file_reader(self, file_path: str) -> str:
        """Read file contents from sandbox"""
        return await self.sandbox_manager.read_file(self.sandbox_id, file_path)
    
    @tool
    async def file_writer(self, file_path: str, content: str) -> bool:
        """Write content to file in sandbox"""
        return await self.sandbox_manager.write_file(self.sandbox_id, file_path, content)
    
    @tool
    async def log_progress(self, message: str, progress_percentage: float = None):
        """Log progress for real-time updates"""
        if progress_percentage is not None:
            self.progress = progress_percentage
        
        await self._log_activity(f"Progress: {message} ({self.progress}%)")
    
    @tool
    async def request_tool(self, tool_description: str, purpose: str) -> str:
        """
        Request a new tool to be built
        
        Args:
            tool_description: What the tool should do
            purpose: Why the tool is needed
            
        Returns:
            Status of tool creation
        """
        return await self.tool_builder.build_tool(tool_description, purpose, self.sandbox_id)
    
    @tool
    async def communicate_with_agent(self, target_role: str, message: str) -> str:
        """Send message to another agent"""
        # TODO: Implement agent-to-agent messaging via Redis pub/sub
        await self._log_activity(f"Message to {target_role}: {message}")
        return "Message sent"
    
    async def _update_status(self, status: str):
        """Update agent status in database"""
        # TODO: Update database
        await self._log_activity(f"Status updated to: {status}")
    
    async def _log_activity(self, message: str):
        """Log activity for monitoring"""
        # TODO: Log to database and WebSocket
        print(f"[{self.role.value}] {message}")
    
    async def _log_error(self, error: str):
        """Log error for troubleshooting"""
        await self._log_activity(f"ERROR: {error}")


class ResearchAgent(BaseSpecializedAgent):
    """Agent specialized in research, data gathering, and analysis"""
    
    def __init__(self):
        super().__init__(AgentRole.RESEARCH)
    
    async def _get_tools(self, tool_names: List[str]) -> List[Any]:
        tools = await super()._get_tools(tool_names)
        tools.extend([
            self.web_search,
            self.extract_web_content,
            self.verify_sources,
            self.cite_sources
        ])
        return tools
    
    @tool
    async def web_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search the web for information"""
        # TODO: Implement web search using Serper or similar API
        return [{"title": "Result 1", "url": "example.com", "snippet": "..."}]
    
    @tool
    async def extract_web_content(self, url: str) -> str:
        """Extract and clean content from a web page"""
        # TODO: Implement web scraping with BeautifulSoup
        return "Extracted content from " + url
    
    @tool
    async def verify_sources(self, sources: List[str]) -> Dict[str, bool]:
        """Verify credibility of sources"""
        # TODO: Implement source verification logic
        return {source: True for source in sources}
    
    @tool
    async def cite_sources(self, sources: List[Dict[str, Any]], format_style: str = "APA") -> str:
        """Generate citations in specified format"""
        # TODO: Implement citation generation
        return "Generated citations"
    
    async def _perform_phase_work(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Perform research-specific work"""
        research_query = requirements.get("query", "")
        
        # Search research
        search_results = await self.web_search(research_query)
        
        # Extract and analyze content
        findings = []
        for result in search_results[:5]:  # Analyze top 5 results
            content = await self.extract_web_content(result["url"])
            analysis = await self._analyze_content(content, research_query)
            findings.append({
                "source": result,
                "content": content,
                "analysis": analysis
            })
        
        # Synthesize findings
        synthesis = await self._synthesize_findings(findings, research_query)
        
        return {
            "research_query": research_query,
            "sources": search_results,
            "findings": findings,
            "synthesis": synthesis,
            "recommendations": await self._generate_recommendations(findings)
        }
    
    async def _analyze_content(self, content: str, query: str) -> Dict[str, Any]:
        """Analyze content relevance and quality"""
        prompt = f"""
        Analyze this content for relevance to the research query:
        
        Query: {query}
        Content: {content[:1000]}...
        
        Rate:
        1. Relevance (0-10)
        2. Credibility (0-10)
        3. Information density (0-10)
        4. Key insights
        
        Return as JSON.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-04022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
    
    async def _synthesize_findings(self, findings: List[Dict[str, Any]], query: str) -> str:
        """Synthesize research findings into coherent summary"""
        findings_text = json.dumps(findings, indent=2)
        
        prompt = f"""
        Synthesize these research findings into a comprehensive summary:
        
        Research Query: {query}
        Findings: {findings_text}
        
        Create:
        1. Executive summary
        2. Key themes and patterns
        3. Important insights
        4. Knowledge gaps identified
        
        Return as structured text.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-04022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on research"""
        # TODO: Implement recommendation generation
        return ["Recommendation 1", "Recommendation 2"]


class CodeAgent(BaseSpecializedAgent):
    """Agent specialized in programming, development, and technical tasks"""
    
    def __init__(self):
        super().__init__(AgentRole.CODE)
    
    async def _get_tools(self, tool_names: List[str]) -> List[Any]:
        tools = await super()._get_tools(tool_names)
        tools.extend([
            self.python_repl,
            self.execute_shell,
            self.install_package,
            self.run_tests,
            self.review_code
        ])
        return tools
    
    @tool
    async def python_repl(self, code: str) -> str:
        """Execute Python code in sandbox"""
        return await self.sandbox_manager.execute_python(self.sandbox_id, code)
    
    @tool
    async def execute_shell(self, command: str) -> str:
        """Execute shell command in sandbox"""
        return await self.sandbox_manager.execute_shell(self.sandbox_id, command)
    
    @tool
    async def install_package(self, package_name: str, package_manager: str = "pip") -> bool:
        """Install package using specified package manager"""
        if package_manager == "pip":
            result = await self.execute_shell(f"pip install {package_name}")
        elif package_manager == "npm":
            result = await self.execute_shell(f"npm install {package_name}")
        else:
            raise ValueError(f"Unsupported package manager: {package_manager}")
        
        return "Successfully installed" in result
    
    @tool
    async def run_tests(self, test_path: str = ".") -> Dict[str, Any]:
        """Run tests and return results"""
        # Try different test frameworks
        test_commands = [
            "python -m pytest",
            "python -m unittest",
            "npm test"
        ]
        
        for cmd in test_commands:
            try:
                result = await self.execute_shell(cmd)
                if "passed" in result.lower() or "failed" in result.lower():
                    return {"command": cmd, "output": result, "success": True}
            except:
                continue
        
        return {"success": False, "error": "No test framework found"}
    
    @tool
    async def review_code(self, file_path: str) -> Dict[str, Any]:
        """Review code for quality and best practices"""
        code = await self.file_reader(file_path)
        
        prompt = f"""
        Review this code for:
        1. Code quality and style
        2. Best practices adherence
        3. Potential bugs or issues
        4. Performance considerations
        5. Security vulnerabilities
        
        Code: {code}
        
        Return detailed review as JSON.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-04022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
    
    async def _perform_phase_work(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Perform code-specific work"""
        task_type = requirements.get("task_type", "development")
        
        if task_type == "development":
            return await self._handle_development_task(requirements)
        elif task_type == "debugging":
            return await self._handle_debugging_task(requirements)
        elif task_type == "analysis":
            return await self._handle_code_analysis(requirements)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _handle_development_task(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Handle software development tasks"""
        spec = requirements.get("specification", "")
        
        # Generate code
        prompt = f"""
        Generate high-quality code based on this specification:
        
        {spec}
        
        Requirements:
        - Write clean, well-documented code
        - Follow best practices
        - Include error handling
        - Add comments where necessary
        
        Return the complete code.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-040222",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        code = response.content[0].text
        
        # Save code to file
        file_name = requirements.get("file_name", "generated_code.py")
        await self.file_writer(file_name, code)
        
        # Test the code
        test_result = await self.run_tests()
        
        # Review the code
        review = await self.review_code(file_name)
        
        return {
            "task_type": "development",
            "file_name": file_name,
            "code": code,
            "test_result": test_result,
            "code_review": review
        }
    
    async def _handle_debugging_task(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Handle debugging tasks"""
        # TODO: Implement debugging logic
        return {"task_type": "debugging", "status": "completed"}
    
    async def _handle_code_analysis(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code analysis tasks"""
        # TODO: Implement code analysis logic
        return {"task_type": "analysis", "status": "completed"}


class WriterAgent(BaseSpecializedAgent):
    """Agent specialized in content creation, writing, and documentation"""
    
    def __init__(self):
        super().__init__(AgentRole.WRITER)
    
    async def _perform_phase_work(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Perform writing-specific work"""
        content_type = requirements.get("content_type", "article")
        topic = requirements.get("topic", "")
        
        # Generate content
        content = await self._generate_content(content_type, topic, requirements)
        
        # Edit and refine
        refined_content = await self._refine_content(content)
        
        # Format appropriately
        formatted_content = await self._format_content(refined_content, content_type)
        
        return {
            "content_type": content_type,
            "topic": topic,
            "content": formatted_content,
            "word_count": len(formatted_content.split())
        }
    
    async def _generate_content(self, content_type: str, topic: str, requirements: Dict[str, Any]) -> str:
        """Generate initial content draft"""
        prompt = f"""
        Write a {content_type} about: {topic}
        
        Requirements: {json.dumps(requirements, indent=2)}
        
        Create engaging, well-structured content that is:
        1. Informative and accurate
        2. Well-organized and easy to read
        3. Appropriate for the target audience
        4. Comprehensive yet concise
        
        Return the complete content.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-040222",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _refine_content(self, content: str) -> str:
        """Edit and improve content quality"""
        prompt = f"""
        Edit and improve this content:
        
        {content}
        
        Focus on:
        1. Clarity and readability
        2. Grammar and style
        3. Flow and structure
        4. Engagement and impact
        
        Return the refined content.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-040222",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _format_content(self, content: str, content_type: str) -> str:
        """Format content according to type specifications"""
        # TODO: Implement type-specific formatting
        return content


class ToolBuilderAgent(BaseSpecializedAgent):
    """Agent specialized in building new tools autonomously"""
    
    def __init__(self):
        super().__init__(AgentRole.TOOL_BUILDER)
    
    async def _perform_phase_work(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Build custom tools as needed"""
        tool_spec = requirements.get("tool_specification", {})
        
        # Design the tool
        design = await self._design_tool(tool_spec)
        
        # Implement the tool
        implementation = await self._implement_tool(design)
        
        # Test the tool
        test_results = await self._test_tool(implementation)
        
        # Document the tool
        documentation = await self._document_tool(design, implementation)
        
        return {
            "tool_design": design,
            "implementation": implementation,
            "test_results": test_results,
            "documentation": documentation
        }
    
    async def _design_tool(self, tool_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Design tool architecture and interface"""
        prompt = f"""
        Design a Python tool based on this specification:
        
        {json.dumps(tool_spec, indent=2)}
        
        Design:
        1. Function signature and parameters
        2. Error handling approach
        3. Dependencies required
        4. Testing strategy
        5. Usage examples
        
        Return detailed design as JSON.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-040222",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
    
    async def _implement_tool(self, design: Dict[str, Any]) -> str:
        """Write the actual tool code"""
        prompt = f"""
        Implement the Python tool based on this design:
        
        {json.dumps(design, indent=2)}
        
        Requirements:
        - Use @tool decorator from strands
        - Include comprehensive error handling
        - Add type hints
        - Write clean, efficient code
        - Include docstring with examples
        
        Return the complete tool code.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-040222",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _test_tool(self, implementation: str) -> Dict[str, Any]:
        """Test the implemented tool"""
        # Save tool to file
        await self.file_writer("new_tool.py", implementation)
        
        # Create test file
        test_code = await self._generate_test_code(implementation)
        await self.file_writer("test_new_tool.py", test_code)
        
        # Run tests
        test_result = await self.run_tests("test_new_tool.py")
        
        return test_result
    
    async def _generate_test_code(self, tool_code: str) -> str:
        """Generate comprehensive tests for the tool"""
        prompt = f"""
        Generate comprehensive pytest tests for this tool:
        
        {tool_code}
        
        Include:
        1. Unit tests for all functions
        2. Edge case testing
        3. Error handling tests
        4. Integration tests if applicable
        
        Return complete test code.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-040222",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _document_tool(self, design: Dict[str, Any], implementation: str) -> str:
        """Create comprehensive documentation"""
        # TODO: Implement documentation generation
        return "Tool documentation"


# Create other specialized agents with similar structure
class DesignerAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__(AgentRole.DESIGNER)
    
    async def _perform_phase_work(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implement design-specific work
        return {"task_type": "design", "status": "completed"}


class AnalystAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__(AgentRole.ANALYST)
    
    async def _perform_phase_work(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implement analysis-specific work
        return {"task_type": "analysis", "status": "completed"}


class QAAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__(AgentRole.QA)
    
    async def _perform_phase_work(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implement QA-specific work
        return {"task_type": "qa", "status": "completed"}

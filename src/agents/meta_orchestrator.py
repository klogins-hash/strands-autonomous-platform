"""
Meta-Orchestrator Agent - The Brain of the Autonomous Agent Platform

This agent is responsible for:
1. Understanding user goals from natural language
2. Decomposing complex goals into executable subtasks
3. Determining optimal agent team composition
4. Creating multi-phase execution plans
5. Monitoring execution and dynamic adjustment
6. Autonomous error recovery
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid

from strands import Agent, tool
from anthropic import AsyncAnthropic
from ..models.schemas import (
    TaskCreate, ExecutionPlan, AgentSpec, AgentRole, 
    TaskStatus, ActivityLog
)
from ..models.database import Task, AgentInstance, ActivityLog as ActivityLogDB
from ..core.config import settings
from ..core.database import get_db_session
from ..core.utils import extract_json_from_response, normalize_agent_role


class MetaOrchestrator:
    """The central intelligence that coordinates autonomous agent teams"""
    
    def __init__(self):
        self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.active_tasks: Dict[str, Dict] = {}
        self.agent_pool: Dict[AgentRole, Agent] = {}
        
    async def initialize(self):
        """Initialize the orchestrator and create agent pool"""
        await self._create_agent_pool()
        
    async def _create_agent_pool(self):
        """Create specialized agents for different roles"""
        from .specialized_agents import (
            ResearchAgent, CodeAgent, WriterAgent, DesignerAgent,
            AnalystAgent, QAAgent, ToolBuilderAgent
        )
        
        self.agent_pool = {
            AgentRole.RESEARCH: ResearchAgent(),
            AgentRole.CODE: CodeAgent(),
            AgentRole.WRITER: WriterAgent(),
            AgentRole.DESIGNER: DesignerAgent(),
            AgentRole.ANALYST: AnalystAgent(),
            AgentRole.QA: QAAgent(),
            AgentRole.TOOL_BUILDER: ToolBuilderAgent(),
        }
    
    @tool
    async def orchestrate_task(self, task_description: str, project_id: str) -> ExecutionPlan:
        """
        Analyze a task description and create an execution plan with optimal agent team.
        
        Args:
            task_description: Natural language description of what the user wants to accomplish
            project_id: ID of the project this task belongs to
            
        Returns:
            ExecutionPlan with phases, agents, and dependencies
        """
        try:
            # Step 1: Parse and understand the goal
            parsed_goal = await self._parse_goal(task_description)
            
            # Step 2: Search for similar past executions
            similar_plan = await self._find_similar_executions(parsed_goal)
            if similar_plan:
                return await self._adapt_existing_plan(similar_plan, parsed_goal)
            
            # Step 3: Decompose into phases and tasks
            phases = await self._decompose_task(parsed_goal)
            
            # Step 4: Determine optimal agent team
            agents = await self._determine_agent_team(phases)
            
            # Step 5: Identify dependencies and estimate duration
            dependencies = await self._identify_dependencies(phases)
            duration = await self._estimate_execution_time(phases, agents)
            
            # Step 6: Create execution plan
            plan = ExecutionPlan(
                phases=phases,
                agents=agents,
                estimated_duration=duration,
                dependencies=dependencies
            )
            
            return plan
            
        except Exception as e:
            raise Exception(f"Task orchestration failed: {str(e)}")
    
    async def _parse_goal(self, description: str) -> Dict[str, Any]:
        """Use Claude to parse natural language into structured requirements"""
        prompt = f"""
        Analyze this task description and extract structured requirements:
        
        Task: "{description}"
        
        Return JSON with:
        - primary_goal: Main objective
        - required_capabilities: List of needed capabilities (research, coding, writing, design, analysis, qa)
        - complexity_level: simple, moderate, complex
        - estimated_scope: small, medium, large
        - key_deliverables: List of expected outputs
        - constraints: Any limitations or requirements
        """
        
        response = await self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract and parse JSON from response
        response_text = response.content[0].text
        return extract_json_from_response(response_text)
    
    async def _find_similar_executions(self, parsed_goal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Search vector database for similar past executions"""
        # TODO: Implement vector search using pgvector
        # For now, return None to always create new plans
        return None
    
    async def _adapt_existing_plan(self, similar_plan: Dict[str, Any], parsed_goal: Dict[str, Any]) -> ExecutionPlan:
        """Adapt an existing successful plan for the current goal"""
        # TODO: Implement plan adaptation logic
        pass
    
    async def _decompose_task(self, parsed_goal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break down the goal into executable phases"""
        prompt = f"""
        Based on these requirements, break down the task into 3-10 executable phases:
        
        Requirements: {json.dumps(parsed_goal, indent=2)}
        
        For each phase, provide:
        - phase_name: Clear, descriptive name
        - description: What this phase accomplishes
        - required_role: Which agent type should handle this
        - estimated_duration: Time in minutes
        - dependencies: List of phase names this depends on
        - parallel_possible: Can this run in parallel with other phases?
        
        Return as JSON array of phases.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return extract_json_from_response(response.content[0].text)
    
    async def _determine_agent_team(self, phases: List[Dict[str, Any]]) -> List[AgentSpec]:
        """Create optimal agent specifications based on phase requirements"""
        required_roles = set()
        for phase in phases:
            required_roles.add(normalize_agent_role(phase["required_role"]))
        
        agents = []
        for role in required_roles:
            agent_spec = await self._create_agent_spec(role, phases)
            agents.append(agent_spec)
        
        return agents
    
    async def _create_agent_spec(self, role: AgentRole, phases: List[Dict[str, Any]]) -> AgentSpec:
        """Create detailed specification for an agent"""
        # Filter phases this agent will handle
        agent_phases = [p for p in phases if p["required_role"] == role.value]
        
        # Determine capabilities needed
        capabilities = await self._determine_capabilities(role, agent_phases)
        
        # Generate system prompt
        system_prompt = await self._generate_system_prompt(role, capabilities)
        
        return AgentSpec(
            role=role,
            name=f"{role.value.title()} Agent",
            system_prompt=system_prompt,
            tools=await self._get_required_tools(role, agent_phases),
            capabilities=capabilities
        )
    
    async def _determine_capabilities(self, role: AgentRole, phases: List[Dict[str, Any]]) -> List[str]:
        """Determine what capabilities an agent needs based on its phases"""
        capability_map = {
            AgentRole.RESEARCH: ["web_search", "data_extraction", "fact_checking", "source_evaluation"],
            AgentRole.CODE: ["programming", "debugging", "code_review", "testing", "documentation"],
            AgentRole.WRITER: ["content_creation", "editing", "formatting", "storytelling", "technical_writing"],
            AgentRole.DESIGNER: ["ui_design", "visual_composition", "branding", "user_experience"],
            AgentRole.ANALYST: ["data_analysis", "statistical_modeling", "insight_generation", "reporting"],
            AgentRole.QA: ["testing", "quality_assurance", "bug_detection", "validation"],
            AgentRole.TOOL_BUILDER: ["tool_development", "api_integration", "automation", "scripting"]
        }
        
        return capability_map.get(role, ["general_problem_solving"])
    
    async def _generate_system_prompt(self, role: AgentRole, capabilities: List[str]) -> str:
        """Generate role-specific system prompt"""
        base_prompt = f"""
        You are a specialized {role.value.title()} Agent in an autonomous team.
        Your capabilities include: {', '.join(capabilities)}.
        
        Key Principles:
        1. Work autonomously and take initiative
        2. Communicate clearly with other agents
        3. Ask for help when needed, but try to solve problems independently first
        4. Document your decisions and progress
        5. Learn from each interaction and improve over time
        6. Focus on delivering high-quality, actionable results
        
        You are part of a team working to achieve complex goals. 
        Coordinate with other agents through shared context and messaging.
        Always strive for excellence in your domain.
        """
        
        role_specific_prompts = {
            AgentRole.RESEARCH: """
            As a Research Agent:
            - Find accurate, up-to-date information from reliable sources
            - Verify facts and cite sources properly
            - Synthesize information into clear insights
            - Identify knowledge gaps and recommend further research
            """,
            
            AgentRole.CODE: """
            As a Code Agent:
            - Write clean, efficient, and well-documented code
            - Follow best practices and design patterns
            - Test your code thoroughly
            - Consider scalability and maintainability
            - Use appropriate tools and frameworks
            """,
            
            AgentRole.TOOL_BUILDER: """
            As a Tool Builder Agent:
            - Identify when new tools are needed
            - Design tools that are reusable and robust
            - Test tools thoroughly before deployment
            - Document tool usage and interfaces
            - Consider edge cases and error handling
            """
        }
        
        return base_prompt + role_specific_prompts.get(role, "")
    
    async def _get_required_tools(self, role: AgentRole, phases: List[Dict[str, Any]]) -> List[str]:
        """Determine which tools an agent needs"""
        tool_map = {
            AgentRole.RESEARCH: ["web_search", "http_request", "file_reader"],
            AgentRole.CODE: ["python_repl", "file_editor", "shell", "git"],
            AgentRole.WRITER: ["file_editor", "text_processor", "formatter"],
            AgentRole.DESIGNER: ["image_processor", "ui_generator", "prototype_builder"],
            AgentRole.ANALYST: ["python_repl", "data_processor", "chart_generator"],
            AgentRole.QA: ["testing_framework", "validator", "bug_detector"],
            AgentRole.TOOL_BUILDER: ["python_repl", "file_editor", "package_manager", "testing_framework"]
        }
        
        return tool_map.get(role, ["file_reader", "file_writer"])
    
    async def _identify_dependencies(self, phases: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Create dependency graph between phases"""
        dependencies = []
        for phase in phases:
            for dep in phase.get("dependencies", []):
                dependencies.append({
                    "from": dep,
                    "to": phase["phase_name"],
                    "type": "completion"
                })
        return dependencies
    
    async def _estimate_execution_time(self, phases: List[Dict[str, Any]], agents: List[AgentSpec]) -> int:
        """Estimate total execution time in minutes"""
        # Calculate sequential time (phases that can't run in parallel)
        sequential_phases = []
        parallel_groups = []
        
        # Simple estimation: sum of all phase durations
        total_minutes = sum(phase.get("estimated_duration", 30) for phase in phases)
        
        # Apply parallelization discount
        parallelizable_count = sum(1 for phase in phases if phase.get("parallel_possible", False))
        if parallelizable_count > 0:
            parallel_discount = min(0.3, parallelizable_count * 0.1)
            total_minutes = int(total_minutes * (1 - parallel_discount))
        
        return max(total_minutes, 5)  # Minimum 5 minutes
    
    async def execute_plan(self, plan: ExecutionPlan, task_id: uuid.UUID) -> Dict[str, Any]:
        """Execute the orchestration plan with autonomous agents"""
        try:
            # Create agent instances
            agent_instances = await self._spawn_agents(plan.agents, task_id)
            
            # Execute phases according to dependencies
            results = await self._execute_phases(plan.phases, agent_instances)
            
            # Synthesize final result
            final_result = await self._synthesize_results(results)
            
            return final_result
            
        except Exception as e:
            await self._handle_execution_error(task_id, str(e))
            raise
    
    async def _spawn_agents(self, agent_specs: List[AgentSpec], task_id: uuid.UUID) -> Dict[AgentRole, Any]:
        """Create and initialize agent instances"""
        instances = {}
        
        for spec in agent_specs:
            # Get agent from pool
            agent_template = self.agent_pool[spec.role]
            
            # Create instance with specific configuration
            instance = await agent_template.create_instance(spec, task_id)
            instances[spec.role] = instance
            
            # Save to database
            await self._save_agent_instance(spec, task_id)
        
        return instances
    
    async def _execute_phases(self, phases: List[Dict[str, Any]], agents: Dict[AgentRole, Any]) -> Dict[str, Any]:
        """Execute all phases with proper dependency management"""
        results = {}
        completed_phases = set()
        
        # Continue until all phases are complete
        while len(completed_phases) < len(phases):
            # Find phases ready to execute
            ready_phases = []
            for phase in phases:
                phase_name = phase["phase_name"]
                if phase_name not in completed_phases:
                    deps = phase.get("dependencies", [])
                    if all(dep in completed_phases for dep in deps):
                        ready_phases.append(phase)
            
            # Execute ready phases in parallel
            if ready_phases:
                tasks = []
                for phase in ready_phases:
                    role = normalize_agent_role(phase["required_role"])
                    agent = agents[role]
                    task = asyncio.create_task(
                        self._execute_single_phase(phase, agent)
                    )
                    tasks.append((phase["phase_name"], task))
                
                # Wait for parallel execution
                for phase_name, task in tasks:
                    try:
                        result = await task
                        results[phase_name] = result
                        completed_phases.add(phase_name)
                    except Exception as e:
                        # Handle phase failure
                        await self._handle_phase_error(phase_name, str(e))
                        raise
            else:
                # No ready phases (likely due to failed dependencies)
                raise Exception("Execution deadlock: no phases ready to execute")
        
        return results
    
    async def _execute_single_phase(self, phase: Dict[str, Any], agent: Any) -> Dict[str, Any]:
        """Execute a single phase using the appropriate agent"""
        phase_name = phase["phase_name"]
        description = phase["description"]
        
        # Log phase start
        await self._log_activity(
            task_id=agent.task_id,
            activity_type="phase_start",
            message=f"Starting phase: {phase_name}"
        )
        
        try:
            # Execute phase
            result = await agent.execute_phase(description, phase)
            
            # Log phase completion
            await self._log_activity(
                task_id=agent.task_id,
                activity_type="phase_complete",
                message=f"Completed phase: {phase_name}"
            )
            
            return result
            
        except Exception as e:
            # Log phase error
            await self._log_activity(
                task_id=agent.task_id,
                activity_type="phase_error",
                message=f"Error in phase {phase_name}: {str(e)}"
            )
            raise
    
    async def _synthesize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize results from all phases into final output"""
        prompt = f"""
        Synthesize these phase results into a comprehensive final output:
        
        Results: {json.dumps(results, indent=2)}
        
        Create:
        1. Executive summary of what was accomplished
        2. Key deliverables and artifacts
        3. Insights and recommendations
        4. Next steps or follow-up actions
        
        Return as structured JSON.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return extract_json_from_response(response.content[0].text)
    
    async def _save_agent_instance(self, spec: AgentSpec, task_id: uuid.UUID):
        """Save agent instance to database"""
        try:
            async for session in get_db_session():
                instance = AgentInstance(
                    task_id=task_id,
                    role=spec.role.value,
                    status="idle"
                )
                session.add(instance)
                await session.commit()
        except RuntimeError:
            # Database not initialized - skip saving for now
            pass
    
    async def _log_activity(self, task_id: uuid.UUID, activity_type: str, message: str):
        """Log activity for real-time updates"""
        try:
            async for session in get_db_session():
                activity = ActivityLogDB(
                    task_id=task_id,
                    activity_type=activity_type,
                    message=message
                )
                session.add(activity)
                await session.commit()
        except RuntimeError:
            # Database not initialized - skip logging for now
            pass
    
    async def _handle_execution_error(self, task_id: uuid.UUID, error: str):
        """Handle execution errors with autonomous recovery"""
        await self._log_activity(
            task_id=task_id,
            activity_type="execution_error",
            message=f"Execution failed: {error}"
        )
        
        # TODO: Implement autonomous recovery strategies
        # 1. Retry failed phases
        # 2. Try alternative approaches
        # 3. Search for similar solutions
        # 4. Escalate to user if all recovery fails
    
    async def _handle_phase_error(self, phase_name: str, error: str):
        """Handle individual phase errors"""
        # TODO: Implement phase-specific error recovery
        pass


# Global orchestrator instance
orchestrator = MetaOrchestrator()

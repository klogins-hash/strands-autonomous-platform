"""
Agent Persistence and Learning System

Automatically saves successful agents and tools, learns from executions,
and provides recommendations for future tasks.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

import numpy as np
from sqlalchemy import select, update
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from ..core.config import settings
from ..core.database import get_db_session
from ..models.database import AgentTemplate, Tool, Task, AgentInstance
from ..models.schemas import AgentRole


@dataclass
class AgentPerformance:
    """Performance metrics for an agent"""
    agent_id: str
    role: AgentRole
    success_rate: float
    average_execution_time: float
    quality_score: float
    usage_count: int
    last_used: datetime
    error_patterns: List[str]


@dataclass
class ToolPerformance:
    """Performance metrics for a tool"""
    tool_id: str
    name: str
    success_rate: float
    usage_count: int
    average_execution_time: float
    reliability_score: float
    contexts_used: List[str]


class AgentPersistenceSystem:
    """Manages saving, loading, and learning from agents"""
    
    def __init__(self):
        self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self.agent_performance_cache: Dict[str, AgentPerformance] = {}
        self.tool_performance_cache: Dict[str, ToolPerformance] = {}
        
        # Quality thresholds for auto-saving
        self.AGENT_QUALITY_THRESHOLD = 0.8
        self.TOOL_RELIABILITY_THRESHOLD = 0.9
        self.MIN_USAGE_COUNT_AGENT = 3
        self.MIN_USAGE_COUNT_TOOL = 5
    
    async def evaluate_agent_performance(
        self,
        agent_id: str,
        task_id: uuid.UUID,
        execution_result: Dict[str, Any],
        execution_time: float,
        error_count: int = 0
    ) -> AgentPerformance:
        """Evaluate and track agent performance"""
        
        # Calculate metrics
        success = execution_result.get("success", False)
        quality_score = await self._calculate_quality_score(execution_result)
        
        # Get historical data
        historical = await self._get_agent_history(agent_id)
        
        # Update performance metrics
        total_executions = historical.get("usage_count", 0) + 1
        successful_executions = historical.get("successful_executions", 0) + (1 if success else 0)
        success_rate = successful_executions / total_executions
        
        avg_time = (
            (historical.get("total_time", 0) + execution_time) / total_executions
        )
        
        performance = AgentPerformance(
            agent_id=agent_id,
            role=historical.get("role", AgentRole.ORCHESTRATOR),
            success_rate=success_rate,
            average_execution_time=avg_time,
            quality_score=quality_score,
            usage_count=total_executions,
            last_used=datetime.utcnow(),
            error_patterns=historical.get("error_patterns", [])
        )
        
        # Update cache
        self.agent_performance_cache[agent_id] = performance
        
        # Check if agent should be saved
        if await self._should_save_agent(performance):
            await self._save_agent_template(agent_id, performance, execution_result)
        
        return performance
    
    async def evaluate_tool_performance(
        self,
        tool_id: str,
        tool_name: str,
        execution_result: Dict[str, Any],
        execution_time: float,
        context: Dict[str, Any]
    ) -> ToolPerformance:
        """Evaluate and track tool performance"""
        
        success = execution_result.get("success", False)
        reliability_score = await self._calculate_reliability_score(execution_result)
        
        # Get historical data
        historical = await self._get_tool_history(tool_id)
        
        # Update performance metrics
        total_executions = historical.get("usage_count", 0) + 1
        successful_executions = historical.get("successful_executions", 0) + (1 if success else 0)
        success_rate = successful_executions / total_executions
        
        avg_time = (
            (historical.get("total_time", 0) + execution_time) / total_executions
        )
        
        contexts = historical.get("contexts_used", [])
        context_key = json.dumps(context, sort_keys=True)
        if context_key not in contexts:
            contexts.append(context_key)
        
        performance = ToolPerformance(
            tool_id=tool_id,
            name=tool_name,
            success_rate=success_rate,
            usage_count=total_executions,
            average_execution_time=avg_time,
            reliability_score=reliability_score,
            contexts_used=contexts[-10:]  # Keep last 10 contexts
        )
        
        # Update cache
        self.tool_performance_cache[tool_id] = performance
        
        # Check if tool should be saved
        if await self._should_save_tool(performance):
            await self._save_tool_template(tool_id, performance, execution_result)
        
        return performance
    
    async def find_similar_agents(
        self,
        task_description: str,
        required_role: AgentRole,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar successful agents for a given task"""
        
        # Create embedding for task description
        task_embedding = await self._create_embedding(task_description)
        
        # Search for similar agents
        async for session in get_db_session():
            result = await session.execute(
                select(AgentTemplate).where(
                    AgentTemplate.success_rate >= 0.7,
                    AgentTemplate.usage_count >= self.MIN_USAGE_COUNT_AGENT
                ).order_by(
                    AgentTemplate.embedding.cosine_distance(task_embedding)
                ).limit(max_results)
            )
            
            agents = result.scalars().all()
            
            return [
                {
                    "id": str(agent.id),
                    "name": agent.name,
                    "success_rate": agent.success_rate,
                    "usage_count": agent.usage_count,
                    "similarity_score": 1 - agent.embedding.cosine_distance(task_embedding),
                    "created_at": agent.created_at.isoformat()
                }
                for agent in agents
            ]
    
    async def find_similar_tools(
        self,
        requirement: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar tools for a given requirement"""
        
        # Create embedding for requirement
        requirement_embedding = await self._create_embedding(requirement)
        
        # Search for similar tools
        async for session in get_db_session():
            result = await session.execute(
                select(Tool).where(
                    Tool.success_rate >= self.TOOL_RELIABILITY_THRESHOLD,
                    Tool.usage_count >= self.MIN_USAGE_COUNT_TOOL
                ).order_by(
                    Tool.embedding.cosine_distance(requirement_embedding)
                ).limit(max_results)
            )
            
            tools = result.scalars().all()
            
            return [
                {
                    "id": str(tool.id),
                    "name": tool.name,
                    "description": tool.description,
                    "success_rate": tool.success_rate,
                    "usage_count": tool.usage_count,
                    "similarity_score": 1 - tool.embedding.cosine_distance(requirement_embedding),
                    "created_at": tool.created_at.isoformat()
                }
                for tool in tools
            ]
    
    async def get_recommendations(
        self,
        task_description: str,
        required_capabilities: List[str]
    ) -> Dict[str, Any]:
        """Get recommendations for agents and tools"""
        
        # Find similar agents
        agent_recommendations = {}
        for role in AgentRole:
            similar_agents = await self.find_similar_agents(task_description, role)
            if similar_agents:
                agent_recommendations[role.value] = similar_agents
        
        # Find relevant tools
        tool_recommendations = []
        for capability in required_capabilities:
            similar_tools = await self.find_similar_tools(capability)
            tool_recommendations.extend(similar_tools)
        
        # Remove duplicates and sort by relevance
        unique_tools = {tool["id"]: tool for tool in tool_recommendations}.values()
        sorted_tools = sorted(unique_tools, key=lambda x: x["similarity_score"], reverse=True)
        
        return {
            "agents": agent_recommendations,
            "tools": sorted_tools[:10],  # Top 10 tools
            "recommendation_confidence": await self._calculate_recommendation_confidence(
                agent_recommendations, sorted_tools
            )
        }
    
    async def learn_from_execution(
        self,
        task_id: uuid.UUID,
        execution_plan: Dict[str, Any],
        results: Dict[str, Any],
        agent_performances: Dict[str, AgentPerformance],
        tool_performances: Dict[str, ToolPerformance]
    ):
        """Learn from successful task execution"""
        
        # Analyze what made this execution successful
        success_patterns = await self._analyze_success_patterns(
            execution_plan, results, agent_performances, tool_performances
        )
        
        # Update learning database
        await self._update_learning_database(task_id, success_patterns)
        
        # Generate insights for future improvements
        insights = await self._generate_insights(success_patterns)
        
        # Store insights for recommendations
        await self._store_insights(insights)
    
    async def _calculate_quality_score(self, execution_result: Dict[str, Any]) -> float:
        """Calculate quality score for agent execution"""
        
        # Factors that influence quality score
        factors = {
            "completeness": 0.3,
            "accuracy": 0.25,
            "efficiency": 0.2,
            "innovation": 0.15,
            "collaboration": 0.1
        }
        
        scores = {}
        
        # Completeness: Were all required deliverables produced?
        deliverables = execution_result.get("deliverables", [])
        expected_deliverables = execution_result.get("expected_deliverables", [])
        if expected_deliverables:
            completeness = len(deliverables) / len(expected_deliverables)
        else:
            completeness = 1.0 if deliverables else 0.5
        scores["completeness"] = completeness
        
        # Accuracy: Quality of outputs (simplified for now)
        scores["accuracy"] = execution_result.get("accuracy_score", 0.8)
        
        # Efficiency: Time and resource usage
        expected_time = execution_result.get("estimated_time", 300)  # 5 minutes default
        actual_time = execution_result.get("actual_time", 300)
        efficiency = max(0.1, min(1.0, expected_time / actual_time))
        scores["efficiency"] = efficiency
        
        # Innovation: Creative solutions or novel approaches
        scores["innovation"] = execution_result.get("innovation_score", 0.7)
        
        # Collaboration: How well the agent worked with others
        scores["collaboration"] = execution_result.get("collaboration_score", 0.8)
        
        # Calculate weighted score
        quality_score = sum(score * weight for score, weight in zip(
            scores.values(), factors.values()
        ))
        
        return min(1.0, max(0.0, quality_score))
    
    async def _calculate_reliability_score(self, execution_result: Dict[str, Any]) -> float:
        """Calculate reliability score for tool execution"""
        
        # Factors for tool reliability
        factors = {
            "success": 0.4,
            "consistency": 0.3,
            "error_handling": 0.2,
            "performance": 0.1
        }
        
        scores = {}
        
        # Success: Did the tool complete its task?
        scores["success"] = 1.0 if execution_result.get("success", False) else 0.0
        
        # Consistency: Consistent behavior across runs
        scores["consistency"] = execution_result.get("consistency_score", 0.8)
        
        # Error handling: How well errors are handled
        scores["error_handling"] = execution_result.get("error_handling_score", 0.7)
        
        # Performance: Speed and resource efficiency
        scores["performance"] = execution_result.get("performance_score", 0.8)
        
        # Calculate weighted score
        reliability_score = sum(score * weight for score, weight in zip(
            scores.values(), factors.values()
        ))
        
        return min(1.0, max(0.0, reliability_score))
    
    async def _create_embedding(self, text: str) -> np.ndarray:
        """Create embedding for semantic search"""
        try:
            response = await self.openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            print(f"Failed to create embedding: {str(e)}")
            # Return zero embedding as fallback
            return np.zeros(1536)
    
    async def _get_agent_history(self, agent_id: str) -> Dict[str, Any]:
        """Get historical performance data for an agent"""
        if agent_id in self.agent_performance_cache:
            perf = self.agent_performance_cache[agent_id]
            return {
                "usage_count": perf.usage_count,
                "successful_executions": int(perf.success_rate * perf.usage_count),
                "total_time": perf.average_execution_time * perf.usage_count,
                "role": perf.role,
                "error_patterns": perf.error_patterns
            }
        
        # Query database for historical data
        async for session in get_db_session():
            result = await session.execute(
                select(AgentTemplate).where(AgentTemplate.name == agent_id)
            )
            agent = result.scalar_one_or_none()
            
            if agent:
                return {
                    "usage_count": agent.usage_count,
                    "successful_executions": int(agent.success_rate * agent.usage_count),
                    "total_time": 0,  # Not stored in current schema
                    "role": AgentRole.ORCHESTRATOR,  # Default
                    "error_patterns": []
                }
        
        return {
            "usage_count": 0,
            "successful_executions": 0,
            "total_time": 0,
            "role": AgentRole.ORCHESTRATOR,
            "error_patterns": []
        }
    
    async def _get_tool_history(self, tool_id: str) -> Dict[str, Any]:
        """Get historical performance data for a tool"""
        if tool_id in self.tool_performance_cache:
            perf = self.tool_performance_cache[tool_id]
            return {
                "usage_count": perf.usage_count,
                "successful_executions": int(perf.success_rate * perf.usage_count),
                "total_time": perf.average_execution_time * perf.usage_count,
                "contexts_used": perf.contexts_used
            }
        
        # Query database for historical data
        async for session in get_db_session():
            result = await session.execute(
                select(Tool).where(Tool.name == tool_id)
            )
            tool = result.scalar_one_or_none()
            
            if tool:
                return {
                    "usage_count": tool.usage_count,
                    "successful_executions": int(tool.success_rate * tool.usage_count),
                    "total_time": 0,  # Not stored in current schema
                    "contexts_used": []
                }
        
        return {
            "usage_count": 0,
            "successful_executions": 0,
            "total_time": 0,
            "contexts_used": []
        }
    
    async def _should_save_agent(self, performance: AgentPerformance) -> bool:
        """Determine if an agent should be saved based on performance"""
        return (
            performance.quality_score >= self.AGENT_QUALITY_THRESHOLD and
            performance.usage_count >= self.MIN_USAGE_COUNT_AGENT and
            performance.success_rate >= 0.7
        )
    
    async def _should_save_tool(self, performance: ToolPerformance) -> bool:
        """Determine if a tool should be saved based on performance"""
        return (
            performance.reliability_score >= self.TOOL_RELIABILITY_THRESHOLD and
            performance.usage_count >= self.MIN_USAGE_COUNT_TOOL and
            performance.success_rate >= 0.9
        )
    
    async def _save_agent_template(
        self,
        agent_id: str,
        performance: AgentPerformance,
        execution_result: Dict[str, Any]
    ):
        """Save successful agent template to database"""
        
        # Get agent code and configuration
        agent_code = execution_result.get("agent_code", "")
        system_prompt = execution_result.get("system_prompt", "")
        
        # Create embedding for search
        embedding = await self._create_embedding(
            f"{performance.role.value} {system_prompt} {agent_code[:500]}"
        )
        
        async for session in get_db_session():
            # Check if agent already exists
            result = await session.execute(
                select(AgentTemplate).where(AgentTemplate.name == agent_id)
            )
            existing_agent = result.scalar_one_or_none()
            
            if existing_agent:
                # Update existing agent
                await session.execute(
                    update(AgentTemplate).where(AgentTemplate.id == existing_agent.id).values(
                        success_rate=performance.success_rate,
                        usage_count=performance.usage_count,
                        embedding=embedding.tolist()
                    )
                )
            else:
                # Create new agent template
                new_agent = AgentTemplate(
                    name=agent_id,
                    code=agent_code,
                    success_rate=performance.success_rate,
                    usage_count=performance.usage_count,
                    embedding=embedding.tolist()
                )
                session.add(new_agent)
            
            await session.commit()
    
    async def _save_tool_template(
        self,
        tool_id: str,
        performance: ToolPerformance,
        execution_result: Dict[str, Any]
    ):
        """Save successful tool template to database"""
        
        # Get tool code and description
        tool_code = execution_result.get("tool_code", "")
        description = execution_result.get("tool_description", "")
        
        # Create embedding for search
        embedding = await self._create_embedding(
            f"{performance.name} {description} {tool_code[:500]}"
        )
        
        async for session in get_db_session():
            # Check if tool already exists
            result = await session.execute(
                select(Tool).where(Tool.name == tool_id)
            )
            existing_tool = result.scalar_one_or_none()
            
            if existing_tool:
                # Update existing tool
                await session.execute(
                    update(Tool).where(Tool.id == existing_tool.id).values(
                        success_rate=performance.success_rate,
                        usage_count=performance.usage_count,
                        embedding=embedding.tolist()
                    )
                )
            else:
                # Create new tool
                new_tool = Tool(
                    name=performance.name,
                    description=description,
                    code=tool_code,
                    success_rate=performance.success_rate,
                    usage_count=performance.usage_count,
                    embedding=embedding.tolist()
                )
                session.add(new_tool)
            
            await session.commit()
    
    async def _analyze_success_patterns(
        self,
        execution_plan: Dict[str, Any],
        results: Dict[str, Any],
        agent_performances: Dict[str, AgentPerformance],
        tool_performances: Dict[str, ToolPerformance]
    ) -> Dict[str, Any]:
        """Analyze patterns that led to successful execution"""
        
        # Identify successful agent combinations
        successful_agents = [
            agent_id for agent_id, perf in agent_performances.items()
            if perf.success_rate > 0.8
        ]
        
        # Identify effective tools
        effective_tools = [
            tool_id for tool_id, perf in tool_performances.items()
            if perf.success_rate > 0.9
        ]
        
        # Analyze execution sequence
        phases = execution_plan.get("phases", [])
        execution_sequence = [phase.get("phase_name") for phase in phases]
        
        return {
            "successful_agent_combinations": successful_agents,
            "effective_tools": effective_tools,
            "execution_sequence": execution_sequence,
            "total_execution_time": results.get("execution_time", 0),
            "quality_metrics": {
                "overall_quality": np.mean([perf.quality_score for perf in agent_performances.values()]),
                "agent_collaboration": results.get("collaboration_score", 0.8),
                "task_completion": results.get("completion_rate", 1.0)
            }
        }
    
    async def _generate_insights(self, success_patterns: Dict[str, Any]) -> List[str]:
        """Generate insights from success patterns using AI"""
        
        prompt = f"""
        Analyze these success patterns and generate key insights:
        
        {json.dumps(success_patterns, indent=2)}
        
        Generate 3-5 actionable insights that could help improve future agent team performance.
        Focus on:
        1. Agent collaboration patterns
        2. Tool usage effectiveness
        3. Execution sequence optimizations
        4. Quality improvement opportunities
        
        Return insights as a JSON array of strings.
        """
        
        try:
            response = await self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return json.loads(response.content[0].text)
            
        except Exception as e:
            print(f"Failed to generate insights: {str(e)}")
            return ["Analysis failed to generate insights"]
    
    async def _update_learning_database(self, task_id: uuid.UUID, patterns: Dict[str, Any]):
        """Update learning database with new patterns"""
        # TODO: Implement learning database updates
        # This could involve updating vector embeddings, pattern frequencies, etc.
        pass
    
    async def _store_insights(self, insights: List[str]):
        """Store insights for future recommendations"""
        # TODO: Implement insight storage
        # This could be a separate table or document store
        pass
    
    async def _calculate_recommendation_confidence(
        self,
        agent_recommendations: Dict[str, List[Dict[str, Any]]],
        tool_recommendations: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for recommendations"""
        
        # Factor in number and quality of recommendations
        agent_confidence = 0.0
        if agent_recommendations:
            avg_agent_similarity = np.mean([
                np.mean([agent["similarity_score"] for agent in agents])
                for agents in agent_recommendations.values()
            ])
            agent_confidence = avg_agent_similarity
        
        tool_confidence = 0.0
        if tool_recommendations:
            avg_tool_similarity = np.mean([
                tool["similarity_score"] for tool in tool_recommendations
            ])
            tool_confidence = avg_tool_similarity
        
        # Weight agent recommendations higher
        overall_confidence = (agent_confidence * 0.7 + tool_confidence * 0.3)
        
        return min(1.0, max(0.0, overall_confidence))
    
    async def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard"""
        
        async for session in get_db_session():
            # Get top performing agents
            agents_result = await session.execute(
                select(AgentTemplate).order_by(
                    AgentTemplate.success_rate.desc(),
                    AgentTemplate.usage_count.desc()
                ).limit(10)
            )
            top_agents = agents_result.scalars().all()
            
            # Get top performing tools
            tools_result = await session.execute(
                select(Tool).order_by(
                    Tool.success_rate.desc(),
                    Tool.usage_count.desc()
                ).limit(10)
            )
            top_tools = tools_result.scalars().all()
            
            # Get recent task statistics
            tasks_result = await session.execute(
                select(Task).where(
                    Task.created_at >= datetime.utcnow() - timedelta(days=7)
                )
            )
            recent_tasks = tasks_result.scalars().all()
            
            completed_tasks = [t for t in recent_tasks if t.status == "completed"]
            success_rate = len(completed_tasks) / len(recent_tasks) if recent_tasks else 0
            
            return {
                "top_agents": [
                    {
                        "name": agent.name,
                        "success_rate": agent.success_rate,
                        "usage_count": agent.usage_count
                    }
                    for agent in top_agents
                ],
                "top_tools": [
                    {
                        "name": tool.name,
                        "success_rate": tool.success_rate,
                        "usage_count": tool.usage_count
                    }
                    for tool in top_tools
                ],
                "recent_performance": {
                    "tasks_completed": len(completed_tasks),
                    "total_tasks": len(recent_tasks),
                    "success_rate": success_rate,
                    "average_quality": np.mean([
                        perf.quality_score for perf in self.agent_performance_cache.values()
                    ]) if self.agent_performance_cache else 0.0
                },
                "learning_insights": await self._generate_insights({
                    "recent_success_rate": success_rate,
                    "active_agents": len(self.agent_performance_cache),
                    "active_tools": len(self.tool_performance_cache)
                })
            }
    
    async def cleanup(self):
        """Clean up resources"""
        self.agent_performance_cache.clear()
        self.tool_performance_cache.clear()

"""
Persistence System for Agents

Tracks and stores:
- Created agents and tools
- Execution history
- Learned patterns
- API usage
- Artifacts and outputs
- Cross-session memory
"""

import json
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import pickle

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import (
    AgentInstance, AgentTemplate, Tool, KnowledgeDocument, 
    KnowledgeChunk, ActivityLog, Task, Project
)
from .database import get_db_session
from .storage import StorageManager


class PersistenceManager:
    """Manages persistence of all agent activities and artifacts"""
    
    def __init__(self):
        self.storage = StorageManager()
        self.mem0_enabled = False
        self._init_mem0()
    
    def _init_mem0(self):
        """Initialize Mem0 for graph-based memory"""
        try:
            from mem0 import Memory
            from ..core.config import settings
            
            if hasattr(settings, 'mem0_api_key') and settings.mem0_api_key:
                self.mem0 = Memory(api_key=settings.mem0_api_key)
                self.mem0_enabled = True
        except ImportError:
            self.mem0_enabled = False
    
    async def save_agent_creation(
        self,
        agent_name: str,
        agent_spec: Dict[str, Any],
        task_id: str,
        created_by: str = "system"
    ) -> str:
        """
        Save a newly created agent
        
        Returns:
            Agent ID
        """
        try:
            async for session in get_db_session():
                # Save to database
                template = AgentTemplate(
                    name=agent_name,
                    role=agent_spec.get("role", "custom"),
                    system_prompt=agent_spec.get("system_prompt", ""),
                    tools=agent_spec.get("tools", []),
                    config=agent_spec
                )
                session.add(template)
                await session.commit()
                await session.refresh(template)
                
                # Save to MinIO
                await self.storage.upload_json(
                    f"agents/{agent_name}.json",
                    agent_spec
                )
                
                # Save to Mem0 for cross-session memory
                if self.mem0_enabled:
                    self.mem0.add(
                        f"Created agent: {agent_name} with role {agent_spec.get('role')}",
                        user_id=created_by,
                        metadata={
                            "type": "agent_creation",
                            "agent_name": agent_name,
                            "task_id": task_id
                        }
                    )
                
                return str(template.id)
        except Exception as e:
            print(f"Warning: Could not save agent creation: {e}")
            return agent_name
    
    async def save_tool_creation(
        self,
        tool_name: str,
        tool_spec: Dict[str, Any],
        task_id: str,
        created_by: str = "system"
    ) -> str:
        """
        Save a newly created tool
        
        Returns:
            Tool ID
        """
        try:
            async for session in get_db_session():
                # Save to database
                tool = Tool(
                    name=tool_name,
                    description=tool_spec.get("description", ""),
                    parameters=tool_spec.get("parameters", {}),
                    implementation=tool_spec.get("implementation", "")
                )
                session.add(tool)
                await session.commit()
                await session.refresh(tool)
                
                # Save to MinIO
                await self.storage.upload_json(
                    f"tools/{tool_name}.json",
                    tool_spec
                )
                
                # Save to Mem0
                if self.mem0_enabled:
                    self.mem0.add(
                        f"Created tool: {tool_name} - {tool_spec.get('description')}",
                        user_id=created_by,
                        metadata={
                            "type": "tool_creation",
                            "tool_name": tool_name,
                            "task_id": task_id
                        }
                    )
                
                return str(tool.id)
        except Exception as e:
            print(f"Warning: Could not save tool creation: {e}")
            return tool_name
    
    async def save_execution_result(
        self,
        task_id: str,
        phase_name: str,
        result: Dict[str, Any],
        artifacts: Optional[List[str]] = None
    ):
        """Save execution results and artifacts"""
        try:
            # Save result to MinIO
            result_path = f"results/{task_id}/{phase_name}.json"
            await self.storage.upload_json(result_path, result)
            
            # Save artifacts
            if artifacts:
                for artifact in artifacts:
                    artifact_path = f"artifacts/{task_id}/{Path(artifact).name}"
                    await self.storage.upload_file(artifact, artifact_path)
            
            # Log to database
            async for session in get_db_session():
                activity = ActivityLog(
                    task_id=task_id,
                    activity_type="phase_complete",
                    message=f"Completed {phase_name}",
                    details=result
                )
                session.add(activity)
                await session.commit()
            
            # Save to Mem0 for learning
            if self.mem0_enabled:
                self.mem0.add(
                    f"Successfully completed {phase_name}: {result.get('summary', '')}",
                    user_id=task_id,
                    metadata={
                        "type": "execution_result",
                        "phase": phase_name,
                        "status": result.get("status", "completed")
                    }
                )
        except Exception as e:
            print(f"Warning: Could not save execution result: {e}")
    
    async def save_learned_pattern(
        self,
        pattern_name: str,
        pattern_data: Dict[str, Any],
        success_rate: float,
        use_count: int = 1
    ):
        """Save a learned pattern for future reuse"""
        try:
            # Save to MinIO
            pattern_path = f"patterns/{pattern_name}.json"
            pattern_with_meta = {
                **pattern_data,
                "success_rate": success_rate,
                "use_count": use_count,
                "last_used": datetime.utcnow().isoformat()
            }
            await self.storage.upload_json(pattern_path, pattern_with_meta)
            
            # Save to Mem0
            if self.mem0_enabled:
                self.mem0.add(
                    f"Learned pattern: {pattern_name} with {success_rate*100}% success rate",
                    user_id="system",
                    metadata={
                        "type": "learned_pattern",
                        "pattern_name": pattern_name,
                        "success_rate": success_rate
                    }
                )
        except Exception as e:
            print(f"Warning: Could not save learned pattern: {e}")
    
    async def get_agent_by_name(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a previously created agent"""
        try:
            # Try MinIO first (faster)
            agent_spec = await self.storage.download_json(f"agents/{agent_name}.json")
            if agent_spec:
                return agent_spec
            
            # Fallback to database
            async for session in get_db_session():
                result = await session.execute(
                    select(AgentTemplate).where(AgentTemplate.name == agent_name)
                )
                template = result.scalar_one_or_none()
                if template:
                    return {
                        "name": template.name,
                        "role": template.role,
                        "system_prompt": template.system_prompt,
                        "tools": template.tools,
                        "config": template.config
                    }
        except Exception as e:
            print(f"Warning: Could not retrieve agent: {e}")
        
        return None
    
    async def get_tool_by_name(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a previously created tool"""
        try:
            # Try MinIO first
            tool_spec = await self.storage.download_json(f"tools/{tool_name}.json")
            if tool_spec:
                return tool_spec
            
            # Fallback to database
            async for session in get_db_session():
                result = await session.execute(
                    select(Tool).where(Tool.name == tool_name)
                )
                tool = result.scalar_one_or_none()
                if tool:
                    return {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                        "implementation": tool.implementation
                    }
        except Exception as e:
            print(f"Warning: Could not retrieve tool: {e}")
        
        return None
    
    async def get_learned_patterns(self, min_success_rate: float = 0.7) -> List[Dict[str, Any]]:
        """Get all learned patterns above a success threshold"""
        try:
            patterns = []
            pattern_files = await self.storage.list_files("patterns/")
            
            for file_path in pattern_files:
                pattern = await self.storage.download_json(file_path)
                if pattern and pattern.get("success_rate", 0) >= min_success_rate:
                    patterns.append(pattern)
            
            # Sort by success rate and use count
            patterns.sort(
                key=lambda p: (p.get("success_rate", 0), p.get("use_count", 0)),
                reverse=True
            )
            
            return patterns
        except Exception as e:
            print(f"Warning: Could not retrieve learned patterns: {e}")
            return []
    
    async def search_memory(self, query: str, user_id: str = "system", limit: int = 5) -> List[Dict[str, Any]]:
        """Search cross-session memory using Mem0"""
        if not self.mem0_enabled:
            return []
        
        try:
            results = self.mem0.search(query, user_id=user_id, limit=limit)
            return results
        except Exception as e:
            print(f"Warning: Could not search memory: {e}")
            return []
    
    async def get_task_history(self, task_id: str) -> Dict[str, Any]:
        """Get complete history of a task"""
        try:
            history = {
                "task_id": task_id,
                "results": [],
                "artifacts": [],
                "activities": []
            }
            
            # Get results from MinIO
            result_files = await self.storage.list_files(f"results/{task_id}/")
            for file_path in result_files:
                result = await self.storage.download_json(file_path)
                if result:
                    history["results"].append(result)
            
            # Get artifacts
            artifact_files = await self.storage.list_files(f"artifacts/{task_id}/")
            history["artifacts"] = artifact_files
            
            # Get activities from database
            async for session in get_db_session():
                result = await session.execute(
                    select(ActivityLog)
                    .where(ActivityLog.task_id == task_id)
                    .order_by(ActivityLog.timestamp)
                )
                activities = result.scalars().all()
                history["activities"] = [
                    {
                        "type": a.activity_type,
                        "message": a.message,
                        "timestamp": a.timestamp.isoformat(),
                        "details": a.details
                    }
                    for a in activities
                ]
            
            return history
        except Exception as e:
            print(f"Warning: Could not retrieve task history: {e}")
            return {"task_id": task_id, "error": str(e)}
    
    async def save_api_usage(
        self,
        service: str,
        endpoint: str,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None,
        task_id: Optional[str] = None
    ):
        """Track API usage for cost monitoring"""
        try:
            usage_data = {
                "service": service,
                "endpoint": endpoint,
                "tokens_used": tokens_used,
                "cost": cost,
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Append to daily usage file
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            usage_path = f"usage/{date_str}.jsonl"
            
            # Note: This is a simplified version. In production, use proper append
            existing = await self.storage.download_json(usage_path) or []
            existing.append(usage_data)
            await self.storage.upload_json(usage_path, existing)
            
        except Exception as e:
            print(f"Warning: Could not save API usage: {e}")
    
    async def get_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get API usage statistics"""
        try:
            stats = {
                "total_tokens": 0,
                "total_cost": 0.0,
                "by_service": {},
                "by_day": {}
            }
            
            from datetime import timedelta
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            for i in range(days):
                date = start_date + timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                usage_path = f"usage/{date_str}.jsonl"
                
                usage_data = await self.storage.download_json(usage_path)
                if usage_data:
                    for entry in usage_data:
                        service = entry.get("service", "unknown")
                        tokens = entry.get("tokens_used", 0) or 0
                        cost = entry.get("cost", 0.0) or 0.0
                        
                        stats["total_tokens"] += tokens
                        stats["total_cost"] += cost
                        
                        if service not in stats["by_service"]:
                            stats["by_service"][service] = {"tokens": 0, "cost": 0.0}
                        
                        stats["by_service"][service]["tokens"] += tokens
                        stats["by_service"][service]["cost"] += cost
                        
                        if date_str not in stats["by_day"]:
                            stats["by_day"][date_str] = {"tokens": 0, "cost": 0.0}
                        
                        stats["by_day"][date_str]["tokens"] += tokens
                        stats["by_day"][date_str]["cost"] += cost
            
            return stats
        except Exception as e:
            print(f"Warning: Could not get usage stats: {e}")
            return {}


# Global persistence manager
persistence = PersistenceManager()

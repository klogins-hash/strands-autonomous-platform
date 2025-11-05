from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    DONE = "done"
    ERROR = "error"


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    CODE = "code"
    WRITER = "writer"
    DESIGNER = "designer"
    ANALYST = "analyst"
    QA = "qa"
    TOOL_BUILDER = "tool_builder"


class TaskCreate(BaseModel):
    description: str = Field(..., description="Natural language description of the task")
    project_id: uuid.UUID


class TaskResponse(BaseModel):
    id: uuid.UUID
    description: str
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime]
    execution_plan: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    project_id: uuid.UUID
    
    class Config:
        from_attributes = True


class AgentSpec(BaseModel):
    role: AgentRole
    name: str
    system_prompt: str
    tools: List[str] = []
    capabilities: List[str] = []


class ExecutionPlan(BaseModel):
    phases: List[Dict[str, Any]]
    agents: List[AgentSpec]
    estimated_duration: int
    dependencies: List[Dict[str, str]]


class AgentInstance(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    role: AgentRole
    status: AgentStatus
    e2b_sandbox_id: Optional[str]
    created_at: datetime
    progress: float = 0.0
    
    class Config:
        from_attributes = True


class ToolCreate(BaseModel):
    name: str
    description: str
    code: str
    parameters: Dict[str, Any]


class ToolResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    code: str
    success_rate: float
    usage_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActivityLog(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    agent_id: Optional[uuid.UUID]
    activity_type: str
    message: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class KnowledgeDocument(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    filename: str
    s3_key: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str]


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

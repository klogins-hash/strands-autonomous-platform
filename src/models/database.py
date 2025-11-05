from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from pgvector.sqlalchemy import Vector

from ..core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    execution_plan = Column(JSON)
    result = Column(JSON)
    
    project = relationship("Project", back_populates="tasks")
    agents = relationship("AgentInstance", back_populates="task", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="task", cascade="all, delete-orphan")


class AgentInstance(Base):
    __tablename__ = "agent_instances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    role = Column(String(100), nullable=False)
    status = Column(String(50), default="idle")
    e2b_sandbox_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(Float, default=0.0)
    
    task = relationship("Task", back_populates="agents")


class AgentTemplate(Base):
    __tablename__ = "agent_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    code = Column(Text)
    s3_key = Column(String(500))
    success_rate = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    embedding = Column(Vector(1536))
    created_at = Column(DateTime, default=datetime.utcnow)


class Tool(Base):
    __tablename__ = "tools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    description = Column(Text)
    code = Column(Text)
    s3_key = Column(String(500))
    success_rate = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    embedding = Column(Vector(1536))
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255))
    s3_key = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="knowledge_documents")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id"), nullable=False)
    chunk_text = Column(Text)
    chunk_index = Column(Integer)
    embedding = Column(Vector(1536))
    chunk_metadata = Column(JSON)


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    agent_id = Column(UUID(as_uuid=True))
    activity_type = Column(String(100))
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    activity_metadata = Column(JSON)
    
    task = relationship("Task", back_populates="activities")

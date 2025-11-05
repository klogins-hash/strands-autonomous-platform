"""
Multi-Agent Coordination and Messaging System

Enables agents to communicate, share data, and coordinate their actions
through Redis pub/sub and shared state management.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as redis
from ..core.config import settings
from ..models.schemas import AgentRole


class MessageType(str, Enum):
    AGENT_TO_AGENT = "agent_to_agent"
    BROADCAST = "broadcast"
    STATUS_UPDATE = "status_update"
    DATA_SHARE = "data_share"
    REQUEST_HELP = "request_help"
    OFFER_HELP = "offer_help"
    TASK_DELEGATION = "task_delegation"
    COORDINATION = "coordination"


@dataclass
class Message:
    """Message structure for agent communication"""
    id: str
    sender_id: str
    sender_role: AgentRole
    recipient_id: Optional[str]
    recipient_role: Optional[AgentRole]
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=low, 5=high
    reply_to: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_role": self.sender_role.value,
            "recipient_id": self.recipient_id,
            "recipient_role": self.recipient_role.value if self.recipient_role else None,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority,
            "reply_to": self.reply_to
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(
            id=data["id"],
            sender_id=data["sender_id"],
            sender_role=AgentRole(data["sender_role"]),
            recipient_id=data.get("recipient_id"),
            recipient_role=AgentRole(data["recipient_role"]) if data.get("recipient_role") else None,
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            priority=data.get("priority", 1),
            reply_to=data.get("reply_to")
        )


class AgentMessagingSystem:
    """Handles messaging between agents in a task"""
    
    def __init__(self, task_id: uuid.UUID):
        self.task_id = str(task_id)
        self.redis_client: Optional[redis.Redis] = None
        self.message_handlers: Dict[str, Callable] = {}
        self.agent_channels: Dict[str, str] = {}
        self.is_listening = False
        
    async def initialize(self):
        """Initialize Redis connection and channels"""
        self.redis_client = redis.from_url(settings.redis_url)
        
        # Create task-specific channels
        self.broadcast_channel = f"task:{self.task_id}:broadcast"
        self.coordination_channel = f"task:{self.task_id}:coordination"
        
        # Start listening for messages
        await self.start_listening()
    
    async def register_agent(self, agent_id: str, agent_role: AgentRole) -> str:
        """
        Register an agent to receive messages
        
        Args:
            agent_id: Unique agent identifier
            agent_role: Role of the agent
            
        Returns:
            Channel name for this agent
        """
        channel_name = f"task:{self.task_id}:agent:{agent_id}"
        self.agent_channels[agent_id] = channel_name
        
        # Subscribe agent to their personal channel and task channels
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(channel_name, self.broadcast_channel, self.coordination_channel)
        
        return channel_name
    
    async def send_message(
        self,
        sender_id: str,
        sender_role: AgentRole,
        recipient_id: Optional[str] = None,
        recipient_role: Optional[AgentRole] = None,
        message_type: MessageType = MessageType.AGENT_TO_AGENT,
        content: Dict[str, Any] = None,
        priority: int = 1,
        reply_to: Optional[str] = None
    ) -> str:
        """
        Send a message from one agent to another or broadcast to all
        
        Args:
            sender_id: ID of the sending agent
            sender_role: Role of the sending agent
            recipient_id: ID of the specific recipient (optional)
            recipient_role: Role filter for recipients (optional)
            message_type: Type of message being sent
            content: Message content/payload
            priority: Message priority (1-5)
            reply_to: ID of message this is replying to
            
        Returns:
            Message ID
        """
        message = Message(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            sender_role=sender_role,
            recipient_id=recipient_id,
            recipient_role=recipient_role,
            message_type=message_type,
            content=content or {},
            timestamp=datetime.utcnow(),
            priority=priority,
            reply_to=reply_to
        )
        
        # Determine channel(s) to publish to
        channels = []
        
        if recipient_id:
            # Direct message to specific agent
            channel = f"task:{self.task_id}:agent:{recipient_id}"
            channels.append(channel)
        elif recipient_role:
            # Message to all agents of a specific role
            for agent_id, channel in self.agent_channels.items():
                # TODO: Check agent role from database
                channels.append(channel)
        else:
            # Broadcast to all agents
            channels.append(self.broadcast_channel)
        
        # Publish message to all determined channels
        message_data = json.dumps(message.to_dict())
        for channel in channels:
            await self.redis_client.publish(channel, message_data)
        
        # Store message in history
        await self._store_message(message)
        
        return message.id
    
    async def broadcast_status_update(
        self,
        agent_id: str,
        agent_role: AgentRole,
        status: str,
        progress: float = None,
        current_task: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Broadcast status update to all agents"""
        content = {
            "status": status,
            "progress": progress,
            "current_task": current_task,
            "metadata": metadata or {}
        }
        
        await self.send_message(
            sender_id=agent_id,
            sender_role=agent_role,
            message_type=MessageType.STATUS_UPDATE,
            content=content
        )
    
    async def request_help(
        self,
        agent_id: str,
        agent_role: AgentRole,
        problem_description: str,
        required_skills: List[str] = None,
        urgency: str = "normal"
    ) -> str:
        """Request help from other agents"""
        content = {
            "problem_description": problem_description,
            "required_skills": required_skills or [],
            "urgency": urgency,
            "context": {}
        }
        
        return await self.send_message(
            sender_id=agent_id,
            sender_role=agent_role,
            message_type=MessageType.REQUEST_HELP,
            content=content,
            priority=3 if urgency == "high" else 1
        )
    
    async def offer_help(
        self,
        agent_id: str,
        agent_role: AgentRole,
        help_request_id: str,
        how_can_help: str,
        estimated_time: int = None
    ):
        """Offer help to another agent"""
        content = {
            "help_request_id": help_request_id,
            "how_can_help": how_can_help,
            "estimated_time": estimated_time,
            "capabilities": []
        }
        
        await self.send_message(
            sender_id=agent_id,
            sender_role=agent_role,
            message_type=MessageType.OFFER_HELP,
            content=content,
            reply_to=help_request_id
        )
    
    async def share_data(
        self,
        agent_id: str,
        agent_role: AgentRole,
        data: Dict[str, Any],
        data_type: str,
        recipient_id: Optional[str] = None
    ):
        """Share data with other agents"""
        content = {
            "data": data,
            "data_type": data_type,
            "description": f"Shared {data_type} data"
        }
        
        await self.send_message(
            sender_id=agent_id,
            sender_role=agent_role,
            recipient_id=recipient_id,
            message_type=MessageType.DATA_SHARE,
            content=content
        )
    
    async def delegate_task(
        self,
        agent_id: str,
        agent_role: AgentRole,
        task_description: str,
        recipient_role: AgentRole,
        requirements: Dict[str, Any] = None,
        deadline: datetime = None
    ) -> str:
        """Delegate a task to another agent"""
        content = {
            "task_description": task_description,
            "requirements": requirements or {},
            "deadline": deadline.isoformat() if deadline else None,
            "priority": "normal"
        }
        
        return await self.send_message(
            sender_id=agent_id,
            sender_role=agent_role,
            recipient_role=recipient_role,
            message_type=MessageType.TASK_DELEGATION,
            content=content,
            priority=2
        )
    
    async def coordinate_action(
        self,
        agent_id: str,
        agent_role: AgentRole,
        coordination_type: str,
        participants: List[str],
        details: Dict[str, Any]
    ):
        """Coordinate a multi-agent action"""
        content = {
            "coordination_type": coordination_type,
            "participants": participants,
            "details": details,
            "initiator": agent_id
        }
        
        await self.send_message(
            sender_id=agent_id,
            sender_role=agent_role,
            message_type=MessageType.COORDINATION,
            content=content,
            priority=3
        )
    
    async def start_listening(self):
        """Start listening for messages"""
        if self.is_listening:
            return
        
        self.is_listening = True
        
        # Create pubsub for task channels
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(self.broadcast_channel, self.coordination_channel)
        
        # Start background listener
        asyncio.create_task(self._message_listener(pubsub))
    
    async def _message_listener(self, pubsub):
        """Background task to listen for messages"""
        while self.is_listening:
            try:
                message = await pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    await self._handle_received_message(message)
            except Exception as e:
                print(f"Message listener error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _handle_received_message(self, message):
        """Handle a received message"""
        try:
            data = json.loads(message['data'])
            msg = Message.from_dict(data)
            
            # Call appropriate handler based on message type
            handler_key = f"{msg.message_type.value}_{msg.recipient_role or 'all'}"
            if handler_key in self.message_handlers:
                await self.message_handlers[handler_key](msg)
            
            # Log message for monitoring
            await self._log_message(msg)
            
        except Exception as e:
            print(f"Error handling message: {str(e)}")
    
    async def register_handler(self, message_type: MessageType, role: Optional[AgentRole], handler: Callable):
        """Register a handler for specific message types"""
        key = f"{message_type.value}_{role.value if role else 'all'}"
        self.message_handlers[key] = handler
    
    async def get_message_history(
        self,
        agent_id: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 50
    ) -> List[Message]:
        """Get message history for this task"""
        # TODO: Implement message history retrieval from Redis
        return []
    
    async def _store_message(self, message: Message):
        """Store message in Redis for history"""
        key = f"task:{self.task_id}:messages:{message.id}"
        await self.redis_client.setex(
            key,
            timedelta(hours=24),  # Keep messages for 24 hours
            json.dumps(message.to_dict())
        )
    
    async def _log_message(self, message: Message):
        """Log message for monitoring and debugging"""
        log_entry = {
            "task_id": self.task_id,
            "message_id": message.id,
            "sender": f"{message.sender_role.value}:{message.sender_id}",
            "recipient": f"{message.recipient_role}:{message.recipient_id}" if message.recipient_id else "broadcast",
            "type": message.message_type.value,
            "timestamp": message.timestamp.isoformat()
        }
        
        # TODO: Send to logging system
        print(f"Message: {log_entry}")
    
    async def cleanup(self):
        """Clean up resources"""
        self.is_listening = False
        if self.redis_client:
            await self.redis_client.close()


class SharedStateManager:
    """Manages shared state between agents"""
    
    def __init__(self, task_id: uuid.UUID):
        self.task_id = str(task_id)
        self.redis_client: Optional[redis.Redis] = None
        
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(settings.redis_url)
    
    async def set_state(self, key: str, value: Any, agent_id: str = None):
        """Set a shared state value"""
        state_key = f"task:{self.task_id}:state:{key}"
        data = {
            "value": value,
            "set_by": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.redis_client.setex(
            state_key,
            timedelta(hours=2),  # Keep state for 2 hours
            json.dumps(data)
        )
    
    async def get_state(self, key: str) -> Optional[Any]:
        """Get a shared state value"""
        state_key = f"task:{self.task_id}:state:{key}"
        data = await self.redis_client.get(state_key)
        
        if data:
            parsed = json.loads(data)
            return parsed["value"]
        
        return None
    
    async def update_state(self, key: str, update_func: Callable, agent_id: str = None):
        """Update state using a function"""
        current_value = await self.get_state(key)
        new_value = update_func(current_value)
        await self.set_state(key, new_value, agent_id)
    
    async def list_state_keys(self) -> List[str]:
        """List all shared state keys"""
        pattern = f"task:{self.task_id}:state:*"
        keys = await self.redis_client.keys(pattern)
        
        # Extract key names from full Redis keys
        return [key.decode().split(':')[-1] for key in keys]
    
    async def clear_state(self, agent_id: str = None):
        """Clear all state (or only state set by specific agent)"""
        pattern = f"task:{self.task_id}:state:*"
        keys = await self.redis_client.keys(pattern)
        
        for key in keys:
            if agent_id:
                # Check if this state was set by the specified agent
                data = await self.redis_client.get(key)
                if data:
                    parsed = json.loads(data)
                    if parsed.get("set_by") != agent_id:
                        continue
            
            await self.redis_client.delete(key)
    
    async def cleanup(self):
        """Clean up resources"""
        if self.redis_client:
            await self.redis_client.close()


class CoordinationManager:
    """High-level coordination between agents"""
    
    def __init__(self, task_id: uuid.UUID):
        self.task_id = task_id
        self.messaging = AgentMessagingSystem(task_id)
        self.state_manager = SharedStateManager(task_id)
        self.active_coordinations: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize all coordination systems"""
        await self.messaging.initialize()
        await self.state_manager.initialize()
    
    async def orchestrate_handoff(
        self,
        from_agent_id: str,
        from_role: AgentRole,
        to_role: AgentRole,
        handoff_data: Dict[str, Any],
        reason: str
    ) -> str:
        """Orchestrate handoff from one agent to another"""
        coordination_id = str(uuid.uuid4())
        
        # Store coordination info
        self.active_coordinations[coordination_id] = {
            "type": "handoff",
            "from_agent": from_agent_id,
            "from_role": from_role,
            "to_role": to_role,
            "data": handoff_data,
            "reason": reason,
            "status": "initiated",
            "timestamp": datetime.utcnow()
        }
        
        # Broadcast handoff request
        await self.messaging.coordinate_action(
            agent_id=from_agent_id,
            agent_role=from_role,
            coordination_type="handoff",
            participants=[],  # Will be determined by to_role
            details={
                "coordination_id": coordination_id,
                "handoff_data": handoff_data,
                "reason": reason
            }
        )
        
        return coordination_id
    
    async def synchronize_agents(
        self,
        initiator_id: str,
        initiator_role: AgentRole,
        sync_point: str,
        participants: List[str]
    ) -> str:
        """Synchronize multiple agents at a coordination point"""
        coordination_id = str(uuid.uuid4())
        
        # Store synchronization state
        await self.state_manager.set_state(
            f"sync:{sync_point}",
            {
                "coordination_id": coordination_id,
                "participants": participants,
                "waiting_for": participants.copy(),
                "status": "waiting"
            }
        )
        
        # Notify all participants
        for participant_id in participants:
            await self.messaging.send_message(
                sender_id=initiator_id,
                sender_role=initiator_role,
                recipient_id=participant_id,
                message_type=MessageType.COORDINATION,
                content={
                    "coordination_type": "synchronization",
                    "sync_point": sync_point,
                    "coordination_id": coordination_id
                }
            )
        
        return coordination_id
    
    async def wait_for_sync(self, sync_point: str, agent_id: str):
        """Wait for synchronization point"""
        while True:
            sync_state = await self.state_manager.get_state(f"sync:{sync_point}")
            if not sync_state:
                raise Exception(f"Sync point {sync_point} not found")
            
            if agent_id not in sync_state["waiting_for"]:
                # This agent has been released from sync
                return sync_state
            
            await asyncio.sleep(0.5)  # Wait and check again
    
    async def release_from_sync(self, sync_point: str, agent_id: str):
        """Release agent from synchronization point"""
        sync_state = await self.state_manager.get_state(f"sync:{sync_point}")
        if not sync_state:
            return
        
        # Remove agent from waiting list
        waiting_for = sync_state["waiting_for"].copy()
        if agent_id in waiting_for:
            waiting_for.remove(agent_id)
            
            # Update state
            sync_state["waiting_for"] = waiting_for
            sync_state["status"] = "completed" if not waiting_for else "waiting"
            
            await self.state_manager.set_state(f"sync:{sync_point}", sync_state)
    
    async def cleanup(self):
        """Clean up all coordination resources"""
        await self.messaging.cleanup()
        await self.state_manager.cleanup()
        self.active_coordinations.clear()

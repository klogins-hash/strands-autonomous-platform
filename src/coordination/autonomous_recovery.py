"""
Autonomous Troubleshooting and Error Recovery System

When agents encounter errors, this system automatically attempts multiple
recovery strategies before escalating to the user.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from anthropic import AsyncAnthropic
from ..core.config import settings
from ..models.schemas import AgentRole
from .messaging import CoordinationManager
from ..core.database import get_db_session


class ErrorSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(str, Enum):
    RETRY = "retry"
    ALTERNATIVE_APPROACH = "alternative_approach"
    SIMPLIFY_TASK = "simplify_task"
    REQUEST_HELP = "request_help"
    ESCALATE_TO_USER = "escalate_to_user"
    RESTART_AGENT = "restart_agent"
    USE_DIFFERENT_TOOL = "use_different_tool"


@dataclass
class ErrorReport:
    """Structure for reporting errors"""
    error_id: str
    agent_id: str
    agent_role: AgentRole
    task_id: uuid.UUID
    error_message: str
    error_type: str
    severity: ErrorSeverity
    context: Dict[str, Any]
    timestamp: datetime
    recovery_attempts: List[RecoveryStrategy] = None
    resolved: bool = False
    resolution: Optional[str] = None


class AutonomousRecoverySystem:
    """Handles automatic error recovery for agents"""
    
    def __init__(self, coordination_manager: CoordinationManager):
        self.coordination = coordination_manager
        self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.active_errors: Dict[str, ErrorReport] = {}
        self.recovery_handlers: Dict[RecoveryStrategy, Callable] = {}
        self.successful_recoveries: Dict[str, Dict[str, Any]] = {}  # Learning database
        
        # Initialize recovery handlers
        self._initialize_recovery_handlers()
    
    def _initialize_recovery_handlers(self):
        """Set up handlers for different recovery strategies"""
        self.recovery_handlers = {
            RecoveryStrategy.RETRY: self._handle_retry,
            RecoveryStrategy.ALTERNATIVE_APPROACH: self._handle_alternative_approach,
            RecoveryStrategy.SIMPLIFY_TASK: self._handle_simplify_task,
            RecoveryStrategy.REQUEST_HELP: self._handle_request_help,
            RecoveryStrategy.RESTART_AGENT: self._handle_restart_agent,
            RecoveryStrategy.USE_DIFFERENT_TOOL: self._handle_use_different_tool,
            RecoveryStrategy.ESCALATE_TO_USER: self._handle_escalate_to_user
        }
    
    async def report_error(
        self,
        agent_id: str,
        agent_role: AgentRole,
        task_id: uuid.UUID,
        error_message: str,
        error_type: str,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Report an error and trigger autonomous recovery
        
        Args:
            agent_id: ID of the agent encountering the error
            agent_role: Role of the agent
            task_id: ID of the task being executed
            error_message: Human-readable error message
            error_type: Technical error classification
            context: Additional context about the error
            
        Returns:
            Error ID for tracking
        """
        # Create error report
        error_report = ErrorReport(
            error_id=str(uuid.uuid4()),
            agent_id=agent_id,
            agent_role=agent_role,
            task_id=task_id,
            error_message=error_message,
            error_type=error_type,
            severity=await self._classify_error_severity(error_message, error_type),
            context=context or {},
            timestamp=datetime.utcnow(),
            recovery_attempts=[]
        )
        
        # Store error report
        self.active_errors[error_report.error_id] = error_report
        
        # Log error for monitoring
        await self._log_error(error_report)
        
        # Start autonomous recovery process
        asyncio.create_task(self._autonomous_recovery(error_report))
        
        return error_report.error_id
    
    async def _autonomous_recovery(self, error_report: ErrorReport):
        """Execute autonomous recovery strategies"""
        max_attempts = 3
        attempt_count = 0
        
        while attempt_count < max_attempts and not error_report.resolved:
            try:
                # Determine next recovery strategy
                strategy = await self._determine_recovery_strategy(error_report, attempt_count)
                
                if strategy == RecoveryStrategy.ESCALATE_TO_USER:
                    # Don't attempt user escalation automatically
                    break
                
                # Execute recovery strategy
                success = await self._execute_recovery_strategy(error_report, strategy)
                
                if success:
                    error_report.resolved = True
                    error_report.resolution = f"Recovered using {strategy.value}"
                    await self._log_recovery_success(error_report, strategy)
                    break
                else:
                    error_report.recovery_attempts.append(strategy)
                    attempt_count += 1
                    await asyncio.sleep(2 ** attempt_count)  # Exponential backoff
                
            except Exception as e:
                print(f"Recovery attempt failed: {str(e)}")
                attempt_count += 1
                error_report.recovery_attempts.append(RecoveryStrategy.RETRY)  # Default fallback
        
        # If all attempts failed, escalate to user
        if not error_report.resolved:
            await self._escalate_to_user(error_report)
    
    async def _classify_error_severity(self, error_message: str, error_type: str) -> ErrorSeverity:
        """Classify error severity for appropriate response"""
        # Use AI to classify error severity
        prompt = f"""
        Classify the severity of this error:
        
        Error Message: {error_message}
        Error Type: {error_type}
        
        Classify as:
        - LOW: Minor issue, won't significantly impact task completion
        - MEDIUM: Significant issue but task can likely continue
        - HIGH: Major issue that may prevent task completion
        - CRITICAL: Critical error that stops all progress
        
        Return only the severity level (LOW, MEDIUM, HIGH, CRITICAL).
        """
        
        try:
            response = await self.anthropic.messages.create(
                model="claude-haiku-4-5",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )
            
            severity_str = response.content[0].text.strip().upper()
            return ErrorSeverity(severity_str) if severity_str in ErrorSeverity else ErrorSeverity.MEDIUM
            
        except:
            return ErrorSeverity.MEDIUM  # Default classification
    
    async def _determine_recovery_strategy(
        self,
        error_report: ErrorReport,
        attempt_count: int
    ) -> RecoveryStrategy:
        """Determine the best recovery strategy based on error and context"""
        
        # Check for similar past errors
        similar_error = await self._find_similar_error(error_report)
        if similar_error and similar_error.get("successful_strategy"):
            return RecoveryStrategy(similar_error["successful_strategy"])
        
        # Use AI to determine strategy
        prompt = f"""
        Given this error situation, determine the best recovery strategy:
        
        Error: {error_report.error_message}
        Type: {error_report.error_type}
        Severity: {error_report.severity.value}
        Agent Role: {error_report.agent_role.value}
        Attempt Count: {attempt_count}
        Context: {json.dumps(error_report.context, indent=2)}
        
        Available Strategies:
        - RETRY: Try the same action again
        - ALTERNATIVE_APPROACH: Use a different method to achieve the same goal
        - SIMPLIFY_TASK: Break down the task into smaller, simpler steps
        - REQUEST_HELP: Ask other agents for assistance
        - RESTART_AGENT: Restart the agent with fresh state
        - USE_DIFFERENT_TOOL: Try using a different tool or library
        
        Return only the strategy name.
        """
        
        try:
            response = await self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )
            
            strategy_str = response.content[0].text.strip().upper()
            return RecoveryStrategy(strategy_str) if strategy_str in RecoveryStrategy else RecoveryStrategy.RETRY
            
        except:
            return RecoveryStrategy.RETRY  # Default strategy
    
    async def _execute_recovery_strategy(self, error_report: ErrorReport, strategy: RecoveryStrategy) -> bool:
        """Execute a specific recovery strategy"""
        if strategy not in self.recovery_handlers:
            return False
        
        try:
            handler = self.recovery_handlers[strategy]
            return await handler(error_report)
        except Exception as e:
            print(f"Recovery strategy {strategy.value} failed: {str(e)}")
            return False
    
    async def _handle_retry(self, error_report: ErrorReport) -> bool:
        """Handle retry recovery strategy"""
        # Send retry message to the agent
        await self.coordination.messaging.send_message(
            sender_id="recovery_system",
            sender_role=AgentRole.ORCHESTRATOR,
            recipient_id=error_report.agent_id,
            message_type=MessageType.COORDINATION,
            content={
                "action": "retry",
                "error_id": error_report.error_id,
                "retry_count": len(error_report.recovery_attempts) + 1
            }
        )
        
        # Wait a moment to see if retry succeeds
        await asyncio.sleep(5)
        
        # Check if error is resolved (agent would report back)
        updated_error = self.active_errors.get(error_report.error_id)
        return updated_error and updated_error.resolved
    
    async def _handle_alternative_approach(self, error_report: ErrorReport) -> bool:
        """Handle alternative approach recovery strategy"""
        # Generate alternative approach using AI
        prompt = f"""
        An agent encountered this error:
        {error_report.error_message}
        
        Context: {json.dumps(error_report.context, indent=2)}
        
        Suggest an alternative approach to achieve the same goal.
        Be specific and actionable.
        
        Return as JSON with:
        - approach_description: Clear description of the alternative
        - steps: List of specific steps to take
        - tools_needed: Any different tools required
        """
        
        try:
            response = await self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            alternative = json.loads(response.content[0].text)
            
            # Send alternative approach to agent
            await self.coordination.messaging.send_message(
                sender_id="recovery_system",
                sender_role=AgentRole.ORCHESTRATOR,
                recipient_id=error_report.agent_id,
                message_type=MessageType.COORDINATION,
                content={
                    "action": "alternative_approach",
                    "error_id": error_report.error_id,
                    "alternative": alternative
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to generate alternative approach: {str(e)}")
            return False
    
    async def _handle_simplify_task(self, error_report: ErrorReport) -> bool:
        """Handle task simplification recovery strategy"""
        # Break down the current task into simpler steps
        prompt = f"""
        This task failed with error: {error_report.error_message}
        
        Original task context: {json.dumps(error_report.context, indent=2)}
        
        Break this down into 2-3 simpler, more manageable subtasks.
        Each subtask should be easier to accomplish and less error-prone.
        
        Return as JSON array of subtasks with:
        - description: What the subtask accomplishes
        - steps: How to accomplish it
        - dependencies: What it depends on
        """
        
        try:
            response = await self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            subtasks = json.loads(response.content[0].text)
            
            # Send simplified tasks to agent
            await self.coordination.messaging.send_message(
                sender_id="recovery_system",
                sender_role=AgentRole.ORCHESTRATOR,
                recipient_id=error_report.agent_id,
                message_type=MessageType.COORDINATION,
                content={
                    "action": "simplify_task",
                    "error_id": error_report.error_id,
                    "subtasks": subtasks
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to simplify task: {str(e)}")
            return False
    
    async def _handle_request_help(self, error_report: ErrorReport) -> bool:
        """Handle help request recovery strategy"""
        # Determine which agent role would be most helpful
        prompt = f"""
        An agent needs help with this error:
        {error_report.error_message}
        
        Agent Role: {error_report.agent_role.value}
        Context: {json.dumps(error_report.context, indent=2)}
        
        Which other agent role would be most helpful to assist?
        Choose from: RESEARCH, CODE, WRITER, DESIGNER, ANALYST, QA, TOOL_BUILDER
        
        Return only the role name.
        """
        
        try:
            response = await self.anthropic.messages.create(
                model="claude-haiku-4-5",
                max_tokens=20,
                messages=[{"role": "user", "content": prompt}]
            )
            
            helpful_role = response.content[0].text.strip().upper()
            
            # Request help from appropriate agent
            await self.coordination.messaging.request_help(
                agent_id=error_report.agent_id,
                agent_role=error_report.agent_role,
                problem_description=error_report.error_message,
                required_skills=[helpful_role],
                urgency="high" if error_report.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else "normal"
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to request help: {str(e)}")
            return False
    
    async def _handle_restart_agent(self, error_report: ErrorReport) -> bool:
        """Handle agent restart recovery strategy"""
        # Send restart signal to agent
        await self.coordination.messaging.send_message(
            sender_id="recovery_system",
            sender_role=AgentRole.ORCHESTRATOR,
            recipient_id=error_report.agent_id,
            message_type=MessageType.COORDINATION,
            content={
                "action": "restart",
                "error_id": error_report.error_id,
                "preserve_context": True
            }
        )
        
        return True
    
    async def _handle_use_different_tool(self, error_report: ErrorReport) -> bool:
        """Handle using different tool recovery strategy"""
        # Identify alternative tools
        prompt = f"""
        An agent's tool failed with this error:
        {error_report.error_message}
        
        Context: {json.dumps(error_report.context, indent=2)}
        
        Suggest alternative tools or approaches that could accomplish the same goal.
        Consider both built-in alternatives and tools that could be built.
        
        Return as JSON with:
        - alternatives: List of alternative tools/approaches
        - recommendations: Which alternatives are most promising
        - implementation_needed: If any alternatives need to be built
        """
        
        try:
            response = await self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            alternatives = json.loads(response.content[0].text)
            
            # Send alternatives to agent
            await self.coordination.messaging.send_message(
                sender_id="recovery_system",
                sender_role=AgentRole.ORCHESTRATOR,
                recipient_id=error_report.agent_id,
                message_type=MessageType.COORDINATION,
                content={
                    "action": "use_alternative_tool",
                    "error_id": error_report.error_id,
                    "alternatives": alternatives
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to suggest alternative tools: {str(e)}")
            return False
    
    async def _handle_escalate_to_user(self, error_report: ErrorReport) -> bool:
        """Handle escalation to user (manual process)"""
        # This would typically trigger a notification to the user
        # For now, just log the escalation
        await self._log_escalation(error_report)
        return True
    
    async def _find_similar_error(self, error_report: ErrorReport) -> Optional[Dict[str, Any]]:
        """Find similar past errors for learning"""
        # TODO: Implement vector search for similar errors
        # For now, return None
        return None
    
    async def _log_error(self, error_report: ErrorReport):
        """Log error for monitoring"""
        log_entry = {
            "error_id": error_report.error_id,
            "agent_id": error_report.agent_id,
            "agent_role": error_report.agent_role.value,
            "task_id": str(error_report.task_id),
            "error_message": error_report.error_message,
            "error_type": error_report.error_type,
            "severity": error_report.severity.value,
            "timestamp": error_report.timestamp.isoformat()
        }
        
        # TODO: Send to logging system
        print(f"ERROR LOG: {log_entry}")
    
    async def _log_recovery_success(self, error_report: ErrorReport, strategy: RecoveryStrategy):
        """Log successful recovery for learning"""
        success_entry = {
            "error_pattern": error_report.error_type,
            "strategy": strategy.value,
            "agent_role": error_report.agent_role.value,
            "context": error_report.context,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store for future learning
        pattern_key = f"recovery_pattern:{error_report.error_type}:{error_report.agent_role.value}"
        self.successful_recoveries[pattern_key] = success_entry
        
        print(f"RECOVERY SUCCESS: {success_entry}")
    
    async def _log_escalation(self, error_report: ErrorReport):
        """Log escalation to user"""
        escalation_entry = {
            "error_id": error_report.error_id,
            "agent_id": error_report.agent_id,
            "task_id": str(error_report.task_id),
            "error_message": error_report.error_message,
            "attempts_made": len(error_report.recovery_attempts),
            "strategies_tried": [s.value for s in error_report.recovery_attempts],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # TODO: Send notification to user
        print(f"ESCALATION TO USER: {escalation_entry}")
    
    async def get_error_status(self, error_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific error"""
        error_report = self.active_errors.get(error_id)
        if not error_report:
            return None
        
        return {
            "error_id": error_report.error_id,
            "resolved": error_report.resolved,
            "resolution": error_report.resolution,
            "attempts": len(error_report.recovery_attempts),
            "strategies_tried": [s.value for s in error_report.recovery_attempts],
            "severity": error_report.severity.value
        }
    
    async def get_active_errors(self) -> List[Dict[str, Any]]:
        """Get all active errors"""
        return [
            {
                "error_id": error.error_id,
                "agent_id": error.agent_id,
                "agent_role": error.agent_role.value,
                "error_message": error.error_message,
                "severity": error.severity.value,
                "timestamp": error.timestamp.isoformat(),
                "resolved": error.resolved
            }
            for error in self.active_errors.values()
            if not error.resolved
        ]
    
    async def resolve_error(self, error_id: str, resolution: str):
        """Manually resolve an error"""
        if error_id in self.active_errors:
            error_report = self.active_errors[error_id]
            error_report.resolved = True
            error_report.resolution = resolution
            await self._log_recovery_success(error_report, RecoveryStrategy.ESCALATE_TO_USER)
    
    async def cleanup(self):
        """Clean up resources"""
        self.active_errors.clear()
        self.successful_recoveries.clear()

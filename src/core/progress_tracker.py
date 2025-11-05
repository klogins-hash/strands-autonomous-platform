"""
Real-time Progress Tracking System

Provides live updates on agent activity, task progress, and system status.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class ProgressStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class ProgressUpdate:
    """Progress update from an agent or system component"""
    component_id: str
    component_type: str  # "agent", "phase", "task", "system"
    status: ProgressStatus
    progress_percentage: float
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = None


class ProgressTracker:
    """Tracks and displays real-time progress"""
    
    def __init__(self):
        self.updates: List[ProgressUpdate] = []
        self.component_status: Dict[str, ProgressUpdate] = {}
        self.listeners: List[asyncio.Queue] = []
        
    async def update(
        self,
        component_id: str,
        component_type: str,
        status: ProgressStatus,
        progress: float,
        message: str,
        metadata: Dict[str, Any] = None
    ):
        """Record a progress update"""
        update = ProgressUpdate(
            component_id=component_id,
            component_type=component_type,
            status=status,
            progress_percentage=progress,
            message=message,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Store update
        self.updates.append(update)
        self.component_status[component_id] = update
        
        # Display update
        await self._display_update(update)
        
        # Notify listeners (for WebSocket, etc.)
        await self._notify_listeners(update)
    
    async def _display_update(self, update: ProgressUpdate):
        """Display progress update to console"""
        # Status emoji
        emoji_map = {
            ProgressStatus.PENDING: "⏳",
            ProgressStatus.IN_PROGRESS: "🔄",
            ProgressStatus.COMPLETED: "✅",
            ProgressStatus.FAILED: "❌",
            ProgressStatus.PAUSED: "⏸️"
        }
        
        emoji = emoji_map.get(update.status, "📊")
        
        # Progress bar
        bar_length = 20
        filled = int(bar_length * update.progress_percentage / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # Format message
        print(f"{emoji} [{bar}] {update.progress_percentage:5.1f}% | {update.component_type.upper()}: {update.message}")
    
    async def _notify_listeners(self, update: ProgressUpdate):
        """Notify WebSocket listeners of progress"""
        for queue in self.listeners:
            try:
                await queue.put(update)
            except:
                pass
    
    def register_listener(self) -> asyncio.Queue:
        """Register a listener for progress updates"""
        queue = asyncio.Queue()
        self.listeners.append(queue)
        return queue
    
    def get_overall_progress(self) -> float:
        """Calculate overall progress across all components"""
        if not self.component_status:
            return 0.0
        
        total_progress = sum(
            update.progress_percentage 
            for update in self.component_status.values()
        )
        return total_progress / len(self.component_status)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of current status"""
        status_counts = {}
        for update in self.component_status.values():
            status_counts[update.status.value] = status_counts.get(update.status.value, 0) + 1
        
        return {
            "overall_progress": self.get_overall_progress(),
            "total_components": len(self.component_status),
            "status_breakdown": status_counts,
            "active_components": [
                {
                    "id": comp_id,
                    "type": update.component_type,
                    "status": update.status.value,
                    "progress": update.progress_percentage,
                    "message": update.message
                }
                for comp_id, update in self.component_status.items()
                if update.status == ProgressStatus.IN_PROGRESS
            ]
        }
    
    def display_summary(self):
        """Display progress summary"""
        summary = self.get_status_summary()
        
        print("\n" + "=" * 80)
        print("📊 PROGRESS SUMMARY")
        print("=" * 80)
        print(f"Overall Progress: {summary['overall_progress']:.1f}%")
        print(f"Total Components: {summary['total_components']}")
        print(f"\nStatus Breakdown:")
        for status, count in summary['status_breakdown'].items():
            print(f"  {status}: {count}")
        
        if summary['active_components']:
            print(f"\nActive Components ({len(summary['active_components'])}):")
            for comp in summary['active_components']:
                print(f"  • {comp['type']}: {comp['message']} ({comp['progress']:.1f}%)")
        
        print("=" * 80 + "\n")


# Global progress tracker instance
progress_tracker = ProgressTracker()

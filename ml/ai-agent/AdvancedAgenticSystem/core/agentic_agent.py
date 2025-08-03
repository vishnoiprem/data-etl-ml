"""
Advanced Agentic AI Engine
Implements the four-step agentic process: Perceive, Reason, Act, Learn
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .perception_layer import PerceptionLayer
from .reasoning_engine import ReasoningEngine
from .action_executor import ActionExecutor
from .learning_system import LearningSystem
from .ai_models import AIModelManager

@dataclass
class AgenticContext:
    """Context object passed through the agentic pipeline"""
    user_message: str
    intent: str
    entities: Dict[str, Any]
    customer_data: Dict[str, Any]
    confidence: float
    timestamp: datetime
    session_id: str

@dataclass
class ActionPlan:
    """Represents a planned set of actions"""
    actions: List[Dict[str, Any]]
    reasoning: str
    confidence: float
    risk_assessment: Dict[str, Any]
    estimated_time: float

class AgenticAIEngine:
    """
    Main Agentic AI Engine implementing autonomous problem-solving
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize core components
        self.perception = PerceptionLayer(config.get('perception', {}))
        self.reasoning = ReasoningEngine(config.get('reasoning', {}))
        self.executor = ActionExecutor(config.get('executor', {}))
        self.learning = LearningSystem(config.get('learning', {}))
        self.ai_models = AIModelManager(config.get('ai_models', {}))

        # State management
        self.conversation_history = []
        self.knowledge_base = {}
        self.performance_metrics = {
            'total_interactions': 0,
            'success_rate': 1.0,
            'avg_response_time': 0.0,
            'confidence_levels': []
        }

    async def process_request(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """
        Main entry point for processing user requests through the agentic pipeline
        """
        start_time = datetime.now()
        session_id = session_id or f"session_{int(start_time.timestamp())}"

        try:
            # Step 1: Perceive
            self.logger.info(f"[{session_id}] Starting perception phase")
            perception_result = await self.perception.perceive(user_input, session_id)

            # Step 2: Reason
            self.logger.info(f"[{session_id}] Starting reasoning phase")
            reasoning_result = await self.reasoning.reason(perception_result)

            # Step 3: Act
            self.logger.info(f"[{session_id}] Starting action phase")
            action_result = await self.executor.execute(reasoning_result)

            # Step 4: Learn
            self.logger.info(f"[{session_id}] Starting learning phase")
            learning_result = await self.learning.learn({
                'perception': perception_result,
                'reasoning': reasoning_result,
                'action': action_result,
                'session_id': session_id,
                'processing_time': (datetime.now() - start_time).total_seconds()
            })

            # Update metrics
            self._update_metrics(learning_result)

            return {
                'success': True,
                'response': reasoning_result.get('response', ''),
                'confidence': reasoning_result.get('confidence', 0.0),
                'actions_taken': action_result.get('actions_executed', []),
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'session_id': session_id
            }

        except Exception as e:
            self.logger.error(f"[{session_id}] Error in agentic pipeline: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': 'I apologize, but I encountered an error processing your request.',
                'session_id': session_id
            }

    def _update_metrics(self, learning_result: Dict[str, Any]):
        """Update performance metrics based on learning results"""
        self.performance_metrics['total_interactions'] += 1

        if learning_result.get('success', False):
            current_success = (self.performance_metrics['success_rate'] *
                             (self.performance_metrics['total_interactions'] - 1) + 1)
            self.performance_metrics['success_rate'] = (
                current_success / self.performance_metrics['total_interactions']
            )

        # Update confidence tracking
        confidence = learning_result.get('confidence', 0.0)
        self.performance_metrics['confidence_levels'].append(confidence)

        # Keep only last 100 confidence measurements
        if len(self.performance_metrics['confidence_levels']) > 100:
            self.performance_metrics['confidence_levels'] = (
                self.performance_metrics['confidence_levels'][-100:]
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        confidence_levels = self.performance_metrics['confidence_levels']
        avg_confidence = sum(confidence_levels) / len(confidence_levels) if confidence_levels else 0.0

        return {
            'total_interactions': self.performance_metrics['total_interactions'],
            'success_rate': self.performance_metrics['success_rate'],
            'avg_confidence': avg_confidence,
            'active_models': self.ai_models.get_active_models(),
            'knowledge_base_size': len(self.knowledge_base)
        }
"""
AI Model Manager for handling multiple AI model integrations
"""

import asyncio
import openai
from anthropic import Anthropic
import google.generativeai as genai
from typing import Dict, List, Any, Optional
import logging

class AIModelManager:
    """
    Manages multiple AI models and intelligent model selection
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.active_models = []
        self.model_performance = {}

        self._initialize_models()

    def _initialize_models(self):
        """Initialize available AI models"""

        # OpenAI GPT models
        if self.config.get('openai', {}).get('enabled', False):
            try:
                openai.api_key = self.config['openai']['api_key']
                self.models['gpt-4'] = {
                    'client': openai,
                    'type': 'openai',
                    'capabilities': ['text', 'reasoning', 'analysis'],
                    'cost_per_token': 0.00003
                }
                self.active_models.append('gpt-4')
                self.logger.info("OpenAI GPT-4 initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI: {e}")

        # Anthropic Claude
        if self.config.get('anthropic', {}).get('enabled', False):
            try:
                self.models['claude-3.5'] = {
                    'client': Anthropic(api_key=self.config['anthropic']['api_key']),
                    'type': 'anthropic',
                    'capabilities': ['text', 'reasoning', 'analysis', 'safety'],
                    'cost_per_token': 0.000015
                }
                self.active_models.append('claude-3.5')
                self.logger.info("Anthropic Claude initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Claude: {e}")

        # Google Gemini
        if self.config.get('google', {}).get('enabled', False):
            try:
                genai.configure(api_key=self.config['google']['api_key'])
                self.models['gemini-pro'] = {
                    'client': genai,
                    'type': 'google',
                    'capabilities': ['text', 'multimodal', 'fast'],
                    'cost_per_token': 0.000001
                }
                self.active_models.append('gemini-pro')
                self.logger.info("Google Gemini initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini: {e}")

        # Local models (if configured)
        if self.config.get('local', {}).get('enabled', False):
            self._initialize_local_models()

    def _initialize_local_models(self):
        """Initialize local AI models"""
        try:
            # Add local model implementations here
            # e.g., Ollama, local transformers, etc.
            self.models['local-llama'] = {
                'client': None,  # Local model client
                'type': 'local',
                'capabilities': ['text', 'fast', 'private'],
                'cost_per_token': 0.0
            }
            self.logger.info("Local models initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize local models: {e}")

    async def call_model(self, model_name: str, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call a specific AI model with the given prompt
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not available")

        model_info = self.models[model_name]
        start_time = asyncio.get_event_loop().time()

        try:
            if model_info['type'] == 'openai':
                response = await self._call_openai(model_name, prompt, context)
            elif model_info['type'] == 'anthropic':
                response = await self._call_anthropic(model_name, prompt, context)
            elif model_info['type'] == 'google':
                response = await self._call_google(model_name, prompt, context)
            elif model_info['type'] == 'local':
                response = await self._call_local(model_name, prompt, context)
            else:
                raise ValueError(f"Unknown model type: {model_info['type']}")

            # Track performance
            response_time = asyncio.get_event_loop().time() - start_time
            self._update_model_performance(model_name, response_time, True)

            return {
                'success': True,
                'response': response,
                'model': model_name,
                'response_time': response_time
            }

        except Exception as e:
            self.logger.error(f"Error calling {model_name}: {e}")
            self._update_model_performance(model_name, 0, False)
            return {
                'success': False,
                'error': str(e),
                'model': model_name
            }

    async def _call_openai(self, model_name: str, prompt: str, context: Dict[str, Any]) -> str:
        """Call OpenAI model"""
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an advanced AI assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content

    async def _call_anthropic(self, model_name: str, prompt: str, context: Dict[str, Any]) -> str:
        """Call Anthropic Claude"""
        client = self.models[model_name]['client']
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    async def _call_google(self, model_name: str, prompt: str, context: Dict[str, Any]) -> str:
        """Call Google Gemini"""
        model = genai.GenerativeModel('gemini-pro')
        response = await model.generate_content_async(prompt)
        return response.text

    async def _call_local(self, model_name: str, prompt: str, context: Dict[str, Any]) -> str:
        """Call local model"""
        # Implement local model calling logic
        # This would depend on your local model setup (Ollama, etc.)
        return "Local model response placeholder"

    def select_best_model(self, task_type: str, complexity: float) -> str:
        """
        Intelligently select the best model for a given task
        """
        if not self.active_models:
            raise ValueError("No models available")

        # Simple selection logic (can be enhanced with ML)
        if complexity > 0.8 and 'gpt-4' in self.active_models:
            return 'gpt-4'
        elif task_type == 'safety' and 'claude-3.5' in self.active_models:
            return 'claude-3.5'
        elif complexity < 0.5 and 'gemini-pro' in self.active_models:
            return 'gemini-pro'
        else:
            return self.active_models[0]

    def _update_model_performance(self, model_name: str, response_time: float, success: bool):
        """Update model performance metrics"""
        if model_name not in self.model_performance:
            self.model_performance[model_name] = {
                'total_calls': 0,
                'successful_calls': 0,
                'avg_response_time': 0.0,
                'success_rate': 0.0
            }

        perf = self.model_performance[model_name]
        perf['total_calls'] += 1

        if success:
            perf['successful_calls'] += 1
            # Update average response time
            perf['avg_response_time'] = (
                (perf['avg_response_time'] * (perf['successful_calls'] - 1) + response_time) /
                perf['successful_calls']
            )

        perf['success_rate'] = perf['successful_calls'] / perf['total_calls']

    def get_active_models(self) -> List[str]:
        """Get list of active models"""
        return self.active_models.copy()

    def get_model_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics for all models"""
        return self.model_performance.copy()
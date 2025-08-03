"""
Advanced Mock API for simulating real-world services
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class AdvancedMockAPI:
    """
    Mock API service simulating real financial and AI services
    """

    def __init__(self):
        self.customers = {}
        self.transactions = []
        self.api_call_count = 0
        self.initialize_data()

    def initialize_data(self):
        """Initialize mock customer data"""
        self.customers['CUST-001'] = {
            'id': 'CUST-001',
            'name': 'John Doe',
            'balance': 2450.00,
            'credit_score': 742,
            'risk_profile': 'Low',
            'ai_confidence': 98.5,
            'account_type': 'Premium',
            'join_date': '2020-03-15',
            'last_payment': '2024-07-15',
            'investments': [
                {'type': 'Stocks', 'value': 15000, 'growth': 12.5},
                {'type': 'Bonds', 'value': 8000, 'growth': 4.2}
            ],
            'preferences': {
                'risk_tolerance': 'Moderate',
                'investment_goals': ['Retirement', 'Growth'],
                'notifications': True,
                'autopay': False
            },
            'behavior_patterns': {
                'spending_trend': 'Stable',
                'payment_habits': 'Excellent',
                'engagement_level': 'High'
            }
        }

    async def get_customer_data(self, customer_id: str) -> Dict[str, Any]:
        """Get customer data by ID"""
        self.api_call_count += 1
        await self._simulate_delay()

        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        return customer.copy()

    async def call_ai(self, prompt: str, context: Dict = None, model: str = 'gpt-4-turbo') -> str:
        """Simulate AI model API call"""
        self.api_call_count += 1
        await self._simulate_delay(min_delay=500, max_delay=2000)

        # Simulate different AI responses based on prompt analysis
        return self._generate_ai_response(prompt, context, model)

    async def process_complex_request(self, request: str) -> Dict[str, Any]:
        """Process complex multi-step requests"""
        self.api_call_count += 1
        await self._simulate_delay(min_delay=1000, max_delay=3000)

        return {
            'analysis': 'Multi-model AI analysis completed',
            'confidence': 95 + random.random() * 4,
            'recommendations': [
                'Implement automated savings strategy',
                'Optimize investment portfolio allocation',
                'Enhance credit utilization efficiency'
            ],
            'actions': [
                {'type': 'financial_optimization', 'status': 'completed'},
                {'type': 'risk_assessment', 'status': 'completed'},
                {'type': 'predictive_modeling', 'status': 'in_progress'}
            ],
            'timestamp': datetime.now().isoformat()
        }

    async def get_realtime_insights(self) -> Dict[str, Any]:
        """Get real-time market and customer insights"""
        self.api_call_count += 1
        await self._simulate_delay(min_delay=200, max_delay=500)

        return {
            'market_trends': random.choice([
                'Bullish sentiment detected in tech sector',
                'Moderate growth expected in financial markets',
                'Defensive positioning recommended'
            ]),
            'risk_factors': random.choice([
                'Low volatility expected next quarter',
                'Moderate risk in emerging markets',
                'Stable economic indicators'
            ]),
            'opportunities': f"{random.randint(2, 5)} high-yield investment options identified",
            'recommendations': random.choice([
                'Consider increasing emergency fund by 12%',
                'Diversify portfolio with international exposure',
                'Rebalance towards growth stocks'
            ]),
            'confidence_score': 85 + random.random() * 10,
            'timestamp': datetime.now().isoformat()
        }

    async def record_interaction(self, customer_id: str, interaction_data: Dict) -> Dict[str, Any]:
        """Record interaction for learning purposes"""
        self.api_call_count += 1
        await self._simulate_delay(min_delay=50, max_delay=200)

        interaction_id = f"INT-{len(self.transactions):06d}"

        interaction_record = {
            'id': interaction_id,
            'customer_id': customer_id,
            'timestamp': datetime.now().isoformat(),
            'data': interaction_data,
            'status': 'recorded'
        }

        self.transactions.append(interaction_record)

        return {
            'success': True,
            'interaction_id': interaction_id,
            'timestamp': interaction_record['timestamp']
        }

    def analyze_complexity(self, prompt: str) -> float:
        """Analyze complexity of user prompt"""
        complex_keywords = [
            'analyze', 'recommend', 'optimize', 'predict', 'strategy',
            'portfolio', 'investment', 'financial planning', 'risk assessment'
        ]

        prompt_lower = prompt.lower()
        complexity_score = sum(0.15 for keyword in complex_keywords if keyword in prompt_lower)

        # Add length-based complexity
        length_factor = min(len(prompt) / 200, 0.3)

        return min(complexity_score + length_factor + random.random() * 0.2, 1.0)

    def _generate_ai_response(self, prompt: str, context: Dict, model: str) -> str:
        """Generate realistic AI responses"""
        prompt_lower = prompt.lower()

        # Response templates based on intent
        responses = {
            'balance': "Based on advanced AI analysis of your account, your current balance shows healthy financial patterns. I've identified optimization opportunities that could save you approximately $180 monthly through strategic payment timing and credit utilization improvements.",

            'payment': "I've created an intelligent payment strategy using predictive modeling and market analysis. This optimized plan minimizes interest charges while improving your credit profile. The AI recommends paying $300 now, followed by $150 monthly payments.",

            'analysis': "Comprehensive AI analysis reveals excellent financial health with 94.8% positive indicators. Your spending patterns demonstrate remarkable stability. I've identified 3 key wealth optimization opportunities: 1) Portfolio rebalancing for 15% better returns, 2) Tax optimization strategies, 3) Automated savings enhancement.",

            'investment': f"Multi-model AI market analysis using {model} suggests strategic portfolio adjustments. Based on your moderate risk profile and current market conditions, I recommend reallocating 15% to emerging tech sectors with projected 18-22% annual returns. Real-time data shows favorable entry points this week.",

            'optimize': "Advanced credit optimization algorithms have processed your data through multiple AI models. Recommended action plan: 1) Increase credit limit by $2,500 (94% approval probability), 2) Transfer $800 to high-yield account (3.2% APY), 3) Implement automated investment of $300/monthly into diversified index funds.",

            'help': f"I'm an advanced agentic AI system powered by {model} and real-time financial intelligence. I can autonomously analyze your complete financial picture, execute complex multi-step strategies, and continuously optimize your wealth management. What specific financial goal would you like me to help achieve?"
        }

        # Select appropriate response
        for keyword, response in responses.items():
            if keyword in prompt_lower:
                return response

        # Default intelligent response
        return f"I've processed your request through our advanced AI pipeline using {model}. After analyzing your financial profile, market conditions, and risk factors, I've generated a comprehensive solution tailored to your specific situation. The AI confidence level for this recommendation is {85 + random.random() * 10:.1f}%."

    async def _simulate_delay(self, min_delay: int = 100, max_delay: int = 800):
        """Simulate realistic API response delays"""
        delay = random.randint(min_delay, max_delay) / 1000
        await asyncio.sleep(delay)

    def get_api_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        return {
            'total_calls': self.api_call_count,
            'customers': len(self.customers),
            'transactions': len(self.transactions),
            'uptime': '99.9%',
            'avg_response_time': f"{random.randint(120, 400)}ms"
        }
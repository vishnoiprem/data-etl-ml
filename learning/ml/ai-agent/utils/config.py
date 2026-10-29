"""
Configuration management for the Agentic AI system
"""

import os
import yaml
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """Load configuration from environment and config files"""

    # Default configuration
    config = {
        'ai_models': {
            'openai': {
                'enabled': os.getenv('OPENAI_ENABLED', 'false').lower() == 'true',
                'api_key': os.getenv('OPENAI_API_KEY', '')
            },
            'anthropic': {
                'enabled': os.getenv('ANTHROPIC_ENABLED', 'false').lower() == 'true',
                'api_key': os.getenv('ANTHROPIC_API_KEY', '')
            },
            'google': {
                'enabled': os.getenv('GOOGLE_ENABLED', 'false').lower() == 'true',
                'api_key': os.getenv('GOOGLE_API_KEY', '')
            },
            'local': {
                'enabled': os.getenv('LOCAL_MODELS_ENABLED', 'true').lower() == 'true'
            }
        },
        'perception': {
            'sentiment_analysis': True,
            'entity_extraction': True,
            'intent_recognition': True
        },
        'reasoning': {
            'confidence_threshold': 0.7,
            'use_multiple_models': True,
            'fallback_enabled': True
        },
        'executor': {
            'max_concurrent_actions': 5,
            'timeout_seconds': 30
        },
        'learning': {
            'store_interactions': True,
            'update_models': True,
            'learning_rate': 0.01
        }
    }

    # Try to load from config file
    config_file = os.getenv('AGENTIC_CONFIG_FILE', 'config.yaml')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")

    return config
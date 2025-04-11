"""
Model configurations for AWS Bedrock Claude models
"""

# Default model to use
DEFAULT_MODEL = "claude-3-7-sonnet"

# Model configurations
MODEL_CONFIGS = {
    "claude-3-7-sonnet": {
        "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "max_tokens": 40960,
    },
    "claude-3-5-sonnet": {
        "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "max_tokens": 8000,
        "description": "Claude 3.5 Sonnet - Balanced performance and speed",
    },
    "claude-3-haiku": {
        "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "max_tokens": 8000,
        "description": "Claude 3 Haiku - Fast and cost-effective",
    },
    "claude-3-5-sonnet-v2": {
        "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "max_tokens": 8000,
        "description": "Claude 3-5 sonnet-v2",
    },
}

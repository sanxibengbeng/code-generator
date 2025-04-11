"""
Model configurations for AWS Bedrock Claude models
"""

# Default model to use
DEFAULT_MODEL = "claude-3-5-sonnet"

# Model configurations
MODEL_CONFIGS = {
    "claude-3-5-sonnet": {
        "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "max_tokens": 4096,
        "description": "Claude 3.5 Sonnet - Balanced performance and speed"
    },
    "claude-3-haiku": {
        "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "max_tokens": 4096,
        "description": "Claude 3 Haiku - Fast and cost-effective"
    },
    "claude-3-sonnet": {
        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
        "max_tokens": 4096,
        "description": "Claude 3 Sonnet - Balanced performance and speed"
    },
    "claude-3-opus": {
        "model_id": "anthropic.claude-3-opus-20240229-v1:0",
        "max_tokens": 4096,
        "description": "Claude 3 Opus - Most powerful model for complex tasks"
    }
}

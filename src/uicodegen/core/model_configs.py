"""
Model configurations for AWS Bedrock Claude models
"""
from uicodegen.utils.bedrock_client import invoke_claude_model, invoke_claude_model_streaming

# Default model to use
DEFAULT_MODEL = "claude-3-7-sonnet"

# Model configurations
MODEL_CONFIGS = {
    "claude-3-7-sonnet": {
        "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "max_tokens": 40960,
        "description": "Claude 3.7 Sonnet - Most capable model",
        "invoke": lambda client, prompt: invoke_claude_model(
            client, prompt, model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0", max_tokens=40960
        ),
        "invoke_streaming": lambda client, prompt: invoke_claude_model_streaming(
            client, prompt, model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0", max_tokens=40960
        ),
    },
    "claude-3-5-sonnet": {
        "model_id": "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
        "max_tokens": 8000,
        "description": "Claude 3.5 Sonnet - Balanced performance and speed",
        "invoke": lambda client, prompt: invoke_claude_model(
            client, prompt, model_id="us.anthropic.claude-3-5-sonnet-20240620-v1:0", max_tokens=8000
        ),
        "invoke_streaming": lambda client, prompt: invoke_claude_model_streaming(
            client, prompt, model_id="us.anthropic.claude-3-5-sonnet-20240620-v1:0", max_tokens=8000
        ),
    },
    "claude-3-haiku": {
        "model_id": "us.anthropic.claude-3-haiku-20240307-v1:0",
        "max_tokens": 8000,
        "description": "Claude 3 Haiku - Fast and cost-effective",
        "invoke": lambda client, prompt: invoke_claude_model(
            client, prompt, model_id="us.anthropic.claude-3-haiku-20240307-v1:0", max_tokens=8000
        ),
        "invoke_streaming": lambda client, prompt: invoke_claude_model_streaming(
            client, prompt, model_id="us.anthropic.claude-3-haiku-20240307-v1:0", max_tokens=8000
        ),
    },
    "claude-3-5-haiku": {
        "model_id": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
        "max_tokens": 8000,
        "description": "Claude 3 Haiku - Fast and cost-effective",
        "invoke": lambda client, prompt: invoke_claude_model(
            client, prompt, model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0", max_tokens=8000
        ),
        "invoke_streaming": lambda client, prompt: invoke_claude_model_streaming(
            client, prompt, model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0", max_tokens=8000
        ),
    },
    "claude-3-5-sonnet-v2": {
        "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "max_tokens": 8000,
        "description": "Claude 3-5 sonnet-v2",
        "invoke": lambda client, prompt: invoke_claude_model(
            client, prompt, model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0", max_tokens=8000
        ),
        "invoke_streaming": lambda client, prompt: invoke_claude_model_streaming(
            client, prompt, model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0", max_tokens=8000
        ),
    },
}

"""
AWS Bedrock client utility for interacting with Claude models
"""
import os
import json
import boto3
from botocore.config import Config

def get_bedrock_client(region="us-east-1"):
    """
    Create and return a Bedrock client
    
    Args:
        region: AWS region (default: us-east-1)
        
    Returns:
        boto3.client: Configured Bedrock client
    """
    # Configure retry settings
    config = Config(
        region_name=region,
        retries={
            'max_attempts': 3,
            'mode': 'standard'
        }
    )
    
    # Create Bedrock client
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        config=config
    )
    
    return bedrock_client

def invoke_claude_model(client, prompt, model_id="anthropic.claude-3-sonnet-20240229-v1:0", max_tokens=4096, temperature=0.7):
    """
    Invoke Claude model with the given prompt
    
    Args:
        client: Bedrock client
        prompt: Text prompt to send to the model
        model_id: Claude model ID
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        
    Returns:
        dict: Model response
    """
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(request_body)
    )
    
    response_body = json.loads(response.get('body').read())
    
    # Extract usage information
    usage = {}
    if 'usage' in response_body:
        usage = response_body['usage']
    
    return {
        'content': response_body.get('content', [{}])[0].get('text', ''),
        'stop_reason': response_body.get('stop_reason', ''),
        'usage': usage
    }

def invoke_claude_model_streaming(client, prompt, model_id="anthropic.claude-3-sonnet-20240229-v1:0", max_tokens=4096, temperature=0.7):
    """
    Invoke Claude model with streaming response
    
    Args:
        client: Bedrock client
        prompt: Text prompt to send to the model
        model_id: Claude model ID
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        
    Yields:
        str: Chunks of generated text
    """
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    response = client.invoke_model_with_response_stream(
        modelId=model_id,
        body=json.dumps(request_body)
    )
    
    stream = response.get('body')
    
    if stream:
        for event in stream:
            chunk = event.get('chunk')
            if chunk:
                chunk_data = json.loads(chunk.get('bytes').decode())
                if 'content' in chunk_data and len(chunk_data['content']) > 0:
                    yield chunk_data['content'][0].get('text', '')

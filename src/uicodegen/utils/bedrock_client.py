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

def invoke_claude_model(client, prompt, model_id="anthropic.claude-3-sonnet-20240229-v1:0", max_tokens=4096, temperature=0.7, prefill_prompt="here is the result"):
    """
    Invoke Claude model with the given prompt
    
    Args:
        client: Bedrock client
        prompt: Text prompt to send to the model
        model_id: Claude model ID
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        prefill_prompt: Text to prefill the assistant's response
        
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
            },
            {
                "role": "assistant",
                "content": prefill_prompt
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

def invoke_claude_model_streaming(client, prompt, model_id="anthropic.claude-3-sonnet-20240229-v1:0", max_tokens=4096, temperature=0.7, prefill_prompt="here is the result"):
    """
    Invoke Claude model with streaming response
    
    Args:
        client: Bedrock client
        prompt: Text prompt to send to the model
        model_id: Claude model ID
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        prefill_prompt: Text to prefill the assistant's response
        
    Yields:
        str or dict: Chunks of generated text or metrics information
    """
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": prompt
            },
            {
                "role": "assistant",
                "content": prefill_prompt 
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
                
                # Handle different types of chunks
                if chunk_data.get('type') == 'content_block_delta':
                    delta = chunk_data.get('delta', {})
                    if delta.get('type') == 'text_delta':
                        chunk_text = delta.get('text', '')
                        if chunk_text:
                            yield chunk_text
                
                # Also yield metrics at the end if available
                elif chunk_data.get('type') == 'message_stop' and 'amazon-bedrock-invocationMetrics' in chunk_data:
                    # This is a special yield with metrics that can be handled by the caller
                    metrics = chunk_data.get('amazon-bedrock-invocationMetrics', {})
                    yield {
                        'type': 'metrics',
                        'input_tokens': metrics.get('inputTokenCount', 0),
                        'output_tokens': metrics.get('outputTokenCount', 0)
                    }
                
                # Handle message_delta with usage information
                elif chunk_data.get('type') == 'message_delta' and 'usage' in chunk_data:
                    if 'output_tokens' in chunk_data.get('usage', {}):
                        output_tokens = chunk_data['usage']['output_tokens']
                        yield {
                            'type': 'usage',
                            'output_tokens': output_tokens
                        }

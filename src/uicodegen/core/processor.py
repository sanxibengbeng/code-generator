import os
import json
import time
import boto3
import botocore.config
import botocore.exceptions

from uicodegen.utils.image_utils import encode_image
from uicodegen.utils.code_extractor import extract_code_from_text
from uicodegen.core.model_configs import MODEL_CONFIGS, DEFAULT_MODEL
from uicodegen.utils.fallback_templates import (
    create_fallback_html, create_fallback_css, create_fallback_js,
    create_timeout_html, create_error_html
)

# Initialize AWS Bedrock client
try:
    from botocore.config import Config
    
    # Configure the AWS SDK
    config = Config(
        retries={
            'max_attempts': 10,
            'mode': 'standard'
        }
    )
    
    # Create a Bedrock Runtime client
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1',
        config=config
    )
except Exception as e:
    print(f"Error initializing AWS Bedrock client: {str(e)}")
    bedrock_runtime = None

def save_generated_files(session_manager, session_id, html_content, css_content, js_content):
    """Save the generated code to files in the session directory"""
    file_paths = {}
    
    # Save HTML
    html_path = session_manager.get_generated_path(session_id, 'index.html')
    with open(html_path, 'w') as f:
        f.write(html_content)
    file_paths['html'] = html_path
    
    # Save CSS
    css_path = session_manager.get_generated_path(session_id, 'styles.css')
    with open(css_path, 'w') as f:
        f.write(css_content)
    file_paths['css'] = css_path
    
    # Save JS
    js_path = session_manager.get_generated_path(session_id, 'script.js')
    with open(js_path, 'w') as f:
        f.write(js_content)
    file_paths['js'] = js_path
    
    return file_paths
def process_image_streaming(session_manager, session_id, image_path):
    """Process the image with selected Bedrock Claude model using streaming API"""
    # Get session status
    status = session_manager.get_session_status(session_id)
    selected_model = status.get('selected_model', DEFAULT_MODEL)
    
    try:
        start_time = time.time()
        session_manager.update_session_status(
            session_id,
            current_task="Preparing image for streaming processing",
            progress_percentage=10,
            is_processing=True,
            processing_complete=False,
            error_message=None
        )
        
        # Encode image to base64
        base64_image = encode_image(image_path)
        
        session_manager.update_session_status(
            session_id,
            current_task="Connecting to AWS Bedrock for streaming",
            progress_percentage=15
        )
        
        # Get model configuration
        model_config = MODEL_CONFIGS[selected_model]
        model_id = model_config["model_id"]
        max_tokens = model_config["max_tokens"]
        model_display_name = selected_model.replace("-", " ").title()
        
        # Prepare the prompt for Claude
        prompt = f"""
        You are an expert web developer. I'm showing you a UI design image. 
        Please convert this design into responsive HTML, CSS, and JavaScript code.
        
        Use Bootstrap 5 for the responsive layout and Vue.js 3 for interactivity.
        Include Font Awesome for icons.
        
        Please provide:
        1. Complete index.html file
        2. Complete styles.css file
        3. Complete script.js file
        
        Make sure the code is clean, well-commented, and follows best practices.
        Make sure the code is the same language as in the picture.
        The website should be fully responsive and match the design as closely as possible.
        
        Return your response in the following format:
        
        ```html
        <!-- Your complete HTML code here -->
        ```
        
        ```css
        /* Your complete CSS code here */
        ```
        
        ```javascript
        // Your complete JavaScript code here
        ```
        """
        
        session_manager.update_session_status(
            session_id,
            current_task=f"Sending streaming request to {model_display_name}",
            progress_percentage=20
        )
        
        # Create the request payload
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        }
        
        # Convert the request body to JSON
        request_body_json = json.dumps(request_body)
        
        session_manager.update_session_status(
            session_id,
            current_task=f"Starting streaming with {model_display_name}",
            progress_percentage=25
        )
        
        try:
            # Invoke the model with streaming
            response = bedrock_runtime.invoke_model_with_response_stream(
                modelId=model_id,
                body=request_body_json
            )
            
            # Process the streaming response
            stream = response.get('body')
            
            # Initialize variables for collecting response
            full_text = ""
            chunk_count = 0
            
            # Create a debug log file for chunks
            debug_log_path = session_manager.get_generated_path(session_id, 'streaming_debug.log')
            with open(debug_log_path, 'w') as debug_file:
                debug_file.write("=== STREAMING DEBUG LOG ===\n\n")
                
                # Process each chunk
                for event in stream:
                    chunk = event.get('chunk')
                    if chunk:
                        chunk_data = json.loads(chunk.get('bytes').decode())
                        
                        # Log the raw chunk data
                        debug_file.write(f"--- CHUNK {chunk_count + 1} ---\n")
                        debug_file.write(f"Raw chunk data: {json.dumps(chunk_data, indent=2)}\n\n")
                        
                        # Extract text from the chunk
                        chunk_text = ""
                        
                        # Handle different types of chunks
                        if chunk_data.get('type') == 'content_block_delta':
                            delta = chunk_data.get('delta', {})
                            if delta.get('type') == 'text_delta':
                                chunk_text = delta.get('text', '')
                                full_text += chunk_text
                        elif chunk_data.get('type') == 'message_delta' and 'usage' in chunk_data:
                            # Extract token usage from message_delta
                            if 'output_tokens' in chunk_data.get('usage', {}):
                                output_tokens = chunk_data['usage']['output_tokens']
                                session_manager.update_session_status(
                                    session_id,
                                    output_tokens=output_tokens
                                )
                        elif chunk_data.get('type') == 'message_stop' and 'amazon-bedrock-invocationMetrics' in chunk_data:
                            # Extract metrics from message_stop
                            metrics = chunk_data.get('amazon-bedrock-invocationMetrics', {})
                            input_tokens = metrics.get('inputTokenCount', 0)
                            output_tokens = metrics.get('outputTokenCount', 0)
                            session_manager.update_session_status(
                                session_id,
                                input_tokens=input_tokens,
                                output_tokens=output_tokens
                            )
                        
                        # Log the extracted text
                        debug_file.write(f"Extracted text: {chunk_text}\n")
                        debug_file.write(f"Current full_text length: {len(full_text)}\n")
                        debug_file.write("-------------------\n\n")
                        
                        # Update progress based on chunk count
                        chunk_count += 1
                        session_manager.update_session_status(
                            session_id,
                            streaming_chunks=chunk_count
                        )
                        
                        # Dynamic progress update based on content received
                        # We'll estimate progress between 25-90% during streaming
                        current_status = session_manager.get_session_status(session_id)
                        current_progress = current_status['progress_percentage']
                        
                        if "```html" in full_text and current_progress < 40:
                            session_manager.update_session_status(
                                session_id,
                                current_task="Generating HTML code",
                                progress_percentage=40
                            )
                            debug_file.write("HTML marker found\n")
                        elif "```css" in full_text and current_progress < 60:
                            session_manager.update_session_status(
                                session_id,
                                current_task="Generating CSS code",
                                progress_percentage=60
                            )
                            debug_file.write("CSS marker found\n")
                        elif "```javascript" in full_text and current_progress < 80:
                            session_manager.update_session_status(
                                session_id,
                                current_task="Generating JavaScript code",
                                progress_percentage=80
                            )
                            debug_file.write("JavaScript marker found\n")
                        else:
                            # Gradual progress update
                            current_progress = min(25 + (chunk_count * 65 / 100), 90)
                            session_manager.update_session_status(
                                session_id,
                                current_task=f"Processing chunk {chunk_count}",
                                progress_percentage=int(current_progress)
                            )
                
                # Log the final full text
                debug_file.write("\n=== FINAL FULL TEXT ===\n")
                debug_file.write(full_text)
                debug_file.write("\n\n=== END OF LOG ===\n")
            
            session_manager.update_session_status(
                session_id,
                current_task="Extracting code from streaming response",
                progress_percentage=90
            )
            
            # Extract code from the full text with debug logging
            extract_debug_path = session_manager.get_generated_path(session_id, 'extraction_debug.log')
            with open(extract_debug_path, 'w') as extract_debug:
                html_code, css_code, js_code = extract_code_from_text(full_text, extract_debug)
                
                # If extraction failed, try to create minimal files
                if not html_code:
                    extract_debug.write("\n=== CREATING FALLBACK HTML ===\n")
                    html_code = create_fallback_html(full_text[:1000])
                
                if not css_code:
                    extract_debug.write("\n=== CREATING FALLBACK CSS ===\n")
                    css_code = create_fallback_css()
                
                if not js_code:
                    extract_debug.write("\n=== CREATING FALLBACK JS ===\n")
                    js_code = create_fallback_js()
        
        except botocore.exceptions.ReadTimeoutError:
            error_message = "Read timeout occurred. The request took too long to complete. Try using a smaller image or the non-streaming mode."
            session_manager.update_session_status(
                session_id,
                current_task=error_message,
                progress_percentage=0,
                error_message=error_message
            )
            
            # Create fallback files in case of timeout
            html_code = create_timeout_html()
            css_code = "/* No CSS generated due to timeout */"
            js_code = "// No JavaScript generated due to timeout"
            
            # Save these fallback files
            file_paths = save_generated_files(session_manager, session_id, html_code, css_code, js_code)
            session_manager.update_session_status(
                session_id,
                processing_complete=True
            )
            return
            
        session_manager.update_session_status(
            session_id,
            current_task="Saving generated files",
            progress_percentage=95
        )
        
        # Save the generated code to files
        file_paths = save_generated_files(session_manager, session_id, html_code, css_code, js_code)
        
        # Calculate processing time
        processing_time = round(time.time() - start_time, 2)
        
        session_manager.update_session_status(
            session_id,
            current_task="Processing complete",
            progress_percentage=100,
            processing_complete=True,
            processing_time=processing_time
        )
        
    except Exception as e:
        error_message = str(e)
        session_manager.update_session_status(
            session_id,
            current_task=f"Error in streaming: {str(e)}",
            progress_percentage=0,
            error_message=error_message
        )
        
        # Create fallback files in case of error
        html_code = create_error_html(error_message)
        css_code = "/* No CSS generated due to error */"
        js_code = "// No JavaScript generated due to error"
        
        # Save these fallback files
        file_paths = save_generated_files(session_manager, session_id, html_code, css_code, js_code)
        session_manager.update_session_status(
            session_id,
            processing_complete=True
        )
    finally:
        session_manager.update_session_status(
            session_id,
            is_processing=False
        )
def process_image_non_streaming(session_manager, session_id, image_path):
    """Process the image with selected Bedrock Claude model using non-streaming API"""
    # Get session status
    status = session_manager.get_session_status(session_id)
    selected_model = status.get('selected_model', DEFAULT_MODEL)
    
    try:
        start_time = time.time()
        session_manager.update_session_status(
            session_id,
            current_task="Preparing image for processing",
            progress_percentage=10,
            is_processing=True,
            processing_complete=False,
            error_message=None
        )
        
        # Encode image to base64
        base64_image = encode_image(image_path)
        
        session_manager.update_session_status(
            session_id,
            current_task="Connecting to AWS Bedrock",
            progress_percentage=20
        )
        
        # Get model configuration
        model_config = MODEL_CONFIGS[selected_model]
        model_id = model_config["model_id"]
        max_tokens = model_config["max_tokens"]
        model_display_name = selected_model.replace("-", " ").title()
        
        # Prepare the prompt for Claude
        prompt = f"""
        You are an expert web developer. I'm showing you a UI design image. 
        Please convert this design into responsive HTML, CSS, and JavaScript code.
        
        Use Bootstrap 5 for the responsive layout and Vue.js 3 for interactivity.
        Include Font Awesome for icons.
        
        Please provide:
        1. Complete index.html file
        2. Complete styles.css file
        3. Complete script.js file
        
        Make sure the code is clean, well-commented, and follows best practices.
        Make sure the code is the same language as in the picture.
        The website should be fully responsive and match the design as closely as possible.
        
        Return your response in the following format:
        
        ```html
        <!-- Your complete HTML code here -->
        ```
        
        ```css
        /* Your complete CSS code here */
        ```
        
        ```javascript
        // Your complete JavaScript code here
        ```
        """
        
        session_manager.update_session_status(
            session_id,
            current_task=f"Sending request to {model_display_name}",
            progress_percentage=30
        )
        
        # Create the request payload
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        }
        
        # Convert the request body to JSON
        request_body_json = json.dumps(request_body)
        
        session_manager.update_session_status(
            session_id,
            current_task=f"Processing with {model_display_name}",
            progress_percentage=40
        )
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=request_body_json
        )
        
        session_manager.update_session_status(
            session_id,
            current_task="Parsing response",
            progress_percentage=70
        )
        
        # Parse the response
        response_body = json.loads(response.get('body').read())
        content = response_body.get('content', [])
        
        # Get usage metrics if available
        if 'usage' in response_body:
            input_tokens = response_body['usage'].get('input_tokens', 0)
            output_tokens = response_body['usage'].get('output_tokens', 0)
            session_manager.update_session_status(
                session_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
        
        # Extract text from the response
        full_text = ""
        for item in content:
            if item.get('type') == 'text':
                full_text += item.get('text', '')
        
        session_manager.update_session_status(
            session_id,
            current_task="Extracting code from response",
            progress_percentage=80
        )
        
        # Extract code from the full text
        extract_debug_path = session_manager.get_generated_path(session_id, 'extraction_debug.log')
        with open(extract_debug_path, 'w') as extract_debug:
            html_code, css_code, js_code = extract_code_from_text(full_text, extract_debug)
            
            # If extraction failed, try to create minimal files
            if not html_code:
                extract_debug.write("\n=== CREATING FALLBACK HTML ===\n")
                html_code = create_fallback_html()
            
            if not css_code:
                extract_debug.write("\n=== CREATING FALLBACK CSS ===\n")
                css_code = create_fallback_css()
            
            if not js_code:
                extract_debug.write("\n=== CREATING FALLBACK JS ===\n")
                js_code = create_fallback_js()
        
        session_manager.update_session_status(
            session_id,
            current_task="Saving generated files",
            progress_percentage=90
        )
        
        # Save the generated code to files
        file_paths = save_generated_files(session_manager, session_id, html_code, css_code, js_code)
        
        # Calculate processing time
        processing_time = round(time.time() - start_time, 2)
        
        session_manager.update_session_status(
            session_id,
            current_task="Processing complete",
            progress_percentage=100,
            processing_complete=True,
            processing_time=processing_time
        )
        
    except Exception as e:
        error_message = str(e)
        session_manager.update_session_status(
            session_id,
            current_task=f"Error: {str(e)}",
            progress_percentage=0,
            error_message=error_message
        )
        
        # Create fallback files in case of error
        html_code = create_error_html(error_message)
        css_code = "/* No CSS generated due to error */"
        js_code = "// No JavaScript generated due to error"
        
        # Save these fallback files
        file_paths = save_generated_files(session_manager, session_id, html_code, css_code, js_code)
        session_manager.update_session_status(
            session_id,
            processing_complete=True
        )
    finally:
        session_manager.update_session_status(
            session_id,
            is_processing=False
        )

def process_image(session_manager, session_id, image_path):
    """Process the image with selected Bedrock Claude model"""
    # Get session status
    status = session_manager.get_session_status(session_id)
    use_streaming = status.get('use_streaming', False)
    
    if use_streaming:
        process_image_streaming(session_manager, session_id, image_path)
    else:
        process_image_non_streaming(session_manager, session_id, image_path)

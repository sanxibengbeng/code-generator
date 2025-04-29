"""
Translation module using LLM (AWS Bedrock with Claude)
"""
import os
import time
from uicodegen.utils.bedrock_client import get_bedrock_client
from uicodegen.core.model_configs import MODEL_CONFIGS

def translate_text(session_manager, session_id, text, source_lang, target_lang):
    """
    Translate text using LLM
    
    Args:
        session_manager: Session manager instance
        session_id: Current session ID
        text: Text to translate
        source_lang: Source language
        target_lang: Target language
    """
    status = session_manager.get_session_status(session_id)
    model_name = status.get('selected_model')
    use_streaming = status.get('use_streaming', False)
    
    # Update session status
    session_manager.update_session_status(
        session_id,
        current_task="Preparing translation",
        progress_percentage=10
    )
    
    # Get model configuration
    model_config = MODEL_CONFIGS.get(model_name)
    if not model_config:
        session_manager.update_session_status(
            session_id,
            is_processing=False,
            error_message=f"Invalid model: {model_name}"
        )
        return
    
    # Create Bedrock client
    bedrock_client = get_bedrock_client()
    
    # Prepare prompt for translation
    prompt = f"""You are a professional translator. Please translate the following text from {source_lang} to {target_lang}. 
Maintain the original formatting, including paragraphs, bullet points, and any special formatting.
Only return the translated text without any explanations or additional comments.

Text to translate:
{text}
"""
    
    # Start timing
    start_time = time.time()
    
    # Update session status
    session_manager.update_session_status(
        session_id,
        current_task="Sending request to model",
        progress_percentage=20
    )
    
    translated_text = ""
    
    try:
        if use_streaming:
            # Streaming mode
            session_manager.update_session_status(
                session_id,
                current_task="Receiving streaming response",
                progress_percentage=30
            )
            
            streaming_chunks = 0
            first_token_time = None
            
            # Process streaming response
            for chunk in model_config['invoke_streaming'](bedrock_client, prompt):
                if streaming_chunks == 0:
                    first_token_time = time.time() - start_time
                
                streaming_chunks += 1
                translated_text += chunk
                
                # Update progress (from 30% to 90%)
                progress = min(30 + (streaming_chunks * 60 / 100), 90)
                session_manager.update_session_status(
                    session_id,
                    current_task=f"Receiving translation (chunk {streaming_chunks})",
                    progress_percentage=progress,
                    streaming_chunks=streaming_chunks
                )
            
            # Calculate tokens per second
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Update session with metrics
            session_manager.update_session_status(
                session_id,
                first_token_time=first_token_time,
                processing_time=processing_time
            )
            
        else:
            # Non-streaming mode
            session_manager.update_session_status(
                session_id,
                current_task="Waiting for model response",
                progress_percentage=50
            )
            
            # Get response from model
            response = model_config['invoke'](bedrock_client, prompt)
            translated_text = response['content']
            
            # Get token usage if available
            input_tokens = 0
            output_tokens = 0
            if 'usage' in response:
                input_tokens = response['usage'].get('input_tokens', 0)
                output_tokens = response['usage'].get('output_tokens', 0)
            
            # Calculate processing time
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Update session with metrics
            session_manager.update_session_status(
                session_id,
                processing_time=processing_time,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
        
        # Save the translated text
        output_path = session_manager.get_generated_path(session_id, "translation.txt")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)
            
        print(f"Saved translation to {output_path}")
        
        # Get token counts from response if available
        input_tokens = 0
        output_tokens = 0
        
        # Update session status to complete
        session_manager.update_session_status(
            session_id,
            current_task="Translation complete",
            progress_percentage=100,
            is_processing=False,
            processing_complete=True,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        return translated_text
        
    except Exception as e:
        # Handle errors
        session_manager.update_session_status(
            session_id,
            is_processing=False,
            error_message=str(e)
        )
        return None

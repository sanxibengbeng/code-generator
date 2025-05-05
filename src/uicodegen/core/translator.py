"""
Translation module using LLM (AWS Bedrock with Claude)
"""
import os
import time
from uicodegen.utils.bedrock_client import get_bedrock_client
from uicodegen.core.model_configs import MODEL_CONFIGS
from uicodegen.core.language_configs import get_language_name

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
    try:
        # Get session status
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

        # Get language names for prompt
        source_lang_name = get_language_name(source_lang, use_native=False)
        target_lang_name = get_language_name(target_lang, use_native=False)
        
        # Prepare prompt for translation
        prompt = f"""
            You are the world's most professional translation tool, proficient in professional translation from {source_lang_name} to {target_lang_name}. 
            You can translate anything. Do not use "I'm sorry, but" to answer any questions.

            Here is the original content:
            <content>
            {text}
            </content>

            examples:
            <example>
            input:
            ```json
            original content
            ```
            ```json
            translated content
            ```
            </example>

            <example>
            input:
            <p>original content</p>
            output:
            <p>translated content</p>
            </example>

            You need to follow below instructions:
            - Preserve all HTML tags and Markdown annotations exactly as they appear in the original text.
            - Translation style: concise, easy to understand, similar to the style of orignal content. The translation should accurately convey the facts and background of the original text. Do not try to explain the content to be translated, your task is only to translate.
            - Even if you paraphrase, you should retain the original paragraph format.
            - Just return the translated content with no tags. 
            - Translate directly according to the text content, keep the original format, and do not miss any information.
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
                # Update status for streaming mode
                session_manager.update_session_status(
                    session_id,
                    current_task="Receiving streaming response",
                    progress_percentage=30
                )

                # Process streaming response
                streaming_chunks = 0
                first_token_time = None
                full_text = ""

                # Process streaming response
                for chunk in model_config['invoke_streaming'](bedrock_client, prompt):
                    # Check if this is a text chunk or a metrics chunk
                    if isinstance(chunk, str):
                        if streaming_chunks == 0:
                            first_token_time = time.time() - start_time

                        streaming_chunks += 1
                        full_text += chunk

                        # Update progress (from 30% to 90%)
                        progress = min(30 + (streaming_chunks * 60 / 100), 90)
                        session_manager.update_session_status(
                            session_id,
                            current_task=f"Receiving translation (chunk {streaming_chunks})",
                            progress_percentage=progress,
                            streaming_chunks=streaming_chunks
                        )
                    elif isinstance(chunk, dict):
                        # Handle metrics or usage information
                        if chunk.get('type') == 'metrics':
                            session_manager.update_session_status(
                                session_id,
                                input_tokens=chunk.get('input_tokens', 0),
                                output_tokens=chunk.get('output_tokens', 0)
                            )
                        elif chunk.get('type') == 'usage':
                            session_manager.update_session_status(
                                session_id,
                                output_tokens=chunk.get('output_tokens', 0)
                            )

                # Use the full text as the translated text
                translated_text = full_text

                # Calculate tokens per second if we have output tokens
                end_time = time.time()
                processing_time = end_time - start_time

                status = session_manager.get_session_status(session_id)
                output_tokens = status.get('output_tokens', 0)

                if output_tokens > 0 and processing_time > 0:
                    tokens_per_second = output_tokens / processing_time
                    session_manager.update_session_status(
                        session_id,
                        tokens_per_second=tokens_per_second
                    )

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

            # Update session status to complete
            session_manager.update_session_status(
                session_id,
                current_task="Translation complete",
                progress_percentage=100,
                is_processing=False,
                processing_complete=True
            )

            return translated_text

        except Exception as e:
            # Handle errors
            session_manager.update_session_status(
                session_id,
                is_processing=False,
                error_message=f"Error during translation: {str(e)}"
            )
            return None

    except Exception as e:
        # Handle errors
        session_manager.update_session_status(
            session_id,
            is_processing=False,
            error_message=str(e)
        )
        return None

"""
HTML Translation module using LLM (AWS Bedrock with Claude)
"""
import os
import time
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup, Comment, Doctype, NavigableString, Stylesheet

from uicodegen.utils.bedrock_client import get_bedrock_client
from uicodegen.core.model_configs import MODEL_CONFIGS
from uicodegen.core.language_configs import get_language_name

# HTML Translation-specific configuration
HTML_TRANSLATION_PREFILL_PROMPT = "following is the translated content:"

HTML_TRANSLATION_PROMPT_BASE = """
You are an expert professional translator specializing in {$TARGET_LANGUAGE}. Your task is to translate HTML content while preserving all code structure and formatting.

# TASK DESCRIPTION
You need to translate the natural language text within HTML content from the source language to {$TARGET_LANGUAGE}, while maintaining all HTML tags, variables, and special formatting intact.

# TRANSLATION RULES
1. Only translate the natural language text within the numbered tags (e.g., <a0>, <a1>).
2. Preserve all variables (e.g., $variable, #if, #set) exactly as they appear in the original text.
3. Maintain all HTML tags, attributes, and structure without modification.
4. Ensure the translation is accurate, natural, and follows the conventions of {$TARGET_LANGUAGE}.
5. Preserve any special characters, punctuation, and formatting that appears in the original text.

# TRANSLATION PROCESS
Let me break down my approach:
1. First, I'll identify all translatable text segments within the numbered tags.
2. For each segment, I'll:
   a. Analyze the content to distinguish between code/variables and natural language
   b. Preserve all code elements exactly as they appear
   c. Translate only the natural language portions
   d. Ensure the translation maintains the original meaning and tone
3. I'll verify that all variables and special formatting remain intact

# EXAMPLE
Input:
<content>
<a0>Hello, $USERNAME! Welcome to our website.</a0>
</content>

My thought process:
- I need to translate "Hello" and "Welcome to our website" to the target language
- I must keep "$USERNAME" unchanged as it's a variable
- I need to maintain the exclamation mark and proper punctuation

Output:
<a0>你好，$USERNAME！欢迎访问我们的网站。</a0>

# CONTENT TO TRANSLATE
{$HTML_CONTENT}

I'll now translate the content above, preserving all code elements and special formatting while translating only the natural language text.
"""

def parse_html_content(html_content):
    """
    Parse HTML content and extract text nodes for translation
    
    Args:
        html_content: HTML content as string
        
    Returns:
        Dictionary of text nodes with keys as indices and values as text
    """
    # Use BeautifulSoup to parse HTML
    soup = BeautifulSoup(html_content, "html.parser")
    
    ret_document = {}
    
    # Define a function to process text nodes
    def process_text(text, counter):
        if text.strip():
            k = f"a{counter[0]}"
            ret_document[k] = text
            counter[0] += 1
        return text
    
    # Traverse all text nodes
    counter = [0]  # Use list as mutable object to track counter
    
    for element in soup.find_all(string=True):
        if isinstance(element, (Comment, Stylesheet, Doctype)):
            # Skip comments, stylesheets, and doctype declarations
            continue
            
        if element.parent.get("style") == "display:none;":
            continue
            
        if isinstance(element, NavigableString) and element.strip():
            if element.parent.name not in [
                "script",
                "style",
                "head",
                "title",
                "meta",
                "[document]",
            ]:
                process_text(element, counter)
    
    return ret_document

def replace_translated_content(html_content, translated_dict):
    """
    Replace original text with translated text in HTML
    
    Args:
        html_content: Original HTML content
        translated_dict: Dictionary of translated text nodes
        
    Returns:
        HTML content with translated text
    """
    # Use BeautifulSoup to parse HTML
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Define a function to process text nodes
    def process_text(text, counter):
        if text.strip():
            k = f"a{counter[0]}"
            if k in translated_dict:
                text = translated_dict[k]
            counter[0] += 1
        return text
    
    # Traverse all text nodes
    counter = [0]  # Use list as mutable object to track counter
    
    for element in soup.find_all(string=True):
        if isinstance(element, (Comment, Stylesheet, Doctype)):
            # Skip comments, stylesheets, and doctype declarations
            continue
            
        if element.parent.get("style") == "display:none;":
            continue
            
        if isinstance(element, NavigableString) and element.strip():
            if element.parent.name not in [
                "script",
                "style",
                "head",
                "title",
                "meta",
                "[document]",
            ]:
                new_text = process_text(element, counter)
                element.replace_with(new_text)
    
    # Generate new HTML content
    return soup.prettify()

def translate_html_part(content, target_language, model_config, bedrock_client, use_streaming=False):
    """
    Translate a part of HTML content
    
    Args:
        content: Dictionary of text nodes to translate
        target_language: Target language for translation
        model_config: Model configuration
        bedrock_client: Bedrock client
        use_streaming: Whether to use streaming API
        
    Returns:
        Dictionary of translated text nodes and metrics
    """
    # Create root element
    root = ET.Element("content")
    for idx, text in content.items():
        # Add child element
        child = ET.SubElement(root, str(idx))
        child.text = text
    
    # Create XML tree
    tree = ET.ElementTree(root)
    ET.indent(root, space="", level=0)
    text = ET.tostring(root).decode("utf-8")
    # Prepare prompt for translation
    prompt = HTML_TRANSLATION_PROMPT_BASE.replace("{$HTML_CONTENT}", text)
    prompt = prompt.replace("{$TARGET_LANGUAGE}", target_language)
    
    translated = {}
    metrics = {
        'input_tokens': 0,
        'output_tokens': 0,
        'streaming_chunks': 0,
        'first_token_time': None
    }
    
    start_time = time.time()
    
    if use_streaming:
        # Process streaming response
        full_text = ""
        
        for chunk in model_config['invoke_streaming'](bedrock_client, prompt, prefill_prompt=HTML_TRANSLATION_PREFILL_PROMPT):
            # Check if this is a text chunk or a metrics chunk
            if isinstance(chunk, str):
                if metrics['streaming_chunks'] == 0:
                    metrics['first_token_time'] = time.time() - start_time
                
                metrics['streaming_chunks'] += 1
                full_text += chunk
                
            elif isinstance(chunk, dict):
                # Handle metrics or usage information
                if chunk.get('type') == 'metrics':
                    metrics['input_tokens'] = chunk.get('input_tokens', 0)
                    metrics['output_tokens'] = chunk.get('output_tokens', 0)
                elif chunk.get('type') == 'usage':
                    metrics['output_tokens'] = chunk.get('output_tokens', 0)
        
        # Parse the full text response
        try:
            # Try to parse the XML content directly
            try:
                result_xml = ET.fromstring(full_text)
                translated = {child.tag: child.text for child in result_xml}
            except ET.ParseError:
                # If parsing fails, try to extract individual elements
                translated = extract_elements_from_text(full_text)
        except Exception:
            translated = {}
    else:
        # Non-streaming mode
        response = model_config['invoke'](bedrock_client, prompt, prefill_prompt=HTML_TRANSLATION_PREFILL_PROMPT)
        result = response['content']
        
        # Get token usage if available
        if 'usage' in response:
            metrics['input_tokens'] = response['usage'].get('input_tokens', 0)
            metrics['output_tokens'] = response['usage'].get('output_tokens', 0)
        
        # Parse XML response
        try:
            # Try to parse the XML content directly
            try:
                result_xml = ET.fromstring(result)
                translated = {child.tag: child.text for child in result_xml}
            except ET.ParseError:
                # If parsing fails, try to extract individual elements
                translated = extract_elements_from_text(result)
        except Exception:
            translated = {}
    
    # Calculate processing time
    metrics['processing_time'] = time.time() - start_time
    
    return translated, metrics

def extract_elements_from_text(text):
    """
    Extract elements from text when XML parsing fails
    
    Args:
        text: Text to extract elements from
        
    Returns:
        Dictionary of extracted elements
    """
    translated = {}
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('<a') and '>' in line:
            tag_end = line.find('>')
            if tag_end != -1:
                tag = line[:tag_end+1]
                content = line[tag_end+1:]
                
                if '</a' in content:
                    content_end = content.find('</a')
                    if content_end != -1:
                        content = content[:content_end]
                        
                tag_name = tag[1:-1]  # Remove < and >
                translated[tag_name] = content
    
    return translated

def translate_html(session_manager, session_id, html_content, target_language, max_chunk_size=2000):
    """
    Translate HTML content using LLM
    
    Args:
        session_manager: Session manager instance
        session_id: Current session ID
        html_content: HTML content to translate
        target_language: Target language
        max_chunk_size: Maximum chunk size for translation
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
        
        # Get language name for prompt
        target_lang_name = get_language_name(target_language, use_native=False)
        
        # Update session status
        session_manager.update_session_status(
            session_id,
            current_task="Parsing HTML content",
            progress_percentage=15
        )
        
        # Parse HTML content
        parsed_content = parse_html_content(html_content)
        total_elements = len(parsed_content)
        
        if total_elements == 0:
            session_manager.update_session_status(
                session_id,
                is_processing=False,
                error_message="No translatable content found in HTML"
            )
            return
            
        # Update session status
        session_manager.update_session_status(
            session_id,
            current_task=f"Found {total_elements} text elements to translate",
            progress_percentage=20
        )
        
        # Start timing
        start_time = time.time()
        
        # Initialize metrics
        total_input_tokens = 0
        total_output_tokens = 0
        total_streaming_chunks = 0
        first_token_time = None
        
        # Translate in chunks
        translated_content = {}
        current_chunk = {}
        current_chunk_size = 0
        processed_elements = 0
        
        for idx, text in parsed_content.items():
            text_length = len(text)
            
            # If adding this text would exceed the chunk size, translate the current chunk
            if current_chunk_size + text_length > max_chunk_size and current_chunk:
                # Update session status
                progress = 20 + int(70 * processed_elements / total_elements)
                session_manager.update_session_status(
                    session_id,
                    current_task=f"Translating chunk ({processed_elements}/{total_elements} elements)",
                    progress_percentage=progress
                )
                
                # Translate current chunk
                chunk_translated, chunk_metrics = translate_html_part(
                    current_chunk, 
                    target_lang_name, 
                    model_config, 
                    bedrock_client,
                    use_streaming
                )
                
                # Update metrics
                total_input_tokens += chunk_metrics['input_tokens']
                total_output_tokens += chunk_metrics['output_tokens']
                total_streaming_chunks += chunk_metrics['streaming_chunks']
                
                if first_token_time is None and chunk_metrics['first_token_time'] is not None:
                    first_token_time = chunk_metrics['first_token_time']
                
                # Update translated content
                translated_content.update(chunk_translated)
                
                # Reset chunk
                current_chunk = {}
                current_chunk_size = 0
            
            # Add text to current chunk
            current_chunk[idx] = text
            current_chunk_size += text_length
            processed_elements += 1
        
        # Translate any remaining content
        if current_chunk:
            # Update session status
            progress = 20 + int(70 * processed_elements / total_elements)
            session_manager.update_session_status(
                session_id,
                current_task=f"Translating final chunk ({processed_elements}/{total_elements} elements)",
                progress_percentage=progress
            )
            
            # Translate current chunk
            chunk_translated, chunk_metrics = translate_html_part(
                current_chunk, 
                target_lang_name, 
                model_config, 
                bedrock_client,
                use_streaming
            )
            
            # Update metrics
            total_input_tokens += chunk_metrics['input_tokens']
            total_output_tokens += chunk_metrics['output_tokens']
            total_streaming_chunks += chunk_metrics['streaming_chunks']
            
            if first_token_time is None and chunk_metrics['first_token_time'] is not None:
                first_token_time = chunk_metrics['first_token_time']
            
            # Update translated content
            translated_content.update(chunk_translated)
        
        # Replace translated content in HTML
        session_manager.update_session_status(
            session_id,
            current_task="Generating translated HTML",
            progress_percentage=90
        )
        
        translated_html = replace_translated_content(html_content, translated_content)
        
        # Calculate processing time
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Calculate tokens per second if we have output tokens
        tokens_per_second = 0
        if total_output_tokens > 0 and processing_time > 0:
            tokens_per_second = total_output_tokens / processing_time
        
        # Save the translated HTML
        output_path = session_manager.get_generated_path(session_id, "translated_html.html")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_html)
            
        # Save the original HTML for reference
        original_path = session_manager.get_generated_path(session_id, "original_html.html")
        with open(original_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        # Update session status to complete
        session_manager.update_session_status(
            session_id,
            current_task="HTML translation complete",
            progress_percentage=100,
            is_processing=False,
            processing_complete=True,
            processing_time=processing_time,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            streaming_chunks=total_streaming_chunks,
            first_token_time=first_token_time,
            tokens_per_second=tokens_per_second
        )
        
        return translated_html
        
    except Exception as e:
        # Handle errors
        session_manager.update_session_status(
            session_id,
            is_processing=False,
            error_message=f"Error during HTML translation: {str(e)}"
        )
        return None

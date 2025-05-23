import os
import threading
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from uicodegen.core.session_manager import SessionManager
from uicodegen.core.processor import process_image
from uicodegen.core.translator import translate_text
from uicodegen.core.html_translator import translate_html
from uicodegen.core.model_configs import MODEL_CONFIGS, DEFAULT_MODEL
from uicodegen.core.language_configs import get_all_languages, DEFAULT_SOURCE_LANGUAGE, DEFAULT_TARGET_LANGUAGE

def init_app(app, session_manager):
    """Initialize Flask routes"""
    
    @app.route('/')
    def index():
        return render_template('index.html', models=list(MODEL_CONFIGS.keys()), languages=get_all_languages(), active_tab="codegen")
        
    @app.route('/translate')
    def translate_page():
        return render_template('index.html', models=list(MODEL_CONFIGS.keys()), languages=get_all_languages(), active_tab="translate")
        
    @app.route('/html-translate')
    def html_translate_page():
        return render_template('index.html', models=list(MODEL_CONFIGS.keys()), languages=get_all_languages(), active_tab="html-translate")

    @app.route('/upload', methods=['POST'])
    def upload_file():
        # Create a new session
        session_id = session_manager.create_session()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        
        file = request.files['file']
        
        # Get selected model
        selected_model = DEFAULT_MODEL
        if 'model' in request.form:
            model_name = request.form['model']
            if model_name in MODEL_CONFIGS:
                selected_model = model_name
        
        # Get streaming preference
        use_streaming = False
        if 'streaming' in request.form:
            use_streaming = request.form['streaming'].lower() == 'true'
        
        # Update session with selected options
        session_manager.update_session_status(
            session_id,
            selected_model=selected_model,
            use_streaming=use_streaming,
            current_task="Starting process",
            progress_percentage=0,
            is_processing=True,
            processing_complete=False,
            error_message=None,
            input_tokens=0,
            output_tokens=0,
            processing_time=0,
            streaming_chunks=0
        )
        
        if file.filename == '':
            session_manager.update_session_status(
                session_id,
                is_processing=False,
                error_message='No selected file'
            )
            return jsonify({'error': 'No selected file'})
        
        if file:
            filename = secure_filename(file.filename)
            file_path = session_manager.get_upload_path(session_id, filename)
            file.save(file_path)
            
            # Start processing in a separate thread
            thread = threading.Thread(target=process_image, args=(session_manager, session_id, file_path))
            thread.start()
            
            return jsonify({
                'message': 'Processing started', 
                'session_id': session_id,
                'model': selected_model,
                'streaming': use_streaming
            })

    @app.route('/progress/<session_id>')
    def get_progress(session_id):
        status = session_manager.get_session_status(session_id)
        if status:
            return jsonify(status)
        else:
            return jsonify({'error': 'Session not found'}), 404

    @app.route('/result/<session_id>')
    def get_result(session_id):
        status = session_manager.get_session_status(session_id)
        
        if not status:
            return jsonify({'error': 'Session not found'}), 404
            
        if status['processing_complete']:
            return jsonify({
                'html_path': f'/generated/{session_id}/index.html',
                'css_path': f'/generated/{session_id}/styles.css',
                'js_path': f'/generated/{session_id}/script.js',
                'metrics': {
                    'input_tokens': status['input_tokens'],
                    'output_tokens': status['output_tokens'],
                    'processing_time': status['processing_time'],
                    'streaming_chunks': status['streaming_chunks'] if status['use_streaming'] else 0,
                    'first_token_time': status.get('first_token_time', 0),
                    'tokens_per_second': status.get('tokens_per_second', 0)
                },
                'model': status.get('selected_model', 'Unknown')
            })
        else:
            return jsonify({'error': 'Processing not complete'})

    @app.route('/generated/<path:filename>')
    def generated_files(filename):
        print(f"Serving file: {app.config['GENERATED_FOLDER']}/{filename}")
        return send_from_directory(app.config['GENERATED_FOLDER'], filename, as_attachment=False)
        
    @app.route('/translate/process', methods=['POST'])
    def process_translation():
        # Create a new session
        session_id = session_manager.create_session()
        
        # Get text to translate
        text = request.form.get('text', '')
        source_lang = request.form.get('source_lang', DEFAULT_SOURCE_LANGUAGE)
        target_lang = request.form.get('target_lang', DEFAULT_TARGET_LANGUAGE)
        
        if not text:
            return jsonify({'error': 'No text provided'})
        
        # Get selected model
        selected_model = DEFAULT_MODEL
        if 'model' in request.form:
            model_name = request.form['model']
            if model_name in MODEL_CONFIGS:
                selected_model = model_name
        
        # Get streaming preference
        use_streaming = False
        if 'streaming' in request.form:
            use_streaming = request.form['streaming'].lower() == 'true'
        
        # Update session with selected options
        session_manager.update_session_status(
            session_id,
            selected_model=selected_model,
            use_streaming=use_streaming,
            current_task="Starting translation",
            progress_percentage=0,
            is_processing=True,
            processing_complete=False,
            error_message=None,
            input_tokens=0,
            output_tokens=0,
            processing_time=0,
            streaming_chunks=0
        )
        
        # Start processing in a separate thread
        thread = threading.Thread(
            target=translate_text, 
            args=(session_manager, session_id, text, source_lang, target_lang)
        )
        thread.start()
        
        return jsonify({
            'message': 'Translation started', 
            'session_id': session_id,
            'model': selected_model,
            'streaming': use_streaming
        })
        
    @app.route('/translate/result/<session_id>')
    def get_translation_result(session_id):
        status = session_manager.get_session_status(session_id)
        
        if not status:
            return jsonify({'error': 'Session not found'}), 404
            
        if status['processing_complete']:
            # Read the translation file
            translation_path = session_manager.get_generated_path(session_id, "translation.txt")
            
            try:
                with open(translation_path, 'r', encoding='utf-8') as f:
                    translated_text = f.read()
                
                print(f"Translation result for session {session_id}: {translated_text[:100]}...")
                
                return jsonify({
                    'translated_text': translated_text,
                    'metrics': {
                        'input_tokens': status.get('input_tokens', 0),
                        'output_tokens': status.get('output_tokens', 0),
                        'processing_time': status.get('processing_time', 0),
                        'streaming_chunks': status.get('streaming_chunks', 0) if status.get('use_streaming', False) else 0,
                        'first_token_time': status.get('first_token_time', 0),
                        'tokens_per_second': status.get('tokens_per_second', 0)
                    },
                    'model': status.get('selected_model', 'Unknown')
                })
            except Exception as e:
                return jsonify({'error': f'Error reading translation: {str(e)}'})
        else:
            return jsonify({'error': 'Processing not complete'})
            
    @app.route('/html-translate/process', methods=['POST'])
    def process_html_translation():
        # Create a new session
        session_id = session_manager.create_session()
        
        # Get HTML content to translate
        html_content = request.form.get('html', '')
        source_lang = request.form.get('source_lang', DEFAULT_SOURCE_LANGUAGE)
        target_lang = request.form.get('target_lang', DEFAULT_TARGET_LANGUAGE)
        
        if not html_content:
            return jsonify({'error': 'No HTML content provided'})
        
        # Get selected model
        selected_model = DEFAULT_MODEL
        if 'model' in request.form:
            model_name = request.form['model']
            if model_name in MODEL_CONFIGS:
                selected_model = model_name
        
        # Get streaming preference
        use_streaming = False
        if 'streaming' in request.form:
            use_streaming = request.form['streaming'].lower() == 'true'
        
        # Update session with selected options
        session_manager.update_session_status(
            session_id,
            selected_model=selected_model,
            use_streaming=use_streaming,
            current_task="Starting HTML translation",
            progress_percentage=0,
            is_processing=True,
            processing_complete=False,
            error_message=None,
            input_tokens=0,
            output_tokens=0,
            processing_time=0,
            streaming_chunks=0
        )
        
        # Start processing in a separate thread
        thread = threading.Thread(
            target=translate_html, 
            args=(session_manager, session_id, html_content, source_lang, target_lang)
        )
        thread.start()
        
        return jsonify({
            'message': 'HTML translation started', 
            'session_id': session_id,
            'model': selected_model,
            'streaming': use_streaming
        })
        
    @app.route('/html-translate/result/<session_id>')
    def get_html_translation_result(session_id):
        status = session_manager.get_session_status(session_id)
        
        if not status:
            return jsonify({'error': 'Session not found'}), 404
            
        if status['processing_complete']:
            # Read the translated HTML file
            translated_path = session_manager.get_generated_path(session_id, "translated_html.html")
            original_path = session_manager.get_generated_path(session_id, "original_html.html")
            
            try:
                with open(translated_path, 'r', encoding='utf-8') as f:
                    translated_html = f.read()
                    
                with open(original_path, 'r', encoding='utf-8') as f:
                    original_html = f.read()
                
                # Count elements translated (approximate)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(original_html, "html.parser")
                text_nodes = len([node for node in soup.find_all(string=True) if node.strip()])
                
                return jsonify({
                    'html_content': translated_html,
                    'elements_translated': text_nodes,
                    'input_size': len(original_html),
                    'output_size': len(translated_html),
                    'metrics': {
                        'input_tokens': status.get('input_tokens', 0),
                        'output_tokens': status.get('output_tokens', 0),
                        'processing_time': status.get('processing_time', 0),
                        'streaming_chunks': status.get('streaming_chunks', 0) if status.get('use_streaming', False) else 0,
                        'first_token_time': status.get('first_token_time', 0),
                        'tokens_per_second': status.get('tokens_per_second', 0)
                    },
                    'model': status.get('selected_model', 'Unknown')
                })
            except Exception as e:
                return jsonify({'error': f'Error reading HTML translation: {str(e)}'})
        else:
            return jsonify({'error': 'Processing not complete'})

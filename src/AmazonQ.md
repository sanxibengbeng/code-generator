# HTML Translator Integration

This document describes the integration of HTML translation functionality into the UI to Code Generator project.

## Overview

The HTML Translator feature allows users to translate HTML content while preserving the structure and formatting of the original HTML. This is particularly useful for translating websites, documentation, and other HTML-based content.

## Implementation Details

The HTML Translator functionality was implemented by:

1. Creating a new module `html_translator.py` in the core directory
2. Adding a new route for HTML translation in `routes.py`
3. Creating a new HTML template for the HTML translator tab
4. Updating the base template to include the new tab
5. Adding BeautifulSoup4 to the requirements

## Key Components

### HTML Translator Module

The HTML translator module (`html_translator.py`) provides the following functionality:

- Parsing HTML content to extract text nodes
- Translating text nodes while preserving HTML structure
- Replacing original text with translated text
- Handling large HTML documents by translating in chunks

### HTML Translation Process

1. The HTML content is parsed using BeautifulSoup4
2. Text nodes are extracted and organized into a dictionary
3. Text nodes are translated in chunks to avoid token limits
4. Translated text is inserted back into the original HTML structure
5. Both the original and translated HTML are saved for reference

### User Interface

The HTML Translator tab provides:

- A file upload option for HTML files
- A text area for pasting HTML content
- Target language selection
- Model selection and streaming options
- Real-time progress tracking
- Preview of the translated HTML
- Download and copy options for the translated HTML
- Processing metrics

## Usage

1. Navigate to the HTML Translator tab
2. Upload an HTML file or paste HTML content
3. Select the target language
4. Choose the model and streaming options
5. Click "Translate HTML"
6. Monitor the translation progress
7. Preview, download, or copy the translated HTML

## Technical Notes

- The HTML translation uses the same AWS Bedrock Claude models as the text translator
- BeautifulSoup4 is used for HTML parsing and manipulation
- The translation is done in chunks to handle large HTML documents
- The HTML structure, attributes, and formatting are preserved during translation
- Only text nodes are translated, not HTML tags or attributes

"""
Utility functions for graph generation and file management
"""

import os
import time
import shutil
import requests
import re
import base64
from pathlib import Path
from urllib.parse import quote

def clean_dot_code(raw_output: str) -> str:
    """
    Clean DOT code from LLM output by removing markdown syntax and extracting pure DOT code
    
    Args:
        raw_output (str): Raw output from LLM that may contain markdown formatting
    
    Returns:
        str: Clean DOT code without markdown syntax
    """
    if not raw_output or not raw_output.strip():
        return ""
    
    # Remove leading/trailing whitespace
    cleaned = raw_output.strip()
    
    # Pattern 1: Remove markdown code blocks with optional language specification
    # Matches: ```dot, ```graphviz, ```DOT, or just ```
    markdown_pattern = r'```(?:dot|graphviz|DOT)?\s*\n?(.*?)\n?```'
    match = re.search(markdown_pattern, cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
    
    # Pattern 2: Remove any remaining backticks at start/end
    cleaned = re.sub(r'^`+|`+$', '', cleaned).strip()
    
    # Pattern 3: Remove common LLM prefixes/suffixes
    prefixes_to_remove = [
        r'^Here\'s the DOT code:?\s*',
        r'^The DOT code is:?\s*',
        r'^DOT code:?\s*',
        r'^Graph:?\s*',
        r'^Here is the digraph:?\s*'
    ]
    
    for prefix in prefixes_to_remove:
        cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE).strip()
    
    # Pattern 4: Remove common suffixes
    suffixes_to_remove = [
        r'\s*This creates the knowledge graph\.?$',
        r'\s*The graph is now ready\.?$',
        r'\s*Hope this helps!?\.?$'
    ]
    
    for suffix in suffixes_to_remove:
        cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE).strip()
    
    # Pattern 5: Ensure the code starts with 'digraph' or 'graph'
    if not re.match(r'^\s*(di)?graph\s+', cleaned, re.IGNORECASE):
        # Try to find the start of a digraph in the text
        digraph_match = re.search(r'((?:di)?graph\s+.*)', cleaned, re.DOTALL | re.IGNORECASE)
        if digraph_match:
            cleaned = digraph_match.group(1)
    
    return cleaned.strip()

def validate_dot_syntax(dot_code: str) -> tuple[bool, str]:
    """
    Validate DOT syntax using QuickChart API
    
    Args:
        dot_code (str): DOT code to validate
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    try:
        print("🔍 Validating DOT syntax using QuickChart API...")
        
        if not dot_code or not dot_code.strip():
            return False, "DOT code is empty"
        
        # Basic syntax checks
        dot_code_lower = dot_code.lower().strip()
        
        # Check if it starts with digraph or graph
        if not (dot_code_lower.startswith('digraph') or dot_code_lower.startswith('graph')):
            return False, "DOT code must start with 'digraph' or 'graph'"
        
        # Check for balanced braces
        open_braces = dot_code.count('{')
        close_braces = dot_code.count('}')
        if open_braces != close_braces:
            return False, f"Unbalanced braces: {open_braces} opening, {close_braces} closing"
        
        # Try to validate with QuickChart API (just test the request)
        encoded_dot = quote(dot_code)
        test_url = f"https://quickchart.io/graphviz?graph={encoded_dot}"
        
        # Make a HEAD request to check if the API would accept it
        response = requests.head(test_url, timeout=10)
        if response.status_code == 200:
            print("✅ DOT syntax validation passed")
            return True, "Valid DOT syntax"
        else:
            return False, f"QuickChart API validation failed with status {response.status_code}"
            
    except Exception as e:
        error_details = f"DOT syntax validation failed: {str(e)}"
        print(f"❌ {error_details}")
        return False, error_details

def compile_dot_to_png(dot_code: str, output_filename: str, output_dir: str = "output"):
    """
    Compile DOT code into a PNG image file using QuickChart API
    
    Args:
        dot_code (str): The DOT language code
        output_filename (str): Name for the output file (without extension)
        output_dir (str): Directory to save the output file
    
    Returns:
        tuple: (file_path, base64_image_data) or (None, None) on failure
    """
    try:
        print(f"🔧 Starting DOT compilation using QuickChart API for file: {output_filename}")
        print(f"📁 Output directory: {output_dir}")
        
        # Clean the DOT code first
        print("🧹 Cleaning DOT code...")
        original_length = len(dot_code)
        cleaned_dot = clean_dot_code(dot_code)
        cleaned_length = len(cleaned_dot)
        
        print(f"📏 Original code length: {original_length} characters")
        print(f"📏 Cleaned code length: {cleaned_length} characters")
        
        if not cleaned_dot.strip():
            error_msg = "❌ DOT code is empty after cleaning"
            print(error_msg)
            print(f"📝 Original DOT code:\n{'-'*50}")
            print(dot_code)
            print(f"{'-'*50}")
            return None, None
        
        # Show the cleaned DOT code for debugging
        print(f"📝 Cleaned DOT code:\n{'-'*50}")
        print(cleaned_dot)
        print(f"{'-'*50}")
        
        # Validate the cleaned DOT code
        print("🔍 Validating DOT syntax...")
        is_valid, error_msg = validate_dot_syntax(cleaned_dot)
        if not is_valid:
            print(f"❌ Validation failed: {error_msg}")
            return None, None
        
        print("✅ DOT syntax validation passed")
        
        # Ensure output directory exists
        print(f"📂 Ensuring output directory exists: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate the graph using QuickChart API
        print("🎨 Generating PNG from DOT code using QuickChart API...")
        
        # URL encode the DOT code
        encoded_dot = quote(cleaned_dot)
        api_url = f"https://quickchart.io/graphviz?graph={encoded_dot}"
        
        print(f"🌐 Making request to QuickChart API...")
        print(f"📏 Encoded DOT length: {len(encoded_dot)} characters")
        
        # Make the API request
        response = requests.get(api_url, timeout=30)
        
        if response.status_code == 200:
            print("✅ Successfully received image from QuickChart API")
            
            # Convert to base64 for direct embedding
            image_data = response.content
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Also save the file for download purposes
            final_path = os.path.join(output_dir, f"{output_filename}.png")
            
            with open(final_path, 'wb') as f:
                f.write(image_data)
            
            print(f"💾 Graph successfully saved as {final_path}")
            
            # Verify the file was created and get its size
            if os.path.exists(final_path):
                file_size = os.path.getsize(final_path)
                print(f"📊 Final file size: {file_size} bytes")
                print(f"📊 Base64 data size: {len(base64_image)} characters")
                return final_path, base64_image
            else:
                print(f"❌ Final file not found at {final_path}")
                return None, base64_image  # Still return base64 data even if file save failed
        else:
            error_msg = f"❌ QuickChart API request failed with status {response.status_code}"
            print(error_msg)
            if response.text:
                print(f"📝 API response: {response.text}")
            return None, None
        
    except Exception as e:
        error_msg = f"❌ DOT compilation failed: {str(e)}"
        print(error_msg)
        print(f"📝 DOT code that failed:\n{'-'*50}")
        print(dot_code)
        print(f"{'-'*50}")
        
        # Print detailed exception information
        import traceback
        print(f"🔍 Full error traceback:")
        traceback.print_exc()
        
        return None, None

def generate_unique_filename():
    """Generate a unique filename based on timestamp"""
    return f"graph_{int(time.time())}"

def cleanup_old_files(output_dir: str = "output", max_age_hours: int = 24):
    """
    Clean up old graph files to prevent disk bloat
    
    Args:
        output_dir (str): Directory to clean
        max_age_hours (int): Maximum age of files to keep in hours
    """
    try:
        if not os.path.exists(output_dir):
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getctime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    print(f"Cleaned up old file: {filename}")
                    
    except Exception as e:
        print(f"Error during cleanup: {e}")

def validate_input_text(text: str, min_length: int = 50) -> tuple[bool, str]:
    """
    Validate input text for processing
    
    Args:
        text (str): Input text to validate
        min_length (int): Minimum required length
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Please enter some lecture content to process."
    
    if len(text.strip()) < min_length:
        return False, f"Please enter at least {min_length} characters of lecture content."
    
    return True, ""

def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes"""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except:
        return 0.0

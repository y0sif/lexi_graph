"""
Utility functions for graph generation and file management
"""

import os
import time
import shutil
import graphviz
import re
from pathlib import Path

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
    Validate DOT syntax by attempting to parse it with graphviz
    
    Args:
        dot_code (str): DOT code to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Try to create a graphviz Source object
        graphviz.Source(dot_code)
        return True, ""
    except Exception as e:
        return False, str(e)

def compile_dot_to_png(dot_code: str, output_filename: str, output_dir: str = "output"):
    """
    Compile DOT code into a PNG image file
    
    Args:
        dot_code (str): The DOT language code
        output_filename (str): Name for the output file (without extension)
        output_dir (str): Directory to save the output file
    
    Returns:
        str: Path to the generated PNG file or None on failure
    """
    try:
        # Clean the DOT code first
        cleaned_dot = clean_dot_code(dot_code)
        
        # Validate the cleaned DOT code
        is_valid, error_msg = validate_dot_syntax(cleaned_dot)
        if not is_valid:
            print(f"Invalid DOT syntax: {error_msg}")
            print(f"Cleaned DOT code:\n{cleaned_dot}")
            return None
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate the graph
        graph = graphviz.Source(cleaned_dot, format='png')
        temp_path = graph.render(filename=output_filename, cleanup=True)
        
        # Move to output directory
        final_path = os.path.join(output_dir, f"{output_filename}.png")
        shutil.move(temp_path, final_path)
        
        print(f"Graph saved as {final_path}")
        return final_path
        
    except Exception as e:
        print(f"Error generating graph: {e}")
        print(f"Original DOT code:\n{dot_code}")
        return None

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

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
    
    # Pattern 6: Fix color attributes for filled nodes
    # When style=filled is used, color should be fillcolor for background
    cleaned = fix_color_attributes(cleaned)
    
    # Pattern 7: Replace unsupported colors with basic supported colors
    cleaned = fix_unsupported_colors(cleaned)
    
    return cleaned.strip()

def fix_color_attributes(dot_code: str) -> str:
    """
    Fix color attributes in DOT code for better rendering with style=filled
    
    Args:
        dot_code (str): DOT code that may have incorrect color attributes
    
    Returns:
        str: DOT code with fixed color attributes
    """
    if not dot_code:
        return dot_code
    
    # Check if the graph uses style=filled globally or on nodes
    has_filled_style = 'style=filled' in dot_code or 'style="filled"' in dot_code
    
    if has_filled_style:
        print("🎨 Fixing color attributes for filled nodes...")
        
        # Replace color=lightXXX with fillcolor=lightXXX in node definitions
        # Pattern matches: NodeName [attributes with color=lightcolor, other_attrs];
        color_pattern = r'(\w+\s*\[(?:[^,\]]*,\s*)*)(color=light\w+)((?:\s*,\s*[^,\]]*)*\])'
        
        def replace_color(match):
            prefix = match.group(1)  # NodeName [other_attrs,
            color_attr = match.group(2)  # color=lightblue
            suffix = match.group(3)  # , other_attrs]
            
            # Replace color= with fillcolor=
            fillcolor_attr = color_attr.replace('color=', 'fillcolor=')
            
            print(f"  🔧 Fixing: {color_attr} → {fillcolor_attr}")
            return prefix + fillcolor_attr + suffix
        
        cleaned = re.sub(color_pattern, replace_color, dot_code)
        
        # Also handle quoted color values: color="lightblue"
        quoted_color_pattern = r'(\w+\s*\[(?:[^,\]]*,\s*)*)(color="light\w+")((?:\s*,\s*[^,\]]*)*\])'
        
        def replace_quoted_color(match):
            prefix = match.group(1)
            color_attr = match.group(2)  # color="lightblue"
            suffix = match.group(3)
            
            fillcolor_attr = color_attr.replace('color=', 'fillcolor=')
            print(f"  🔧 Fixing: {color_attr} → {fillcolor_attr}")
            return prefix + fillcolor_attr + suffix
        
        cleaned = re.sub(quoted_color_pattern, replace_quoted_color, cleaned)
        
        # Add explicit fontcolor=black for all nodes to ensure text visibility
        # This prevents text from being invisible when fillcolor is applied
        print("🎨 Adding explicit fontcolor=black for text visibility...")
        
        # Pattern to find node definitions and add fontcolor if missing
        node_pattern = r'(\w+\s*\[)([^\]]+)(\])'
        
        def ensure_fontcolor(match):
            prefix = match.group(1)  # NodeName [
            attributes = match.group(2)  # all attributes
            suffix = match.group(3)  # ]
            
            # Check if fontcolor is already specified
            if 'fontcolor=' not in attributes:
                # Add fontcolor=black to ensure text is visible
                if attributes.strip().endswith(','):
                    new_attributes = attributes + ' fontcolor=black'
                else:
                    new_attributes = attributes + ', fontcolor=black'
                print(f"  ✏️ Adding fontcolor=black to node")
                return prefix + new_attributes + suffix
            
            return prefix + attributes + suffix
        
        cleaned = re.sub(node_pattern, ensure_fontcolor, cleaned)
        
        return cleaned
    
    return dot_code

def fix_unsupported_colors(dot_code: str) -> str:
    """
    Replace unsupported colors with basic colors that work with QuickChart
    Also ensures proper text contrast by using appropriate font colors
    
    Args:
        dot_code (str): DOT code that may contain unsupported colors
    
    Returns:
        str: DOT code with supported colors and proper text contrast
    """
    if not dot_code:
        return dot_code
    
    print("🎨 Converting unsupported colors to basic supported colors with proper text contrast...")
    
    # Mapping of unsupported colors to lighter, more readable alternatives
    color_mapping = {
        'lightgray': 'white',       # Use white instead of gray for better readability
        'lightgrey': 'white', 
        'lightblue': 'cyan',        # Use cyan instead of blue for better readability
        'lightgreen': 'yellow',     # Use yellow instead of green for better readability  
        'lightcyan': 'cyan',
        'lightpink': 'pink',
        'lightyellow': 'yellow',
        'lightsalmon': 'orange',
        'lightcoral': 'pink',
        'lightsteelblue': 'cyan',
        'lightseagreen': 'yellow',
        'lightslategray': 'white',
        'lightslategrey': 'white',
    }
    
    # Colors that need white text for good contrast
    dark_colors = {'blue', 'purple', 'red', 'green'}
    # Colors that work well with black text
    light_colors = {'white', 'yellow', 'cyan', 'pink', 'orange', 'gray'}
    
    # Replace both fillcolor and color attributes
    for unsupported, supported in color_mapping.items():
        # Replace fillcolor=lightcolor
        pattern1 = rf'fillcolor={unsupported}\b'
        replacement1 = f'fillcolor={supported}'
        if re.search(pattern1, dot_code):
            print(f"  🔧 Replacing: fillcolor={unsupported} → fillcolor={supported}")
            dot_code = re.sub(pattern1, replacement1, dot_code)
        
        # Replace fillcolor="lightcolor"
        pattern2 = rf'fillcolor="{unsupported}"\b'
        replacement2 = f'fillcolor="{supported}"'
        if re.search(pattern2, dot_code):
            print(f"  🔧 Replacing: fillcolor=\"{unsupported}\" → fillcolor=\"{supported}\"")
            dot_code = re.sub(pattern2, replacement2, dot_code)
        
        # Replace color=lightcolor (in case some still exist)
        pattern3 = rf'color={unsupported}\b'
        replacement3 = f'color={supported}'
        if re.search(pattern3, dot_code):
            print(f"  🔧 Replacing: color={unsupported} → color={supported}")
            dot_code = re.sub(pattern3, replacement3, dot_code)
        
        # Replace color="lightcolor"
        pattern4 = rf'color="{unsupported}"\b'
        replacement4 = f'color="{supported}"'
        if re.search(pattern4, dot_code):
            print(f"  🔧 Replacing: color=\"{unsupported}\" → color=\"{supported}\"")
            dot_code = re.sub(pattern4, replacement4, dot_code)
    
    # Now fix font colors based on background colors for better contrast
    print("🎨 Optimizing text contrast based on background colors...")
    
    # Pattern to find nodes with fillcolor and adjust fontcolor accordingly
    node_pattern = r'(\w+\s*\[)([^\]]+)(\])'
    
    def optimize_text_contrast(match):
        prefix = match.group(1)  # NodeName [
        attributes = match.group(2)  # all attributes
        suffix = match.group(3)  # ]
        
        # Extract fillcolor if present
        fillcolor_match = re.search(r'fillcolor=(["\']?)(\w+)\1', attributes)
        if fillcolor_match:
            color = fillcolor_match.group(2).lower()
            
            # Determine optimal font color based on background
            if color in dark_colors:
                optimal_fontcolor = 'white'
            else:
                optimal_fontcolor = 'black'
            
            # Update or add fontcolor
            if re.search(r'fontcolor=', attributes):
                # Replace existing fontcolor
                new_attributes = re.sub(r'fontcolor=(["\']?)\w+\1', f'fontcolor={optimal_fontcolor}', attributes)
                print(f"  ✏️ Updated fontcolor to {optimal_fontcolor} for {color} background")
            else:
                # Add fontcolor
                if attributes.strip().endswith(','):
                    new_attributes = attributes + f' fontcolor={optimal_fontcolor}'
                else:
                    new_attributes = attributes + f', fontcolor={optimal_fontcolor}'
                print(f"  ✏️ Added fontcolor={optimal_fontcolor} for {color} background")
            
            return prefix + new_attributes + suffix
        
        return prefix + attributes + suffix
    
    dot_code = re.sub(node_pattern, optimize_text_contrast, dot_code)
    
    return dot_code

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
        
        print(f"🌐 Generated QuickChart URL")
        print(f"📏 Encoded DOT length: {len(encoded_dot)} characters")
        print(f"🔗 Direct URL: {api_url}")
        
        # Return the direct URL instead of making the API call
        # This is much more efficient and follows best practices
        print("✅ Returning direct QuickChart URL for frontend to use")
        
        return None, api_url  # Return URL as the "image data"
        
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

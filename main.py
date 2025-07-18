"""
LexiGraph CLI - Command Line Interface for lecture to knowledge graph conversion
"""

import os
import shutil
from core.pipeline import pipeline, EXAMPLE_LECTURE
from core.utils import compile_dot_to_png, generate_unique_filename

def main():
    """Main CLI function"""
    print("🔗 LexiGraph - Lecture to Knowledge Graph Converter")
    print("=" * 50)
    
    # Use the example lecture content
    lecture_input = EXAMPLE_LECTURE
    
    # Run the pipeline
    print("\n[Processing...]")
    summary, dot_code = pipeline(lecture_input)
    
    if dot_code is None:
        print(f"❌ Error: {summary}")
        return
    
    # Output results
    print("\n[Summary Output]\n")
    print(summary)
    print("\n[DOT Code Output]\n")
    print(dot_code)
    
    # Generate unique filename and compile to PNG
    output_filename = generate_unique_filename()
    output_path = compile_dot_to_png(dot_code, output_filename)
    
    if output_path:
        print(f"\n✅ Graph saved successfully: {output_path}")
    else:
        print("\n❌ Failed to generate graph image")

if __name__ == "__main__":
    main()

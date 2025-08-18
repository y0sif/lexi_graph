#!/usr/bin/env python3
"""
Test script to verify QuickChart API integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.utils import compile_dot_to_png

def test_quickchart_api():
    """Test the QuickChart API with a simple graph"""
    
    # Simple test DOT code
    test_dot = """
    digraph G {
        main -> parse -> execute;
        main -> init;
        main -> cleanup;
        execute -> make_string;
        execute -> printf;
        init -> make_string;
        main -> printf;
        execute -> compare;
    }
    """
    
    print("🧪 Testing QuickChart API integration...")
    print(f"📝 Test DOT code:\n{test_dot}")
    
    # Test the compilation
    result = compile_dot_to_png(test_dot, "test_graph", "test_output")
    
    if result:
        print(f"✅ Test successful! Graph saved to: {result}")
        return True
    else:
        print("❌ Test failed!")
        return False

if __name__ == "__main__":
    success = test_quickchart_api()
    sys.exit(0 if success else 1)

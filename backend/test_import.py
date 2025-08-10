#!/usr/bin/env python3

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    from main import app
    print('✅ App imported successfully')
    print(f'App type: {type(app)}')
    
    # Test a simple endpoint
    print('Testing health endpoint...')
    
except Exception as e:
    print(f'❌ Import failed: {e}')
    import traceback
    traceback.print_exc()

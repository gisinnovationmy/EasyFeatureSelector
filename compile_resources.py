#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Compile resources for both PyQt5 and PyQt6 compatibility
"""

import os
import sys
import subprocess

def compile_resources():
    """
    Compile the resources.qrc file to resources.py with Qt6/Qt5 compatibility
    """
    qrc_file = "resources.qrc"
    output_file = "resources.py"
    
    if not os.path.exists(qrc_file):
        print(f"Error: {qrc_file} not found!")
        return False
    
    # Try to compile with PyQt6 first
    try:
        print("Attempting to compile with PyQt6...")
        subprocess.run(["pyrcc6", "-o", output_file, qrc_file], check=True)
        print(f"Successfully compiled with PyQt6 to {output_file}")
        
        # Add compatibility layer
        add_compatibility_layer(output_file)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("PyQt6 not available, trying PyQt5...")
    
    # Fall back to PyQt5
    try:
        subprocess.run(["pyrcc5", "-o", output_file, qrc_file], check=True)
        print(f"Successfully compiled with PyQt5 to {output_file}")
        
        # Add compatibility layer
        add_compatibility_layer(output_file)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Neither pyrcc6 nor pyrcc5 found!")
        return False

def add_compatibility_layer(filepath):
    """
    Modify the resources.py file to support both PyQt5 and PyQt6
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace PyQt5 import with compatibility import
    if 'from PyQt5 import QtCore' in content:
        content = content.replace(
            'from PyQt5 import QtCore',
            'try:\n    from PyQt6 import QtCore\nexcept ImportError:\n    from PyQt5 import QtCore'
        )
    # Replace PyQt6 import with compatibility import  
    elif 'from PyQt6 import QtCore' in content:
        content = content.replace(
            'from PyQt6 import QtCore',
            'try:\n    from PyQt6 import QtCore\nexcept ImportError:\n    from PyQt5 import QtCore'
        )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Added Qt5/Qt6 compatibility layer to {filepath}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    success = compile_resources()
    sys.exit(0 if success else 1)
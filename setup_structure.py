#!/usr/bin/env python3
"""
Complete setup script for music_bot_project
Generates all directory structures and initial files
"""

import os
import sys
from pathlib import Path

BASE = Path(__file__).parent

def setup_project():
    """Create all directories and initial files"""
    
    # Directory structure with their init files
    paths = [
        "backend/app/routers",
        "backend/app/services",
        "backend/tests",
        "bot/handlers",
    ]
    
    for path in paths:
        p = BASE / path
        p.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py for each package
        init_file = p / "__init__.py"
        init_file.touch()
    
    # Also create __init__ files for parent packages
    (BASE / "backend" / "app" / "__init__.py").touch()
    (BASE / "backend" / "__init__.py").touch()
    (BASE / "bot" / "__init__.py").touch()
    
    print("✓ All directories created successfully")
    return True

if __name__ == "__main__":
    if setup_project():
        sys.exit(0)
    sys.exit(1)

import os
import sys

# Create directory structure
dirs = [
    "backend/app/routers",
    "backend/app/services",
    "backend/tests",
    "bot/handlers",
]

base_path = r"c:\Users\Lenovo\Desktop\software-engineering-toolkit\music_bot_project"

for dir_path in dirs:
    full_path = os.path.join(base_path, dir_path)
    os.makedirs(full_path, exist_ok=True)
    
    # Create __init__.py in each package directory
    init_file = os.path.join(full_path, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("")

print("Directory structure created successfully!")

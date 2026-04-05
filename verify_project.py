"""
Music Bot Project - File Verification Script
Verifies that all required files are in place
"""

import os
from pathlib import Path

BASE = Path(__file__).parent
REQUIRED_FILES = {
    # Backend
    "backend/requirements.txt": "dependencies",
    "backend/.env": "configuration",
    "backend/app/__init__.py": "package",
    "backend/app/main.py": "FastAPI app",
    "backend/app/config.py": "settings",
    "backend/app/database.py": "database setup",
    "backend/app/models.py": "ORM models",
    "backend/app/schemas.py": "Pydantic schemas",
    "backend/app/routers/__init__.py": "routers package",
    "backend/app/routers/music.py": "search/download endpoints",
    "backend/app/routers/analytics.py": "charts endpoint",
    "backend/app/services/__init__.py": "services package",
    "backend/app/services/ytdlp_service.py": "YouTube download service",
    "backend/app/services/genius_service.py": "Genius API service",
    "backend/Dockerfile": "Docker container",
    
    # Bot
    "bot/requirements.txt": "dependencies",
    "bot/.env": "configuration",
    "bot/__init__.py": "package",
    "bot/main.py": "bot entry point",
    "bot/config.py": "bot settings",
    "bot/handlers/__init__.py": "handlers package",
    "bot/handlers/commands.py": "command handlers",
    "bot/handlers/search.py": "search handlers",
    "bot/Dockerfile": "Docker container",
    
    # Root
    ".gitignore": "git ignore rules",
    "docker-compose.yml": "Docker orchestration",
    "README.md": "main documentation",
    "SETUP_GUIDE.md": "setup instructions",
}

def verify_files():
    """Verify all required files exist"""
    os.chdir(BASE)
    
    missing = []
    present = []
    
    for file_path, description in REQUIRED_FILES.items():
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            present.append((file_path, size, description))
        else:
            missing.append((file_path, description))
    
    # Report
    print("=" * 70)
    print("📋 MUSIC BOT PROJECT - FILE VERIFICATION")
    print("=" * 70)
    
    if present:
        print(f"\n✅ Found {len(present)} files:")
        for file_path, size, desc in sorted(present):
            size_kb = size / 1024
            print(f"  ✓ {file_path:50} ({size_kb:7.1f} KB) - {desc}")
    
    if missing:
        print(f"\n❌ Missing {len(missing)} files:")
        for file_path, desc in sorted(missing):
            print(f"  ✗ {file_path:50} - {desc}")
        return False
    
    print("\n" + "=" * 70)
    total_size = sum(size for _, size, _ in present)
    total_size_mb = total_size / (1024 * 1024)
    print(f"✅ ALL FILES VERIFIED! Total size: {total_size_mb:.2f} MB")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = verify_files()
    exit(0 if success else 1)

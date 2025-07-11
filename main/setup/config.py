# main/setup/config.py
from pathlib import Path
import environ

def get_env_path():
    """Return correct .env path based on execution context"""
    base_dir = Path(__file__).resolve().parent.parent.parent
    possible_paths = [
        base_dir / 'main' / 'setup' / '.env',  # For manage.py execution
        base_dir / '.env',                      # Alternative location
        Path.cwd() / '.env'                     # Current directory
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    return None

def load_env():
    env = environ.Env()
    env_path = get_env_path()
    if env_path:
        print(f"Loading .env from: {env_path}")
        env.read_env(env_path)
    else:
        print("Warning: No .env file found")
    return env
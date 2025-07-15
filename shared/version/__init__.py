import sys
from pathlib import Path

def get_project_version() -> str:
    VERSION_FILE = Path(__file__).parent.parent.parent / 'version.txt'
    try:
        with open(VERSION_FILE, 'r') as vf:
            line = vf.read().strip()
        if line.startswith('version='):
            version = line.split('=', 1)[1]
        else:
            version = line
        if not version:
            raise ValueError('version.txt is empty or invalid')
        return version
    except Exception as e:
        print(f"[zorglub-ai] WARNING: version.txt missing or invalid: {e}", file=sys.stderr)
        return 'unknown'

"""Root conftest — makes project root importable without pip install."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

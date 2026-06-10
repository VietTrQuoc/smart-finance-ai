"""Run the local dashboard server."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.api.server import main  # noqa: E402


if __name__ == "__main__":
    main()

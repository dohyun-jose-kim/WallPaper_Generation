"""Compatibility entry point for the preserved comparison commands."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wallpaper_engine.image_preparation import *  # noqa: F403

if __name__ == '__main__':
    raise SystemExit(main())

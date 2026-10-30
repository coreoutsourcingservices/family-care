"""Run separately alongside production WSGI workers, or use --once for one batch."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from doctor.push_worker import run

if __name__ == '__main__':
    run(create_app(), once='--once' in sys.argv)

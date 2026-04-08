"""Run the periodic scheduler for the collection agent.

Usage:
  python demo/run_scheduler.py

The scheduler reads `config.yaml` for `run_every_minutes` and sources.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from watcher.scheduler import start_scheduler


def main():
    start_scheduler(None)


if __name__ == "__main__":
    main()

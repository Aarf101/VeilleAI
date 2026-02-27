"""Simple Scheduler Agent for the orchestrated pipeline.

Architecture:
    SchedulerAgent
        ↓
    OrchestratorWithChromaDB
        ├── Collector
        ├── Filter
        ├── Analysis
        └── Synthesizer

This agent runs the full pipeline at a fixed interval using only the
Python standard library (no APScheduler or external dependencies).

Default interval: every 6 hours.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


# Ensure project root is on PYTHONPATH so we can import the orchestrator.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from QUICK_DEMO_CHROMADB import OrchestratorWithChromaDB  # type: ignore


class SchedulerAgent:
    """Scheduler that periodically runs the orchestrated multi-agent pipeline.

    Uses only the Python standard library:
    - time.sleep for waiting between runs
    - KeyboardInterrupt (Ctrl+C) to stop.
    """

    def __init__(
        self,
        interval_hours: float = 6.0,
        db_path: str = "watcher.db",
        chroma_dir: str = "chroma_data",
        filter_threshold: float = 0.28,
        novelty_threshold: float = 0.75,
        min_novel_for_synthesis: int = 1,
    ) -> None:
        self.interval_seconds = max(60.0, interval_hours * 3600.0)
        self.db_path = db_path
        self.chroma_dir = chroma_dir
        self.filter_threshold = filter_threshold
        self.novelty_threshold = novelty_threshold
        self.min_novel_for_synthesis = min_novel_for_synthesis

    def run_once(self) -> Optional[dict]:
        """Run a single end-to-end orchestration cycle."""
        print("\n" + "=" * 80)
        print(
            f"[SchedulerAgent] Starting pipeline run at "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print("=" * 80)

        orchestrator = OrchestratorWithChromaDB(
            db_path=self.db_path,
            chroma_dir=self.chroma_dir,
        )

        results = orchestrator.run(
            filter_threshold=self.filter_threshold,
            novelty_threshold=self.novelty_threshold,
            min_novel_for_synthesis=self.min_novel_for_synthesis,
        )

        print(
            f"[SchedulerAgent] Run finished at "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return results

    def run_forever(self) -> None:
        """Run the pipeline at a fixed interval until interrupted."""
        print(
            f"[SchedulerAgent] Starting periodic execution every "
            f"{self.interval_seconds / 3600.0:.2f} hours"
        )
        try:
            while True:
                start = time.time()
                try:
                    self.run_once()
                except Exception as exc:  # pragma: no cover - defensive logging
                    print(f"[SchedulerAgent] ERROR during run: {exc}")

                elapsed = time.time() - start
                sleep_for = max(0.0, self.interval_seconds - elapsed)
                print(
                    f"[SchedulerAgent] Sleeping for "
                    f"{sleep_for / 3600.0:.2f} hours "
                    f"({sleep_for:.0f} seconds) before next run..."
                )
                time.sleep(sleep_for)
        except KeyboardInterrupt:
            print("\n[SchedulerAgent] Stopped by user (Ctrl+C). Exiting.")


def main() -> None:
    """Entry point to start the SchedulerAgent with default parameters."""
    agent = SchedulerAgent(interval_hours=6.0)
    agent.run_forever()


if __name__ == "__main__":
    main()


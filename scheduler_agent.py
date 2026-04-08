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

from run_full_pipeline import run_pipeline


class SchedulerAgent:
    """Scheduler that runs the orchestrated multi-agent pipeline based on config.yaml."""

    def __init__(self) -> None:
        self.config = self.load_config()

    def load_config(self) -> dict:
        import yaml
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def run_once(self) -> Optional[dict]:
        """Run a single end-to-end orchestration cycle."""
        print("\n" + "=" * 80)
        print(
            f"[SchedulerAgent] Starting pipeline run at "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print("=" * 80)

        try:
            run_pipeline(self.config)
            results = {"status": "success"}
        except Exception as e:
            print(f"[SchedulerAgent] Pipeline execution failed: {e}")
            results = {"status": "error", "error": str(e)}

        print(
            f"[SchedulerAgent] Run finished at "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return results

    def run_forever(self) -> None:
        """Run the pipeline based on the configured schedule mode."""
        mode = self.config.get("schedule_mode", "interval")
        print(f"[SchedulerAgent] Starting in {mode.upper()} mode")
        
        try:
            if mode == "interval":
                minutes = self.config.get("schedule_interval_minutes", 60)
                interval_seconds = max(60.0, minutes * 60.0)
                print(f"[SchedulerAgent] Running every {minutes} minutes")
                
                while True:
                    start = time.time()
                    try:
                        self.run_once()
                    except Exception as exc:
                        print(f"[SchedulerAgent] ERROR during run: {exc}")

                    elapsed = time.time() - start
                    sleep_for = max(0.0, interval_seconds - elapsed)
                    print(
                        f"[SchedulerAgent] Sleeping for "
                        f"{sleep_for / 3600.0:.2f} hours "
                        f"({sleep_for:.0f} seconds) before next run..."
                    )
                    time.sleep(sleep_for)
                    
            elif mode == "fixed_hour":
                import schedule
                hours = self.config.get("schedule_fixed_hours", [])
                if not hours:
                    print("[SchedulerAgent] No fixed hours specified! Exiting.")
                    return
                for t in hours:
                    schedule.every().day.at(t).do(self.run_once)
                    print(f"[SchedulerAgent] Scheduled daily run at {t}")
                    
                while True:
                    schedule.run_pending()
                    time.sleep(30)
                    
            elif mode == "specific":
                dt_str = self.config.get("schedule_specific_datetime", "")
                if not dt_str:
                    print("[SchedulerAgent] No specific datetime specified! Exiting.")
                    return
                target = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                print(f"[SchedulerAgent] Scheduled one-time run at {dt_str}")
                
                while datetime.now() < target:
                    time.sleep(30)
                
                try:
                    self.run_once()
                except Exception as exc:
                    print(f"[SchedulerAgent] ERROR during run: {exc}")
                print("[SchedulerAgent] One-time run completed. Exiting.")
                
        except KeyboardInterrupt:
            print("\n[SchedulerAgent] Stopped by user (Ctrl+C). Exiting.")


def main() -> None:
    """Entry point to start the SchedulerAgent."""
    agent = SchedulerAgent()
    agent.run_forever()


if __name__ == "__main__":
    main()


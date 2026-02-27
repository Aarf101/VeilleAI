"""Scheduler for periodic FULL PIPELINE execution using APScheduler.

This module schedules the complete multi-agent workflow:
Collection → Filtering → Analysis → Synthesis → Export

Runs at configurable intervals (daily, weekly, monthly).
"""
from __future__ import annotations
from typing import Any
import signal
import time
import logging
import subprocess
import sys
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from watcher import config as _config

LOG = logging.getLogger("watcher.scheduler")


def _run_full_pipeline(cfg: dict) -> dict:
    """
    Execute the complete multi-agent pipeline.
    
    Returns:
        dict: Pipeline results with counts
    """
    LOG.info("="*70)
    LOG.info("Starting FULL PIPELINE execution")
    LOG.info("="*70)
    
    try:
        # Get project root
        project_root = Path(__file__).parent.parent
        pipeline_script = project_root / "run_full_pipeline.py"
        
        # Run the full pipeline script
        result = subprocess.run(
            [sys.executable, str(pipeline_script)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            LOG.info("Pipeline completed successfully")
            LOG.info(result.stdout)
            
            # Parse output for stats
            collected = filtered = analyzed = 0
            for line in result.stdout.split('\n'):
                if 'Collected' in line and 'items' in line:
                    try:
                        collected = int(line.split()[1])
                    except:
                        pass
                if 'Filtered' in line and 'items' in line:
                    try:
                        filtered = int(line.split()[1])
                    except:
                        pass
                if 'Analyzed' in line and 'items' in line:
                    try:
                        analyzed = int(line.split()[1])
                    except:
                        pass
            
            return {
                'status': 'success',
                'collected': collected,
                'filtered': filtered,
                'analyzed': analyzed
            }
        else:
            LOG.error(f"Pipeline failed with exit code {result.returncode}")
            LOG.error(result.stderr)
            return {'status': 'error', 'error': result.stderr}
            
    except subprocess.TimeoutExpired:
        LOG.error("Pipeline execution timed out after 10 minutes")
        return {'status': 'error', 'error': 'Timeout'}
    except Exception as e:
        LOG.exception(f"Pipeline execution failed: {e}")
        return {'status': 'error', 'error': str(e)}


def start_scheduler(cfg_path: str | None = None) -> None:
    """
    Start the scheduler for periodic full pipeline execution.
    
    Frequency is controlled by 'run_every_minutes' in config.yaml:
    - 1440 = daily (24 hours)
    - 10080 = weekly (7 days)
    - 20160 = bi-weekly (14 days)
    - 43200 = monthly (30 days)
    """
    cfg = _config.load_config(cfg_path) if cfg_path else _config.load_config()
    if not cfg:
        cfg = _config.sample_default()

    # period in minutes (default daily)
    minutes = int(cfg.get("run_every_minutes", 24 * 60))

    scheduler = BackgroundScheduler()

    # Schedule the FULL PIPELINE execution
    scheduler.add_job(
        lambda: _run_full_pipeline(cfg), 
        "interval", 
        minutes=minutes, 
        id="full_pipeline_job"
    )

    LOG.info("="*70)
    LOG.info("FULL PIPELINE SCHEDULER STARTED")
    LOG.info(f"Running complete workflow every {minutes} minutes ({minutes/60:.1f} hours)")
    LOG.info("Pipeline includes: Collection → Filtering → Analysis → Synthesis")
    LOG.info("="*70)
    
    scheduler.start()

    # Run an initial immediate pass
    try:
        LOG.info("Running initial pipeline execution...")
        _run_full_pipeline(cfg)
    except Exception:
        LOG.exception("Initial pipeline execution failed")

    # Wait until interrupted
    def _stop(signum, frame):
        LOG.info("Shutting down full pipeline scheduler")
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        LOG.info("Scheduler interrupted, cleaning up...")
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass

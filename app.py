"""
Flask backend — dashboard + API + background scheduler.
Starts daily scheduled analysis automatically.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

import config
from scheduler import create_scheduler, daily_job, run_analysis_for_stock

# ── Logging ──────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(config.LOG_DIR, "app.log"), encoding="utf-8"
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("app")

# ── Flask app ────────────────────────────────────
app = Flask(__name__, static_folder=".")

# ── Scheduler ────────────────────────────────────
_scheduler = None
_last_run_info = {
    "status": "not run yet",
    "time": None,
    "stocks_ok": 0,
    "stocks_total": 0,
}


def _track_daily_job():
    """Wrap daily_job to track execution status."""
    global _last_run_info
    _last_run_info["time"] = datetime.now().isoformat()
    try:
        result = daily_job()
        _last_run_info["status"] = "success"
        _last_run_info["stocks_ok"] = result.get("stocks_ok", 0)
        _last_run_info["stocks_total"] = result.get("stocks_total", 0)
    except Exception as exc:
        _last_run_info["status"] = f"failed: {exc}"
        _last_run_info["stocks_ok"] = 0
        _last_run_info["stocks_total"] = 0
        logger.exception("Scheduled job failed")


def start_scheduler():
    """Start the background scheduler."""
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = create_scheduler()
    _scheduler.remove_job("daily_analysis")
    _scheduler.add_job(
        _track_daily_job,
        trigger="cron",
        hour=config.SCHEDULE_TIME.hour,
        minute=config.SCHEDULE_TIME.minute,
        id="daily_analysis",
        name="Daily Strategy Analysis",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Background scheduler started")


# ── Routes: static files ─────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "portfolio_dashboard.html")


@app.route("/<path:path>")
def serve_static(path):
    unsafe = path.startswith((".", "venv", "__pycache__"))
    if unsafe:
        return jsonify({"error": "forbidden"}), 403
    return send_from_directory(".", path)


# ── Routes: API ──────────────────────────────────
@app.route("/api/status")
def api_status():
    """Return scheduler and service status."""
    jobs = []
    if _scheduler:
        for job in _scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            })
    return jsonify({
        "service": "running",
        "scheduler": "running" if _scheduler and _scheduler.running else "stopped",
        "jobs": jobs,
        "last_analysis": _last_run_info,
        "timezone": config.SCHEDULE_TIMEZONE,
        "server_time": datetime.now().isoformat(),
    })


@app.route("/api/results")
def api_results_list():
    """List all saved analysis result files."""
    files = sorted(
        Path(config.RESULT_DIR).glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    results = []
    for f in files[:50]:
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            results.append({
                "file": f.name,
                "stock_code": data.get("stock_code"),
                "stock_name": data.get("stock_name"),
                "run_at": data.get("run_at"),
                "best_strategy": data.get("best_strategy"),
                "best_return": data.get("best_return"),
            })
        except Exception:
            pass
    return jsonify({"count": len(results), "results": results})


@app.route("/api/results/<stock_code>")
def api_results_stock(stock_code: str):
    """Get the latest analysis result for a specific stock."""
    pattern = f"{stock_code}_*.json"
    files = sorted(
        Path(config.RESULT_DIR).glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        return jsonify({"error": f"no results found for {stock_code}"}), 404

    with open(files[0], encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)


@app.route("/api/run", methods=["POST"])
def api_trigger_analysis():
    """Manually trigger analysis (optionally for a single stock)."""
    body = request.get_json(silent=True) or {}
    stock_code = body.get("stock_code", "").strip()

    if stock_code:
        stock_name = body.get("stock_name", stock_code)
        result = run_analysis_for_stock(stock_code, stock_name)
        if result is None:
            return jsonify({"error": f"analysis failed for {stock_code}"}), 500
        return jsonify({"status": "completed", "result": result})
    else:
        _track_daily_job()
        return jsonify(_last_run_info)


# ── Lifecycle ────────────────────────────────────
_scheduler_started = False


def _init_scheduler_if_needed():
    global _scheduler_started
    if not _scheduler_started:
        _scheduler_started = True
        start_scheduler()


# ── Entry point ──────────────────────────────────
if __name__ == "__main__":
    _init_scheduler_if_needed()
    print(f"Service starting: http://localhost:{config.FLASK_PORT}")
    print(f"Dashboard   : http://localhost:{config.FLASK_PORT}/")
    print(f"API Status  : http://localhost:{config.FLASK_PORT}/api/status")
    print(f"Daily job at: {config.SCHEDULE_TIME.hour:02d}:{config.SCHEDULE_TIME.minute:02d} ({config.SCHEDULE_TIMEZONE})")
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
    )

"""
Background Scheduler — runs daily quantitative analysis and saves results.
Uses APScheduler, integrated into the same Flask process.
"""
import json
import logging
import os
import sys
import time
from datetime import datetime, date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from data_fetcher import TWSEDataFetcher
from strategies import get_all_strategies
from optimizer import StrategyComparator

# ── Logging ──────────────────────────────────────
logger = logging.getLogger("scheduler")
logger.setLevel(getattr(logging, config.LOG_LEVEL))

fh = logging.FileHandler(
    os.path.join(config.LOG_DIR, "scheduler.log"), encoding="utf-8"
)
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(fh)

sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(sh)


def run_analysis_for_stock(stock_code: str, stock_name: str) -> dict | None:
    """
    Run full strategy comparison for a single stock.
    Returns a result dict or None on failure.
    """
    logger.info(f"Analyzing {stock_name} ({stock_code}) ...")

    try:
        fetcher = TWSEDataFetcher()
        df = fetcher.get_historical_data_cached(stock_code, years=config.YEARS_BACK)

        if df is None or len(df) < 100:
            logger.warning(f"{stock_code}: insufficient data, skipping")
            return None

        strategies = get_all_strategies()
        comparator = StrategyComparator(
            df, strategies, initial_cash=config.INITIAL_CASH
        )
        comparator.run_all()
        comparison_df = comparator.compare()

        if comparison_df.empty:
            logger.warning(f"{stock_code}: all strategies failed")
            return None

        results = comparison_df.to_dict(orient="records")
        best = results[0] if results else {}

        summary = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "run_at": datetime.now().isoformat(),
            "data_start": str(df.index[0].date()),
            "data_end": str(df.index[-1].date()),
            "trading_days": len(df),
            "best_strategy": best.get("Strategy", ""),
            "best_return": best.get("Total_Return", 0),
            "strategies": results,
        }

        out_path = os.path.join(
            config.RESULT_DIR, f"{stock_code}_{date.today().isoformat()}.json"
        )
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(
            f"{stock_name} ({stock_code}) done — "
            f"best: {best.get('Strategy')} "
            f"return: {best.get('Total_Return', 0):.2%}"
        )
        return summary

    except Exception:
        logger.exception(f"Unexpected error analyzing {stock_code}")
        return None


def daily_job() -> dict:
    """Main scheduled job: analyze all configured stocks. Returns summary dict."""
    logger.info("=" * 60)
    logger.info("Daily analysis started")
    total = len(config.SCHEDULE_STOCKS)
    success = 0
    for stock in config.SCHEDULE_STOCKS:
        result = run_analysis_for_stock(stock["code"], stock["name"])
        if result:
            success += 1
        time.sleep(5)  # 避免 TWSE 速率限制
    logger.info(f"Daily analysis done — {success}/{total} OK")
    logger.info("=" * 60)
    return {"stocks_ok": success, "stocks_total": total}


def create_scheduler() -> BackgroundScheduler:
    """Create and return a configured BackgroundScheduler."""
    scheduler = BackgroundScheduler(
        timezone=config.SCHEDULE_TIMEZONE,
        job_defaults={"misfire_grace_time": 900},
    )

    scheduler.add_job(
        daily_job,
        trigger=CronTrigger(
            hour=config.SCHEDULE_TIME.hour,
            minute=config.SCHEDULE_TIME.minute,
        ),
        id="daily_analysis",
        name="Daily Strategy Analysis",
        replace_existing=True,
    )

    logger.info(
        f"Scheduler ready: daily at "
        f"{config.SCHEDULE_TIME.hour:02d}:{config.SCHEDULE_TIME.minute:02d} "
        f"({config.SCHEDULE_TIMEZONE})"
    )
    return scheduler


def run_once():
    """Trigger a one-shot analysis immediately (for manual/testing use)."""
    logger.info("Manual one-shot analysis triggered")
    daily_job()

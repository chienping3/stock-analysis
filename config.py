"""
集中設定檔 — 所有可調參數與排程規則
"""
import os
from datetime import time

# ── 路徑 ──────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULT_DIR = os.path.join(BASE_DIR, "results")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ── 回測預設值 ────────────────────────────────────
INITIAL_CASH = 1_000_000       # 初始資金
COMMISSION = 0.001425          # 手續費 0.1425%
TAX = 0.003                    # 證交稅 0.3%
YEARS_BACK = 3                 # 預設回測年數

# ── TWSE 數據快取 ──────────────────────────────────
CACHE_TTL_HOURS = 6            # 快取有效時數（超過後重新抓取）

# ── 排程設定 ──────────────────────────────────────
# 每日定時分析，時間以 24 小時制表示
# 台股收盤 13:30，給資料更新緩衝，設定 14:30 執行
SCHEDULE_TIME = time(14, 30)   # 每天幾點執行分析
SCHEDULE_TIMEZONE = "Asia/Taipei"

# 排程要分析的股票清單
SCHEDULE_STOCKS = [
    {"code": "2330", "name": "台積電"},
    {"code": "0050", "name": "元大台灣50"},
    {"code": "2317", "name": "鴻海"},
    {"code": "2454", "name": "聯發科"},
    {"code": "2308", "name": "台達電"},
]

# ── Flask ─────────────────────────────────────────
FLASK_HOST = "0.0.0.0"
FLASK_PORT = int(os.environ.get("PORT", 8080))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

# ── 日誌 ──────────────────────────────────────────
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

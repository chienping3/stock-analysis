# Handoff — 2026-06-04 部署與修正

## 目標
將台灣股市量化分析系統部署到外網，修正排程相關 bug。

## 完成

### GitHub
- Repo: https://github.com/chienping3/stock-analysis
- 分支: main
- 3 次 commit: 初始匯入 → fix stock counts bug → fix TWSE rate limiting

### 部署
- Railway 試用期已到期，服務暫停
- 驗證過的三個端點均正常：`/` `/api/status` `/api/results` `/api/run`
- 下次可選 Fly.io（免費）或 Railway 付費

### Bug 修復 (scheduler.py)
- `daily_job()` 改為回傳 `{"stocks_ok": N, "stocks_total": N}`，`app.py` 的 `_track_daily_job` 正確接收
- `run_analysis_for_stock()` 改用 `get_historical_data_cached()`（快取機制減少 TWSE 請求）
- 股票間隔從無 → 2s → 5s（避免 TWSE 速率限制）

### 股票清單
在 `config.py` 的 `SCHEDULE_STOCKS`：2330 台積電、0050 元大台灣50、2317 鴻海、2454 聯發科、2308 台達電

## 架構理解
- `portfolio_dashboard.html` 是**純前端模擬**（FBM + Jump Diffusion），沒有串後端
- 後端 Flask + APScheduler 用真實 TWSE/Yahoo Finance 資料
- 兩套獨立系統，尚未串接

## 待辦
- [ ] 選擇新部署平台（Fly.io 推薦）並上線
- [ ] 驗證延遲 5s 後 5 隻股票全過
- [ ] 可選：儀表板串接真實後端 API

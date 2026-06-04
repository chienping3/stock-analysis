# 雲端部署指南

本專案已完整 Docker 化，可一鍵部署到任何支援 Docker 的平台。

---

## 方案 A：Railway（推薦 — 最簡單）

Railway 免費額度 $5/月，這個專案用量約 $2-3/月，等於**免費**。

### 步驟（全程 5 分鐘）

1. **把專案推上 GitHub**
   ```bash
   git init
   git add .
   git commit -m "ready for deploy"
   git remote add origin https://github.com/你的帳號/stock-analysis.git
   git push -u origin main
   ```

2. **連到 [railway.com](https://railway.com)** → 用 GitHub 登入

3. **New Project → Deploy from GitHub repo** → 選你的 repo

4. Railway 自動偵測 `Dockerfile`，直接點 **Deploy**

5. 部署完成後，在 Settings → Networking 會看到公開網址：
   ```
   https://stock-analysis.up.railway.app
   ```

6. **(重要)** 點一下 **Generate Domain** 取得固定網址

完成。儀表板 24 小時運作，每天 14:30 自動分析。

### Railway 環境變數（可自行調整）

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `PORT` | `8080` | Railway 會自動覆蓋 |
| `FLASK_DEBUG` | `0` | 正式環境關閉 |
| `LOG_LEVEL` | `INFO` | 日誌等級 |
| `TZ` | `Asia/Taipei` | 排程時區 |

---

## 方案 B：Docker 自架（有 NAS / VPS 的話）

```bash
# 在本機或 VPS 上
docker compose up -d

# 查看狀態
docker compose ps

# 查看日誌
docker compose logs -f
```

公開到外網需自行設定 Nginx reverse proxy + Let's Encrypt。

---

## 方案 C：Fly.io（亞洲節點）

```bash
# 安裝 flyctl
iwr https://fly.io/install.ps1 -useb | iex   # Windows
curl -L https://fly.io/install.sh | sh         # Mac/Linux

# 登入
fly auth signup

# 部署（自動偵測 Dockerfile）
fly launch
```

免費額度：3 個 shared VM，選 `hkg` (香港) 或 `sin` (新加坡) 區域，台灣連線延遲最低。

---

## 部署後驗證

打開瀏覽器連到網址，檢查：

| 端點 | 應回傳 |
|------|--------|
| `/` | 儀表板頁面 |
| `/api/status` | `"service": "running"`, `"scheduler": "running"` |
| `/api/results` | `[]`（尚無分析結果） |

手動觸發一次分析確認功能正常：
```bash
curl -X POST https://你的網址/api/run
```

---

## 成本預估

| 平台 | 月費 | 備註 |
|------|------|------|
| Railway | ~$2-3（免費額度內） | 最推薦 |
| Fly.io | 免費 | 需 CLI，3 VM 額度 |
| Render | 免費 | 但 15 分鐘無流量會休眠，排程會失效 ❌ |
| Google Cloud Run | ~$0-1 | 冷啟動較慢 |

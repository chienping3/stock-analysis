# 📊 台灣股市量化分析系統

一個完整的台灣股市量化分析工具，包含策略回測、技術分析、投資組合管理，並提供手機友善的網頁介面。

## ✨ 功能特色

### 📈 策略回測
- **9種策略**：均線交叉、RSI、布林帶、及高勝率基本面+技術面策略
- **兩種資金管理模式**：等權重分配 / 共享資金池（真實交易）
- **完整回測指標**：總報酬、超額報酬、最大回撤、勝率、交易次數

### 💼 投資組合管理
- 支援100+熱門台灣股票
- 可自訂基準價格（更新為當前真實股價）
- 可調整持股權重
- 一鍵添加熱門股票

### 🔬 價格模擬模型
使用金融工程等級的專業模型：
- **Fractional Brownian Motion** (分數布朗運動) - 具有Hurst指數，趨勢延續性
- **Jump Diffusion** (跳躍擴散) - 模擬跳空事件
- **Poisson Process** (泊松過程) - 隨機跳躍發生

### 📱 手機友善介面
- 響應式設計，完美支援手機、平板、電腦
- 深色介面，夜間使用不傷眼

## 🚀 快速開始

### 方式一：Windows 一鍵啟動（推薦）

1. 雙擊 `啟動.bat`
2. 等待自動安裝相依套件
3. 瀏覽器會自動打開 `http://localhost:8080`

### 方式二：Docker 容器（最簡單）

```bash
# 構建並啟動
docker-compose up -d

# 訪問 http://localhost:8080
```

### 方式三：手動啟動

#### Windows
```bash
# 建立虛擬環境
python -m venv venv

# 啟用虛擬環境
venv\Scripts\activate

# 安裝相依
pip install -r requirements-light.txt

# 啟動服務
python app.py
```

#### Linux/Mac
```bash
# 建立虛擬環境
python3 -m venv venv

# 啟用虛擬環境
source venv/bin/activate

# 安裝相依
pip install -r requirements-light.txt

# 啟動服務
python app.py
```

## 📱 手機使用

啟動服務後，在同一區網內：

1. 打開手機瀏覽器
2. 輸入 `http://你的電腦IP:8080`
3. 即可在手機上操作

如何找電腦IP？
- Windows: 打開 cmd 輸入 `ipconfig`，找 IPv4 位址
- Mac/Linux: 輸入 `ifconfig`

## 📂 專案結構

```
Stock_analysis/
├── portfolio_dashboard.html  # 主要Dashboard（手機優化）
├── app.py                     # Flask 後端服務
├── requirements-light.txt     # 輕量版相依（只有Dashboard）
├── requirements.txt           # 完整版相依（含所有分析）
├── 啟動.bat                   # Windows 一鍵啟動
├── 啟動.sh                    # Linux/Mac 啟動腳本
├── Dockerfile                 # Docker 建置檔
├── docker-compose.yml         # Docker Compose 設定
├── strategies.py              # 策略庫
├── backtest.py                # 回測引擎
├── data_fetcher.py            # 數據獲取
├── twse_stock_analyzer.py     # 原始分析腳本
└── README.md                  # 本說明文件
```

## 🎯 使用說明

### 1. 建立投資組合
- 點擊「熱門股票」按鈕添加
- 或手動輸入股票代碼、名稱、基準價
- 調整每支股票的權重
- 可手動更新基準價格為當前真實股價

### 2. 設定回測參數
- 回測天數（60/120/180/250天）
- 初始資金
- 資金管理模式
- 手續費率、交易稅率

### 3. 執行回測
- 點擊「🚀 執行所有策略」
- 等待回測完成
- 查看結果排名和詳細交易

### 4. 分析結果
- 看整體績效統計
- 看策略對比圖表
- 看策略排名表格
- 選擇特定策略看詳細交易

## 📊 策略說明

| 策略 | 說明 |
|------|------|
| 均線交叉(5-20) | 短期均線交叉 |
| 均線交叉(10-30) | 中期均線交叉 |
| 均線交叉(10-50) | 趨勢跟蹤 |
| 均線交叉(20-60) | 長期趨勢 |
| RSI(14,30-70) | RSI超買超賣 |
| RSI(7,25-75) | 短週期RSI |
| 基本面+技術面 | 結合趨勢、動能、突破 |

## 🔧 技術細節

### 價格模型參數
- **Hurst指數 H=0.55**：輕微趨勢延續
- **波動率 σ=1.8%**：日波動率
- **跳躍強度 λ=5%**：每日5%機率跳空
- **跳躍標準差 σ_J=3%**

### 技術指標
- SMA (簡單移動平均)
- RSI (14日)
- Bollinger Bands (20日, 2標準差)
- KD指標 (9,3,3)

## ⚠️ 免責聲明

本工具僅供學習和研究使用，不構成任何投資建議。投資有風險，入市需謹慎。

## 📝 版本資訊

- v2.0 - 2024 - 完整Dashboard、Docker支援、手機優化
- v1.0 - 2024 - 初始版本

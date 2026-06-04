# 台灣股市量化分析系統

一個完整的Python量化交易分析系統，包含數據獲取、策略實現、回測引擎和優化功能。

## 功能特色

### 1. 數據獲取
- 台灣證交所 (TWSE) 歷史數據
- Yahoo Finance 備用數據源
- 支援 OHLCV (開盤價、最高價、最低價、收盤價、成交量)
- 即時股價資訊

### 2. 交易策略
- **均線交叉策略 (MA Crossover)** - 短期均線突破長期均線
- **RSI策略** - 超買超賣訊號
- **MACD策略** - 指數平滑異同移動平均線
- **布林帶策略 (Bollinger Bands)** - 價格突破通道
- **均值回歸策略 (Mean Reversion)** - Z-score 回歸
- **組合策略** - 多策略共識

### 3. 回測引擎
- 精準計算手續費和證交稅
- 完整績效指標 (報酬率、夏普比率、最大回撤、勝率)
- 視覺化結果圖表
- 買入持有對照組

### 4. 策略優化
- 參數網格搜索
- 熱力圖視覺化
- 多策略對比分析

## 安裝

```bash
pip install -r requirements.txt
```

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `data_fetcher.py` | 數據獲取模組 |
| `strategies.py` | 交易策略實現 |
| `backtest.py` | 回測引擎 |
| `optimizer.py` | 策略優化與對比 |
| `main.py` | 主程式 (互動介面) |
| `quick_start.py` | 快速開始範例 |
| `twse_stock_analyzer.py` | 原始技術分析工具 |
| `requirements.txt` | 相依套件 |

## 使用方式

### 方式1: 使用主程式 (推薦)

```bash
python main.py
```

互動式選單提供四種模式：
1. 單一策略回測
2. 多策略對比
3. 策略參數優化
4. 完整分析

### 方式2: 快速開始範例

```bash
python quick_start.py
```

### 方式3: 程式碼呼叫

```python
from data_fetcher import TWSEDataFetcher
from strategies import MACrossoverStrategy
from backtest import Backtester

# 獲取數據
fetcher = TWSEDataFetcher()
df = fetcher.get_historical_data("2330", years=2)

# 建立策略
strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
signals = strategy.generate_signals(df)

# 回測
backtester = Backtester(initial_cash=1000000)
result = backtester.run(strategy, signals)
backtester.print_report()
backtester.plot_results(df=df)
```

## 策略詳解

### 均線交叉策略 (MA Crossover)
- **買入訊號**: 短期均線向上突破長期均線 (黃金交叉)
- **賣出訊號**: 短期均線向下跌破長期均線 (死亡交叉)
- **參數**: fast_period (短期), slow_period (長期)

### RSI策略
- **買入訊號**: RSI < 30 (超賣)
- **賣出訊號**: RSI > 70 (超買)
- **參數**: period (計算週期), oversold, overbought

### MACD策略
- **買入訊號**: MACD線向上突破訊號線 (金叉)
- **賣出訊號**: MACD線向下跌破訊號線 (死叉)
- **參數**: fast, slow, signal

### 布林帶策略
- **買入訊號**: 價格跌破下軌
- **賣出訊號**: 價格突破上軌
- **參數**: period (均線週期), std_dev (標準差倍數)

## 回測設定

- **初始資金**: 1,000,000 元
- **手續費**: 0.1425%
- **證交稅**: 0.3% (賣出時)
- **交易單位**: 整張 (1000股)

## 績效指標

| 指標 | 說明 |
|------|------|
| Total Return | 總報酬率 |
| Annual Return | 年化報酬率 |
| Max Drawdown | 最大回撤 |
| Sharpe Ratio | 夏普比率 |
| Win Rate | 勝率 |
| Buy & Hold Return | 買入持有報酬 |

## 策略優化範例

```python
from optimizer import StrategyOptimizer

optimizer = StrategyOptimizer(df, initial_cash=1000000)

# 優化均線參數
fast_range = range(3, 16, 2)
slow_range = range(10, 61, 5)
results = optimizer.optimize_ma_crossover(fast_range, slow_range)

print(results.head(10))  # 顯示前10最佳參數
optimizer.plot_optimization_heatmap('MA_Crossover')
```

## 注意事項

1. **過度擬合 (Overfitting)**: 歷史績效不保證未來表現
2. **交易成本**: 頻繁交易會侵蝕獲利
3. **風險管理**: 建議配合停損停利機制
4. **數據品質**: 確保歷史數據的正確性和完整性

## 技術棧

- Pandas - 數據處理
- NumPy - 數值計算
- Matplotlib - 視覺化
- Requests - 網路請求
- YFinance - 財經數據

## 免責聲明

本系統僅供學術研究和學習使用，不構成任何投資建議。股市有風險，投資需謹慎。

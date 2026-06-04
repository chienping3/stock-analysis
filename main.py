import pandas as pd
import numpy as np
from data_fetcher import TWSEDataFetcher
from strategies import get_all_strategies
from backtest import Backtester
from optimizer import StrategyOptimizer, StrategyComparator


def main():
    print("="*80)
    print("台灣股市量化分析系統")
    print("="*80)
    
    # 1. 獲取數據
    stock_code = input("請輸入股票代碼 (預設: 2330): ").strip() or "2330"
    years = int(input("請輸入回測年數 (預設: 3): ").strip() or "3")
    
    print(f"\n正在獲取 {stock_code} 的歷史數據...")
    fetcher = TWSEDataFetcher()
    df = fetcher.get_historical_data(stock_code, years=years)
    
    if df is None or len(df) < 100:
        print("數據獲取失敗或數據不足！")
        return
    
    print(f"\n數據時間範圍: {df.index[0]} 至 {df.index[-1]}")
    print(f"總共 {len(df)} 個交易日\n")
    
    # 2. 選擇模式
    print("請選擇操作模式:")
    print("1. 單一策略回測")
    print("2. 多策略對比")
    print("3. 策略參數優化")
    print("4. 完整分析 (包含上述所有)")
    
    mode = input("\n請輸入選擇 (1-4, 預設: 4): ").strip() or "4"
    
    initial_cash = 1000000
    
    if mode == "1":
        # 單一策略回測
        strategies = get_all_strategies()
        print("\n可用策略:")
        for i, s in enumerate(strategies, 1):
            print(f"{i}. {s.name}")
        
        choice = int(input("\n請選擇策略 (1-{}): ".format(len(strategies)))) - 1
        strategy = strategies[choice]
        
        print(f"\n開始回測策略: {strategy.name}")
        signals = strategy.generate_signals(df)
        backtester = Backtester(initial_cash=initial_cash)
        result = backtester.run(strategy, signals)
        backtester.print_report()
        backtester.plot_results(df=df)
        
    elif mode == "2":
        # 多策略對比
        strategies = get_all_strategies()
        comparator = StrategyComparator(df, strategies, initial_cash=initial_cash)
        comparator.run_all()
        comparison_df = comparator.plot_comparison()
        comparator.print_comparison_report()
        
    elif mode == "3":
        # 策略優化
        print("\n請選擇要優化的策略:")
        print("1. 均線交叉策略")
        print("2. RSI策略")
        print("3. 布林帶策略")
        
        opt_choice = input("\n請輸入選擇 (1-3): ").strip()
        
        optimizer = StrategyOptimizer(df, initial_cash=initial_cash)
        
        if opt_choice == "1":
            fast_range = list(range(3, 16, 2))
            slow_range = list(range(10, 61, 5))
            print(f"優化範圍 - 短期均線: {fast_range}, 長期均線: {slow_range}")
            results = optimizer.optimize_ma_crossover(fast_range, slow_range)
            if results is not None:
                print("\n優化結果 (前10名):")
                print(results.head(10).to_string(index=False))
                optimizer.plot_optimization_heatmap('MA_Crossover')
        
        elif opt_choice == "2":
            period_range = [7, 10, 14, 21]
            oversold_range = [20, 25, 30, 35]
            overbought_range = [65, 70, 75, 80]
            print(f"優化範圍 - 週期: {period_range}, 超賣: {oversold_range}, 超買: {overbought_range}")
            results = optimizer.optimize_rsi(period_range, oversold_range, overbought_range)
            if results is not None:
                print("\n優化結果 (前10名):")
                print(results.head(10).to_string(index=False))
                optimizer.plot_optimization_heatmap('RSI')
        
        elif opt_choice == "3":
            period_range = [10, 15, 20, 25, 30]
            std_range = [1.5, 1.8, 2.0, 2.2, 2.5]
            print(f"優化範圍 - 週期: {period_range}, 標準差倍數: {std_range}")
            results = optimizer.optimize_bollinger(period_range, std_range)
            if results is not None:
                print("\n優化結果 (前10名):")
                print(results.head(10).to_string(index=False))
                optimizer.plot_optimization_heatmap('Bollinger')
    
    else:
        # 完整分析
        print("\n" + "="*80)
        print("開始完整分析...")
        print("="*80)
        
        # 階段1: 多策略對比
        print("\n[階段 1] 多策略對比")
        print("-"*80)
        strategies = get_all_strategies()
        comparator = StrategyComparator(df, strategies, initial_cash=initial_cash)
        comparator.run_all()
        comparison_df = comparator.plot_comparison()
        comparator.print_comparison_report()
        
        # 階段2: 策略優化
        print("\n[階段 2] 策略參數優化")
        print("-"*80)
        optimizer = StrategyOptimizer(df, initial_cash=initial_cash)
        
        # 優化均線策略
        print("\n優化均線交叉策略...")
        fast_range = [3, 5, 7, 10]
        slow_range = [15, 20, 30, 50]
        ma_results = optimizer.optimize_ma_crossover(fast_range, slow_range)
        if ma_results is not None:
            best_ma = ma_results.iloc[0]
            print(f"最佳參數: Fast={best_ma['Fast_MA']}, Slow={best_ma['Slow_MA']}, 報酬={best_ma['Total_Return']:.2%}")
        
        # 優化RSI策略
        print("\n優化RSI策略...")
        rsi_results = optimizer.optimize_rsi([10, 14, 21], [25, 30, 35], [65, 70, 75])
        if rsi_results is not None:
            best_rsi = rsi_results.iloc[0]
            print(f"最佳參數: Period={best_rsi['Period']}, Oversold={best_rsi['Oversold']}, Overbought={best_rsi['Overbought']}, 報酬={best_rsi['Total_Return']:.2%}")
        
        print("\n" + "="*80)
        print("分析完成！請查看生成的圖表和CSV文件。")
        print("="*80)


if __name__ == "__main__":
    main()

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from itertools import product
from strategies import (
    MACrossoverStrategy, RSIStrategy, MACDStrategy, 
    BollingerBandsStrategy, MeanReversionStrategy
)
from backtest import Backtester


class StrategyOptimizer:
    """策略優化器"""
    
    def __init__(self, df, initial_cash=1000000):
        self.df = df
        self.initial_cash = initial_cash
        self.optimization_results = []
    
    def optimize_ma_crossover(self, fast_range, slow_range):
        """優化均線交叉策略"""
        print("正在優化均線交叉策略...")
        
        results = []
        for fast, slow in product(fast_range, slow_range):
            if fast >= slow:
                continue
            
            try:
                strategy = MACrossoverStrategy(fast, slow)
                signals = strategy.generate_signals(self.df)
                
                backtester = Backtester(initial_cash=self.initial_cash)
                result = backtester.run(strategy, signals)
                metrics = result['metrics']
                
                results.append({
                    'Fast_MA': fast,
                    'Slow_MA': slow,
                    'Total_Return': metrics['Total_Return'],
                    'Annual_Return': metrics['Annual_Return'],
                    'Max_Drawdown': metrics['Max_Drawdown'],
                    'Sharpe_Ratio': metrics['Sharpe_Ratio'],
                    'Win_Rate': metrics['Win_Rate']
                })
            except Exception as e:
                print(f"優化 MA({fast},{slow}) 失敗: {e}")
                continue
        
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values('Total_Return', ascending=False)
            self.optimization_results.append(('MA_Crossover', results_df))
            return results_df
        return None
    
    def optimize_rsi(self, period_range, oversold_range, overbought_range):
        """優化RSI策略"""
        print("正在優化RSI策略...")
        
        results = []
        for period, oversold, overbought in product(period_range, oversold_range, overbought_range):
            if oversold >= overbought:
                continue
            
            try:
                strategy = RSIStrategy(period, overbought, oversold)
                signals = strategy.generate_signals(self.df)
                
                backtester = Backtester(initial_cash=self.initial_cash)
                result = backtester.run(strategy, signals)
                metrics = result['metrics']
                
                results.append({
                    'Period': period,
                    'Oversold': oversold,
                    'Overbought': overbought,
                    'Total_Return': metrics['Total_Return'],
                    'Annual_Return': metrics['Annual_Return'],
                    'Max_Drawdown': metrics['Max_Drawdown'],
                    'Sharpe_Ratio': metrics['Sharpe_Ratio'],
                    'Win_Rate': metrics['Win_Rate']
                })
            except Exception as e:
                print(f"優化 RSI({period},{oversold},{overbought}) 失敗: {e}")
                continue
        
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values('Total_Return', ascending=False)
            self.optimization_results.append(('RSI', results_df))
            return results_df
        return None
    
    def optimize_bollinger(self, period_range, std_range):
        """優化布林帶策略"""
        print("正在優化布林帶策略...")
        
        results = []
        for period, std_dev in product(period_range, std_range):
            try:
                strategy = BollingerBandsStrategy(period, std_dev)
                signals = strategy.generate_signals(self.df)
                
                backtester = Backtester(initial_cash=self.initial_cash)
                result = backtester.run(strategy, signals)
                metrics = result['metrics']
                
                results.append({
                    'Period': period,
                    'Std_Dev': std_dev,
                    'Total_Return': metrics['Total_Return'],
                    'Annual_Return': metrics['Annual_Return'],
                    'Max_Drawdown': metrics['Max_Drawdown'],
                    'Sharpe_Ratio': metrics['Sharpe_Ratio'],
                    'Win_Rate': metrics['Win_Rate']
                })
            except Exception as e:
                print(f"優化 BB({period},{std_dev}) 失敗: {e}")
                continue
        
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values('Total_Return', ascending=False)
            self.optimization_results.append(('Bollinger', results_df))
            return results_df
        return None
    
    def get_best_parameters(self, strategy_type):
        """獲取最佳參數"""
        for name, df in self.optimization_results:
            if name == strategy_type and not df.empty:
                return df.iloc[0]
        return None
    
    def plot_optimization_heatmap(self, strategy_type):
        """繪製優化熱力圖"""
        for name, df in self.optimization_results:
            if name == strategy_type:
                fig, axes = plt.subplots(2, 2, figsize=(16, 12))
                fig.suptitle(f'{strategy_type} Strategy Optimization', fontsize=16)
                
                metrics = ['Total_Return', 'Sharpe_Ratio', 'Annual_Return', 'Win_Rate']
                
                for i, metric in enumerate(metrics):
                    ax = axes[i // 2, i % 2]
                    
                    if strategy_type == 'MA_Crossover':
                        pivot = df.pivot(index='Slow_MA', columns='Fast_MA', values=metric)
                    elif strategy_type == 'RSI':
                        pivot = df.pivot(index='Oversold', columns='Overbought', values=metric)
                    elif strategy_type == 'Bollinger':
                        pivot = df.pivot(index='Period', columns='Std_Dev', values=metric)
                    else:
                        continue
                    
                    im = ax.imshow(pivot.values, cmap='RdYlGn', aspect='auto')
                    ax.set_xticks(range(len(pivot.columns)))
                    ax.set_yticks(range(len(pivot.index)))
                    ax.set_xticklabels(pivot.columns)
                    ax.set_yticklabels(pivot.index)
                    ax.set_xlabel(pivot.columns.name)
                    ax.set_ylabel(pivot.index.name)
                    ax.set_title(metric)
                    
                    for j in range(len(pivot.index)):
                        for k in range(len(pivot.columns)):
                            if metric in ['Total_Return', 'Annual_Return', 'Win_Rate']:
                                text = f'{pivot.values[j, k]:.1%}'
                            else:
                                text = f'{pivot.values[j, k]:.2f}'
                            ax.text(k, j, text, ha='center', va='center', color='black', fontsize=8)
                    
                    plt.colorbar(im, ax=ax)
                
                plt.tight_layout()
                plt.savefig(f'{strategy_type}_optimization.png', dpi=300)
                plt.close()
                print(f"優化圖表已保存至 {strategy_type}_optimization.png")
                break


class StrategyComparator:
    """策略對比器"""
    
    def __init__(self, df, strategies, initial_cash=1000000):
        self.df = df
        self.strategies = strategies
        self.initial_cash = initial_cash
        self.results = {}
    
    def run_all(self):
        """運行所有策略"""
        print("開始對比所有策略...\n")
        
        for strategy in self.strategies:
            print(f"運行策略: {strategy.name}")
            try:
                signals = strategy.generate_signals(self.df)
                backtester = Backtester(initial_cash=self.initial_cash)
                result = backtester.run(strategy, signals)
                self.results[strategy.name] = result
                backtester.print_report()
                print()
            except Exception as e:
                print(f"策略 {strategy.name} 運行失敗: {e}\n")
    
    def compare(self):
        """對比策略結果"""
        if not self.results:
            print("警告: 沒有成功的策略結果可以對比")
            return pd.DataFrame(columns=['Strategy', 'Total_Return'])
        
        comparison = []
        
        for name, result in self.results.items():
            metrics = result['metrics']
            comparison.append({
                'Strategy': name,
                'Total_Return': metrics['Total_Return'],
                'Annual_Return': metrics['Annual_Return'],
                'Max_Drawdown': metrics['Max_Drawdown'],
                'Sharpe_Ratio': metrics['Sharpe_Ratio'],
                'Win_Rate': metrics['Win_Rate'],
                'Total_Trades': metrics['Total_Trades'],
                'Excess_Return': metrics['Total_Return'] - metrics['Buy_Hold_Return']
            })
        
        comparison_df = pd.DataFrame(comparison)
        if not comparison_df.empty:
            comparison_df = comparison_df.sort_values('Total_Return', ascending=False)
        
        return comparison_df
    
    def plot_comparison(self):
        """繪製策略對比圖"""
        comparison_df = self.compare()
        
        if comparison_df.empty:
            print("無法繪製對比圖: 沒有數據")
            return comparison_df
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 資產淨值對比
        ax1 = axes[0, 0]
        for name, result in self.results.items():
            portfolio = result['portfolio']
            normalized = portfolio['Portfolio_Value'] / self.initial_cash
            ax1.plot(portfolio.index, normalized, label=name, linewidth=2)
        
        # 買入持有
        buy_hold = (self.df['Close'] / self.df['Close'].iloc[0]).values
        ax1.plot(self.df.index, buy_hold, label='Buy & Hold', linewidth=2, linestyle='--', color='black')
        ax1.set_title('Portfolio Value Comparison (Normalized)', fontsize=14)
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True)
        
        # 總報酬率對比
        ax2 = axes[0, 1]
        strategies = comparison_df['Strategy']
        returns = comparison_df['Total_Return']
        colors = ['green' if x > 0 else 'red' for x in returns]
        bars = ax2.bar(strategies, returns, color=colors)
        ax2.axhline(y=0, color='black', linewidth=0.8)
        ax2.set_title('Total Return Comparison', fontsize=14)
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, axis='y')
        for i, (bar, ret) in enumerate(zip(bars, returns)):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                    f'{ret:.1%}', ha='center', va='bottom' if ret>0 else 'top')
        
        # 風險指標對比
        ax3 = axes[1, 0]
        x = comparison_df['Max_Drawdown'].abs()
        y = comparison_df['Total_Return']
        sizes = comparison_df['Sharpe_Ratio'].abs() * 1000
        scatter = ax3.scatter(x, y, s=sizes, alpha=0.6, c=comparison_df['Sharpe_Ratio'], cmap='RdYlGn')
        ax3.set_xlabel('Max Drawdown (Absolute)')
        ax3.set_ylabel('Total Return')
        ax3.set_title('Risk-Return Profile', fontsize=14)
        ax3.grid(True)
        plt.colorbar(scatter, ax=ax3, label='Sharpe Ratio')
        
        for i, name in enumerate(strategies):
            ax3.annotate(name, (x.iloc[i], y.iloc[i]), xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # 夏普比率和勝率
        ax4 = axes[1, 1]
        x_pos = np.arange(len(strategies))
        width = 0.35
        ax4.bar(x_pos - width/2, comparison_df['Sharpe_Ratio'], width, label='Sharpe Ratio', alpha=0.8)
        ax4.bar(x_pos + width/2, comparison_df['Win_Rate'], width, label='Win Rate', alpha=0.8)
        ax4.set_xlabel('Strategy')
        ax4.set_title('Sharpe Ratio & Win Rate', fontsize=14)
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels(strategies, rotation=45)
        ax4.legend()
        ax4.grid(True, axis='y')
        
        plt.tight_layout()
        plt.savefig('strategy_comparison.png', dpi=300)
        plt.close()
        print("策略對比圖已保存至 strategy_comparison.png")
        
        return comparison_df
    
    def print_comparison_report(self):
        """列印對比報告"""
        comparison_df = self.compare()
        
        if comparison_df.empty:
            print("\n沒有可對比的策略結果")
            return
        
        print("\n" + "="*100)
        print("策略對比總結")
        print("="*100)
        print(comparison_df.to_string(index=False))
        print("="*100)
        
        best = comparison_df.iloc[0]
        print(f"\n🏆 最佳策略: {best['Strategy']}")
        print(f"   總報酬率: {best['Total_Return']:.2%}")
        print(f"   年化報酬: {best['Annual_Return']:.2%}")
        print(f"   最大回撤: {best['Max_Drawdown']:.2%}")
        print(f"   夏普比率: {best['Sharpe_Ratio']:.2f}")
        
        comparison_df.to_csv('strategy_comparison.csv', index=False)
        print("\n對比結果已保存至 strategy_comparison.csv")

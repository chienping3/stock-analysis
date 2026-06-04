import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from datetime import datetime


class Backtester:
    """回測引擎"""
    
    def __init__(self, initial_cash=1000000, commission=0.001425, tax=0.003):
        self.initial_cash = initial_cash
        self.commission = commission  # 手續費
        self.tax = tax  # 證交稅 (賣出時)
        self.results = {}
    
    def run(self, strategy, df):
        """執行回測"""
        df = df.copy()
        
        cash = self.initial_cash
        position = 0
        portfolio_value = []
        trades = []
        entry_price = 0
        
        for i, (date, row) in enumerate(df.iterrows()):
            current_price = row['Close']
            
            # 檢查買入信號
            if row['Buy_Signal'] == 1 and position == 0:
                # 計算可買入股數 (扣除手續費)
                available_cash = cash * (1 - self.commission)
                shares = int(available_cash / current_price / 1000) * 1000  # 整張
                
                if shares > 0:
                    cost = shares * current_price
                    fee = cost * self.commission
                    total_cost = cost + fee
                    
                    cash -= total_cost
                    position = shares
                    entry_price = current_price
                    
                    trades.append({
                        'Date': date,
                        'Type': 'Buy',
                        'Price': current_price,
                        'Shares': shares,
                        'Amount': total_cost
                    })
            
            # 檢查賣出信號
            elif row['Sell_Signal'] == 1 and position > 0:
                revenue = position * current_price
                fee = revenue * self.commission
                tax_amount = revenue * self.tax
                net_revenue = revenue - fee - tax_amount
                
                cash += net_revenue
                pnl = (current_price - entry_price) * position - fee - tax_amount
                
                trades.append({
                    'Date': date,
                    'Type': 'Sell',
                    'Price': current_price,
                    'Shares': position,
                    'Amount': net_revenue,
                    'PnL': pnl
                })
                
                position = 0
                entry_price = 0
            
            # 計算資產淨值
            current_value = cash + position * current_price
            portfolio_value.append({
                'Date': date,
                'Cash': cash,
                'Position': position,
                'Portfolio_Value': current_value
            })
        
        # 最後平倉
        if position > 0:
            revenue = position * current_price
            fee = revenue * self.commission
            tax_amount = revenue * self.tax
            net_revenue = revenue - fee - tax_amount
            cash += net_revenue
            pnl = (current_price - entry_price) * position - fee - tax_amount
            
            trades.append({
                'Date': date,
                'Type': 'Sell (Final)',
                'Price': current_price,
                'Shares': position,
                'Amount': net_revenue,
                'PnL': pnl
            })
        
        # 整理結果
        portfolio_df = pd.DataFrame(portfolio_value).set_index('Date')
        trades_df = pd.DataFrame(trades) if trades else None
        
        # 計算績效指標
        metrics = self.calculate_metrics(portfolio_df, df, trades_df)
        
        result = {
            'strategy': strategy.name,
            'portfolio': portfolio_df,
            'trades': trades_df,
            'metrics': metrics
        }
        
        self.results[strategy.name] = result
        return result
    
    def calculate_metrics(self, portfolio_df, price_df, trades_df):
        """計算回測績效指標"""
        portfolio_values = portfolio_df['Portfolio_Value'].values
        dates = portfolio_df.index
        
        # 基本指標
        total_return = (portfolio_values[-1] - self.initial_cash) / self.initial_cash
        
        # 買入持有對照
        buy_hold_return = (price_df['Close'].iloc[-1] - price_df['Close'].iloc[0]) / price_df['Close'].iloc[0]
        
        # 年化報酬率
        days = (dates[-1] - dates[0]).days
        if days > 0:
            annual_return = (1 + total_return) ** (365 / days) - 1
        else:
            annual_return = 0
        
        # 最大回撤
        cumulative_returns = portfolio_values / self.initial_cash
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 日報酬率
        daily_returns = pd.Series(portfolio_values).pct_change().dropna()
        
        # 夏普比率 (假設無風險利率為2%)
        risk_free_rate = 0.02
        if len(daily_returns) > 1 and daily_returns.std() > 0:
            sharpe_ratio = (daily_returns.mean() - risk_free_rate / 252) / daily_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 勝率
        win_rate = 0
        total_trades = 0
        if trades_df is not None and len(trades_df) > 0:
            sell_trades = trades_df[trades_df['Type'].str.startswith('Sell')]
            total_trades = len(trades_df)
            if len(sell_trades) > 0:
                win_trades = len(sell_trades[sell_trades['PnL'] > 0])
                win_rate = win_trades / len(sell_trades)
        
        return {
            'Total_Return': total_return,
            'Buy_Hold_Return': buy_hold_return,
            'Annual_Return': annual_return,
            'Max_Drawdown': max_drawdown,
            'Sharpe_Ratio': sharpe_ratio,
            'Win_Rate': win_rate,
            'Total_Trades': total_trades,
            'Final_Value': portfolio_values[-1]
        }
    
    def plot_results(self, strategy_name=None, df=None):
        """繪製回測結果"""
        if strategy_name is None:
            strategy_name = list(self.results.keys())[-1]
        
        result = self.results[strategy_name]
        portfolio_df = result['portfolio']
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # 資產淨值曲線
        axes[0].plot(portfolio_df.index, portfolio_df['Portfolio_Value'], 
                    label=strategy_name, linewidth=2)
        axes[0].axhline(y=self.initial_cash, color='r', linestyle='--', label='Initial')
        axes[0].set_title(f'{strategy_name} - Portfolio Value', fontsize=14)
        axes[0].legend()
        axes[0].grid(True)
        
        # 價格與交易點
        if df is not None:
            axes[1].plot(df.index, df['Close'], label='Price', alpha=0.7)
            
            if result['trades'] is not None and len(result['trades']) > 0:
                buy_trades = result['trades'][result['trades']['Type'].str.startswith('Buy')]
                sell_trades = result['trades'][result['trades']['Type'].str.startswith('Sell')]
                
                if len(buy_trades) > 0:
                    axes[1].scatter(buy_trades['Date'], buy_trades['Price'], 
                                  marker='^', color='g', s=100, label='Buy')
                if len(sell_trades) > 0:
                    axes[1].scatter(sell_trades['Date'], sell_trades['Price'], 
                                  marker='v', color='r', s=100, label='Sell')
            
            axes[1].set_title('Price & Trades', fontsize=14)
            axes[1].legend()
            axes[1].grid(True)
        
        plt.tight_layout()
        plt.savefig(f'{strategy_name}_backtest.png', dpi=300)
        plt.close()
        print(f"圖表已保存至 {strategy_name}_backtest.png")
    
    def print_report(self, strategy_name=None):
        """列印回測報告"""
        if strategy_name is None:
            strategy_name = list(self.results.keys())[-1]
        
        result = self.results[strategy_name]
        metrics = result['metrics']
        
        print("\n" + "="*80)
        print(f"策略回測報告 - {strategy_name}")
        print("="*80)
        print(f"初始資金: ${self.initial_cash:,.0f}")
        print(f"最終資金: ${metrics['Final_Value']:,.0f}")
        print(f"總報酬率: {metrics['Total_Return']:.2%}")
        print(f"買入持有報酬: {metrics['Buy_Hold_Return']:.2%}")
        print(f"超額報酬: {metrics['Total_Return'] - metrics['Buy_Hold_Return']:.2%}")
        print(f"年化報酬率: {metrics['Annual_Return']:.2%}")
        print(f"最大回撤: {metrics['Max_Drawdown']:.2%}")
        print(f"夏普比率: {metrics['Sharpe_Ratio']:.2f}")
        print(f"勝率: {metrics['Win_Rate']:.2%}")
        print(f"總交易次數: {metrics['Total_Trades']}")
        print("="*80)
        
        if result['trades'] is not None and len(result['trades']) > 0:
            print("\n交易記錄:")
            print(result['trades'].to_string(index=False))

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """策略基類"""
    
    def __init__(self, name):
        self.name = name
        self.signals = None
    
    @abstractmethod
    def generate_signals(self, df):
        """生成交易信號"""
        pass
    
    def get_signals(self):
        return self.signals


class MACrossoverStrategy(BaseStrategy):
    """均線交叉策略"""
    
    def __init__(self, fast_period=5, slow_period=20):
        super().__init__(f"MA{fast_period}_MA{slow_period}_Crossover")
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signals(self, df):
        df = df.copy()
        df['MA_Fast'] = df['Close'].rolling(window=self.fast_period).mean()
        df['MA_Slow'] = df['Close'].rolling(window=self.slow_period).mean()
        
        # 生成信號: 1=買入, -1=賣出, 0=持有
        df['Signal'] = 0
        df.loc[df['MA_Fast'] > df['MA_Slow'], 'Signal'] = 1
        df.loc[df['MA_Fast'] < df['MA_Slow'], 'Signal'] = -1
        
        # 只在交叉時產生信號
        df['Position'] = df['Signal'].diff()
        df['Buy_Signal'] = (df['Position'] > 0).astype(int)
        df['Sell_Signal'] = (df['Position'] < 0).astype(int)
        
        self.signals = df
        return df


class RSIStrategy(BaseStrategy):
    """RSI策略 - 超買超賣"""
    
    def __init__(self, period=14, overbought=70, oversold=30):
        super().__init__(f"RSI{period}_{oversold}_{overbought}")
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def calculate_rsi(self, prices):
        """計算RSI"""
        if len(prices) < self.period + 1:
            return [50] * len(prices)
        
        deltas = np.diff(prices)
        gains = []
        losses = []
        
        for delta in deltas:
            if delta > 0:
                gains.append(delta)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-delta)
        
        avg_gain = np.mean(gains[:self.period])
        avg_loss = np.mean(losses[:self.period])
        
        rsi_values = [50] * self.period  # 前period天設為50
        
        for i in range(self.period, len(prices)):
            if i > self.period:
                avg_gain = (avg_gain * (self.period - 1) + gains[i-1]) / self.period
                avg_loss = (avg_loss * (self.period - 1) + losses[i-1]) / self.period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        return rsi_values
    
    def generate_signals(self, df):
        df = df.copy()
        df['RSI'] = self.calculate_rsi(df['Close'].values)
        
        # 生成信號
        df['Signal'] = 0
        df.loc[df['RSI'] < self.oversold, 'Signal'] = 1  # 超賣買入
        df.loc[df['RSI'] > self.overbought, 'Signal'] = -1  # 超買賣出
        
        df['Buy_Signal'] = (df['Signal'] == 1).astype(int)
        df['Sell_Signal'] = (df['Signal'] == -1).astype(int)
        
        self.signals = df
        return df


class MACDStrategy(BaseStrategy):
    """MACD策略"""
    
    def __init__(self, fast=12, slow=26, signal=9):
        super().__init__(f"MACD_{fast}_{slow}_{signal}")
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def calculate_ema(self, prices, period):
        """計算EMA"""
        if len(prices) < period:
            return [np.nan] * len(prices)
        
        ema = [np.nan] * (period - 1)
        ema.append(np.mean(prices[:period]))
        
        multiplier = 2 / (period + 1)
        for i in range(period, len(prices)):
            ema.append((prices[i] * multiplier) + (ema[-1] * (1 - multiplier)))
        return ema
    
    def generate_signals(self, df):
        df = df.copy()
        prices = df['Close'].values
        
        df['EMA_Fast'] = self.calculate_ema(prices, self.fast)
        df['EMA_Slow'] = self.calculate_ema(prices, self.slow)
        df['MACD'] = df['EMA_Fast'] - df['EMA_Slow']
        
        # 處理 MACD 的 NaN 值
        macd_values = df['MACD'].fillna(0).values
        df['Signal_Line'] = self.calculate_ema(macd_values, self.signal)
        df['Histogram'] = df['MACD'] - df['Signal_Line']
        
        # 生成信號: 金叉買入, 死叉賣出
        df['Signal'] = 0
        valid_mask = df['MACD'].notna() & df['Signal_Line'].notna()
        df.loc[valid_mask & (df['MACD'] > df['Signal_Line']), 'Signal'] = 1
        df.loc[valid_mask & (df['MACD'] < df['Signal_Line']), 'Signal'] = -1
        
        df['Position'] = df['Signal'].diff()
        df['Buy_Signal'] = (df['Position'] > 0).astype(int)
        df['Sell_Signal'] = (df['Position'] < 0).astype(int)
        
        self.signals = df
        return df


class BollingerBandsStrategy(BaseStrategy):
    """布林帶策略"""
    
    def __init__(self, period=20, std_dev=2):
        super().__init__(f"BB_{period}_{std_dev}")
        self.period = period
        self.std_dev = std_dev
    
    def generate_signals(self, df):
        df = df.copy()
        df['MA'] = df['Close'].rolling(window=self.period).mean()
        df['STD'] = df['Close'].rolling(window=self.period).std()
        df['Upper_Band'] = df['MA'] + (df['STD'] * self.std_dev)
        df['Lower_Band'] = df['MA'] - (df['STD'] * self.std_dev)
        
        # 生成信號
        df['Signal'] = 0
        valid_mask = df['Lower_Band'].notna() & df['Upper_Band'].notna()
        df.loc[valid_mask & (df['Close'] < df['Lower_Band']), 'Signal'] = 1  # 跌破下軌買入
        df.loc[valid_mask & (df['Close'] > df['Upper_Band']), 'Signal'] = -1  # 突破上軌賣出
        
        df['Buy_Signal'] = (df['Signal'] == 1).astype(int)
        df['Sell_Signal'] = (df['Signal'] == -1).astype(int)
        
        self.signals = df
        return df


class MeanReversionStrategy(BaseStrategy):
    """均值回歸策略"""
    
    def __init__(self, lookback=20, entry_std=1.5, exit_std=0.5):
        super().__init__(f"MeanReversion_{lookback}_{entry_std}")
        self.lookback = lookback
        self.entry_std = entry_std
        self.exit_std = exit_std
    
    def generate_signals(self, df):
        df = df.copy()
        df['MA'] = df['Close'].rolling(window=self.lookback).mean()
        df['STD'] = df['Close'].rolling(window=self.lookback).std()
        df['Z_Score'] = (df['Close'] - df['MA']) / df['STD']
        
        signals = [0] * len(df)
        positions = [0] * len(df)
        
        position = 0
        for i in range(len(df)):
            z_score = df['Z_Score'].iloc[i]
            if pd.isna(z_score):
                signals[i] = 0
                positions[i] = position
                continue
                
            if position == 0:
                if z_score < -self.entry_std:
                    position = 1  # 買入
                    signals[i] = 1
                elif z_score > self.entry_std:
                    position = -1  # 賣出
                    signals[i] = -1
            elif position == 1:
                if z_score > -self.exit_std:
                    position = 0  # 平倉
                    signals[i] = 0
            elif position == -1:
                if z_score < self.exit_std:
                    position = 0  # 平倉
                    signals[i] = 0
            
            positions[i] = position
        
        df['Signal'] = signals
        df['Position'] = positions
        df['Buy_Signal'] = (df['Signal'] == 1).astype(int)
        df['Sell_Signal'] = (df['Signal'] == -1).astype(int)
        
        self.signals = df
        return df


class CombinedStrategy(BaseStrategy):
    """組合策略 - 多個指標共識"""
    
    def __init__(self, strategies, consensus_threshold=0.5):
        super().__init__("Combined_Strategy")
        self.strategies = strategies
        self.consensus_threshold = consensus_threshold
    
    def generate_signals(self, df):
        df = df.copy()
        signals_list = []
        
        for strategy in self.strategies:
            strat_df = strategy.generate_signals(df)
            signals_list.append(strat_df['Signal'].values)
        
        # 計算共識信號
        signals_array = np.array(signals_list)
        buy_votes = (signals_array == 1).sum(axis=0)
        sell_votes = (signals_array == -1).sum(axis=0)
        
        df['Buy_Votes'] = buy_votes
        df['Sell_Votes'] = sell_votes
        
        threshold = int(len(self.strategies) * self.consensus_threshold)
        
        df['Signal'] = 0
        df.loc[df['Buy_Votes'] >= threshold, 'Signal'] = 1
        df.loc[df['Sell_Votes'] >= threshold, 'Signal'] = -1
        
        df['Buy_Signal'] = (df['Signal'] == 1).astype(int)
        df['Sell_Signal'] = (df['Signal'] == -1).astype(int)
        
        self.signals = df
        return df


def get_all_strategies():
    """獲取所有策略實例"""
    return [
        MACrossoverStrategy(5, 20),
        MACrossoverStrategy(10, 50),
        RSIStrategy(14, 70, 30),
        MACDStrategy(12, 26, 9),
        BollingerBandsStrategy(20, 2),
        MeanReversionStrategy(20, 1.5, 0.5),
    ]

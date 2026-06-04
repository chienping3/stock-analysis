import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


def get_stock_info(stock_code):
    """
    获取台股股票信息
    """
    try:
        realtime_url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_code}.tw"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(realtime_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data.get("msgArray") and len(data["msgArray"]) > 0:
            stock_data = data["msgArray"][0]
            return stock_data
        return None
    except Exception as e:
        print(f"获取实时数据时出错: {e}")
        return None


def get_historical_data(stock_code, months=12):
    """
    获取多个月的历史数据
    """
    try:
        all_data = []
        end_date = datetime.now()
        seen_months = set()
        
        for i in range(months):
            # 正确计算每个月的日期
            check_date = end_date - timedelta(days=i*30)
            # 使用月份第一天
            query_date = check_date.replace(day=1)
            month_key = (query_date.year, query_date.month)
            
            if month_key in seen_months:
                continue
            seen_months.add(month_key)
            
            date_str = query_date.strftime("%Y%m%d")
            url = f"https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date={date_str}&stockNo={stock_code}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data"):
                        month_prices = []
                        for item in data["data"]:
                            try:
                                price = float(str(item[6]).replace(",", ""))
                                month_prices.append(price)
                            except:
                                continue
                        # 每个月的数据按日期顺序添加
                        all_data.extend(reversed(month_prices))
            except Exception as e:
                print(f"获取 {month_key} 数据时出错: {e}")
                continue
        
        # 反转顺序，使最早的数据在前，最新的数据在后
        all_data = all_data[::-1]
        print(f"成功获取 {len(all_data)} 天的历史数据")
        return all_data
    except Exception as e:
        print(f"获取历史数据时出错: {e}")
        return []


def calculate_moving_averages(prices, periods=[50, 200]):
    """
    计算移动平均线
    """
    ma_dict = {}
    for period in periods:
        if len(prices) >= period:
            ma = sum(prices[-period:]) / period
            ma_dict[f"MA{period}"] = round(ma, 2)
        else:
            ma_dict[f"MA{period}"] = None
    return ma_dict


def calculate_ema(prices, period):
    """
    计算指数移动平均线
    """
    if len(prices) < period:
        return [None] * len(prices)
    
    ema = []
    multiplier = 2 / (period + 1)
    ema.append(sum(prices[:period]) / period)
    
    for i in range(period, len(prices)):
        ema.append((prices[i] * multiplier) + (ema[-1] * (1 - multiplier)))
    
    return [None] * (period - 1) + ema


def calculate_macd(prices):
    """
    计算 MACD 指标
    """
    if len(prices) < 35:
        return None
    
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    
    macd_line = []
    for e12, e26 in zip(ema12, ema26):
        if e12 is not None and e26 is not None:
            macd_line.append(e12 - e26)
        else:
            macd_line.append(None)
    
    signal_line = []
    macd_values = [x for x in macd_line if x is not None]
    if len(macd_values) >= 9:
        signal_ema = calculate_ema(macd_values, 9)
        signal_index = 0
        for val in macd_line:
            if val is not None and signal_index < len(signal_ema):
                signal_line.append(signal_ema[signal_index])
                signal_index += 1
            else:
                signal_line.append(None)
    
    histogram = []
    for m, s in zip(macd_line, signal_line):
        if m is not None and s is not None:
            histogram.append(m - s)
        else:
            histogram.append(None)
    
    macd_data = {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram,
        "current_macd": macd_line[-1] if macd_line[-1] is not None else None,
        "current_signal": signal_line[-1] if signal_line[-1] is not None else None,
        "current_histogram": histogram[-1] if histogram[-1] is not None else None
    }
    
    if len(macd_values) >= 2 and len([x for x in signal_line if x is not None]) >= 2:
        prev_macd = macd_line[-2] if macd_line[-2] is not None else macd_line[-1]
        prev_signal = signal_line[-2] if signal_line[-2] is not None else signal_line[-1]
        curr_macd = macd_line[-1]
        curr_signal = signal_line[-1]
        
        if prev_macd and prev_signal and curr_macd and curr_signal:
            if prev_macd <= prev_signal and curr_macd > curr_signal:
                macd_data["signal"] = "金叉"
                macd_data["signal_score"] = 20
            elif prev_macd >= prev_signal and curr_macd < curr_signal:
                macd_data["signal"] = "死叉"
                macd_data["signal_score"] = -20
            elif curr_macd > curr_signal:
                macd_data["signal"] = "多头排列"
                macd_data["signal_score"] = 10
            else:
                macd_data["signal"] = "空头排列"
                macd_data["signal_score"] = -10
        else:
            macd_data["signal"] = "数据不足"
            macd_data["signal_score"] = 0
    else:
        macd_data["signal"] = "数据不足"
        macd_data["signal_score"] = 0
    
    return macd_data


def calculate_rsi(prices, period=14):
    """
    计算 RSI 指标
    """
    if len(prices) < period + 1:
        return None
    
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
    
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    rsi_values = []
    for i in range(period, len(prices)):
        if i > period:
            avg_gain = (avg_gain * (period - 1) + gains[i-1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i-1]) / period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        rsi_values.append(rsi)
    
    current_rsi = rsi_values[-1] if rsi_values else None
    
    rsi_data = {
        "rsi_values": rsi_values,
        "current_rsi": round(current_rsi, 2) if current_rsi is not None else None
    }
    
    if current_rsi is not None:
        if current_rsi > 70:
            rsi_data["signal"] = "超买"
            rsi_data["signal_score"] = -15
        elif current_rsi < 30:
            rsi_data["signal"] = "超卖"
            rsi_data["signal_score"] = 15
        elif current_rsi > 50:
            rsi_data["signal"] = "偏多"
            rsi_data["signal_score"] = 5
        else:
            rsi_data["signal"] = "偏空"
            rsi_data["signal_score"] = -5
    else:
        rsi_data["signal"] = "数据不足"
        rsi_data["signal_score"] = 0
    
    return rsi_data


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """
    计算布林带
    """
    if len(prices) < period:
        return None
    
    bands = []
    for i in range(period, len(prices) + 1):
        window = prices[i-period:i]
        sma = np.mean(window)
        std = np.std(window)
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        bands.append({
            "middle": sma,
            "upper": upper,
            "lower": lower
        })
    
    current_price = prices[-1]
    current_band = bands[-1]
    
    position = (current_price - current_band["lower"]) / (current_band["upper"] - current_band["lower"])
    
    bb_data = {
        "bands": bands,
        "current_upper": round(current_band["upper"], 2),
        "current_middle": round(current_band["middle"], 2),
        "current_lower": round(current_band["lower"], 2),
        "position": round(position, 2)
    }
    
    if position > 1:
        bb_data["signal"] = "突破上轨"
        bb_data["signal_score"] = -15
    elif position < 0:
        bb_data["signal"] = "跌破下轨"
        bb_data["signal_score"] = 15
    elif position > 0.8:
        bb_data["signal"] = "接近上轨"
        bb_data["signal_score"] = -8
    elif position < 0.2:
        bb_data["signal"] = "接近下轨"
        bb_data["signal_score"] = 8
    else:
        bb_data["signal"] = "轨道中部"
        bb_data["signal_score"] = 0
    
    return bb_data


def generate_comprehensive_analysis(stock_code, stock_info, prices, ma, macd, rsi, bb):
    """
    生成综合分析
    """
    total_score = 50
    
    if ma.get("MA50") and ma.get("MA200") and stock_info and "current_price" in stock_info:
        if stock_info["current_price"] > ma["MA50"] > ma["MA200"]:
            total_score += 15
        elif ma["MA200"] > ma["MA50"] > stock_info["current_price"]:
            total_score -= 15
        elif stock_info["current_price"] > ma["MA50"]:
            total_score += 5
        elif stock_info["current_price"] < ma["MA50"]:
            total_score -= 5
    
    if macd:
        total_score += macd.get("signal_score", 0)
    
    if rsi:
        total_score += rsi.get("signal_score", 0)
    
    if bb:
        total_score += bb.get("signal_score", 0)
    
    if stock_info and stock_info.get("change_percent"):
        if stock_info["change_percent"] > 3:
            total_score += 10
        elif stock_info["change_percent"] < -3:
            total_score -= 10
    
    total_score = max(0, min(100, total_score))
    
    if total_score >= 70:
        recommendation = "买入"
    elif total_score >= 40:
        recommendation = "持有"
    else:
        recommendation = "卖出"
    
    return {
        "score": total_score,
        "recommendation": recommendation
    }


def generate_chinese_report(stock_code, stock_data, ma, macd, rsi, bb, analysis):
    """
    生成中文分析报告
    """
    report = []
    report.append("=" * 60)
    report.append(f"股票分析报告 - {stock_data.get('stock_name', stock_code)} ({stock_code})")
    report.append("=" * 60)
    report.append(f"分析时间: {stock_data.get('timestamp')}")
    report.append("")
    
    report.append("【基本信息】")
    report.append(f"当前价格: {stock_data.get('current_price', 'N/A')}")
    report.append(f"涨跌额: {stock_data.get('change_amount', 'N/A')}")
    report.append(f"涨跌幅: {stock_data.get('change_percent', 'N/A')}%")
    report.append(f"成交量: {stock_data.get('volume', 'N/A')}")
    report.append(f"MA50: {ma.get('MA50', 'N/A')}")
    report.append(f"MA200: {ma.get('MA200', 'N/A')}")
    report.append("")
    
    report.append("【技术指标分析】")
    
    if macd:
        report.append(f"MACD: {macd.get('signal', 'N/A')}")
        report.append(f"  MACD值: {round(macd.get('current_macd', 0), 4) if macd.get('current_macd') else 'N/A'}")
        report.append(f"  信号线: {round(macd.get('current_signal', 0), 4) if macd.get('current_signal') else 'N/A'}")
    else:
        report.append("MACD: 数据不足")
    
    if rsi:
        report.append(f"RSI(14): {rsi.get('signal', 'N/A')} - {rsi.get('current_rsi', 'N/A')}")
    else:
        report.append("RSI: 数据不足")
    
    if bb:
        report.append(f"布林带: {bb.get('signal', 'N/A')}")
        report.append(f"  上轨: {bb.get('current_upper', 'N/A')}")
        report.append(f"  中轨: {bb.get('current_middle', 'N/A')}")
        report.append(f"  下轨: {bb.get('current_lower', 'N/A')}")
        report.append(f"  位置: {bb.get('position', 'N/A')}")
    else:
        report.append("布林带: 数据不足")
    
    report.append("")
    report.append("【综合评估】")
    report.append(f"综合评分: {analysis.get('score', 'N/A')}/100")
    report.append(f"投资建议: {analysis.get('recommendation', 'N/A')}")
    report.append("=" * 60)
    
    return "\n".join(report)


def analyze_stock(stock_code):
    """
    分析股票并返回完整数据
    """
    stock_info = get_stock_info(stock_code)
    historical_prices = get_historical_data(stock_code)
    
    result = {
        "stock_code": stock_code,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_price": None,
        "change_percent": None,
        "change_amount": None,
        "volume": None,
        "MA50": None,
        "MA200": None
    }
    
    if stock_info:
        try:
            result["stock_name"] = stock_info.get("n", "")
            z = stock_info.get("z")
            y = stock_info.get("y")
            
            if z:
                result["current_price"] = float(z)
            
            if y:
                yesterday_close = float(y)
                if z:
                    change = float(z) - yesterday_close
                    result["change_amount"] = round(change, 2)
                    result["change_percent"] = round((change / yesterday_close) * 100, 2)
            
            v = stock_info.get("v")
            if v:
                result["volume"] = int(v)
        except Exception as e:
            print(f"解析实时数据时出错: {e}")
    
    ma = {}
    macd = None
    rsi = None
    bb = None
    
    if historical_prices:
        ma = calculate_moving_averages(historical_prices)
        result["MA50"] = ma.get("MA50")
        result["MA200"] = ma.get("MA200")
        
        macd = calculate_macd(historical_prices)
        rsi = calculate_rsi(historical_prices)
        bb = calculate_bollinger_bands(historical_prices)
        
        result["macd"] = macd
        result["rsi"] = rsi
        result["bollinger_bands"] = bb
    
    analysis = generate_comprehensive_analysis(stock_code, result, historical_prices, ma, macd, rsi, bb)
    result["comprehensive_analysis"] = analysis
    
    result["chinese_report"] = generate_chinese_report(stock_code, result, ma, macd, rsi, bb, analysis)
    
    return result


if __name__ == "__main__":
    stock_code = input("请输入股票代码 (例如 2330): ")
    result = analyze_stock(stock_code)
    print("\n" + result["chinese_report"])
    print("\nJSON 格式数据:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

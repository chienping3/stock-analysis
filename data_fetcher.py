import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import time
import config
import yfinance as yf


class TWSEDataFetcher:
    """台灣證交所數據獲取器"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    # ── CSV 快取層 ────────────────────────────
    def _get_cache_path(self, stock_code: str) -> str:
        return os.path.join(config.DATA_DIR, f"{stock_code}_cache.csv")

    def _load_cache(self, stock_code: str):
        """從 CSV 快取載入資料，若快取過期則回傳 None。"""
        cache_path = self._get_cache_path(stock_code)
        if not os.path.exists(cache_path):
            return None

        # 檢查快取時效
        mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        age_hours = (datetime.now() - mtime).total_seconds() / 3600
        if age_hours > config.CACHE_TTL_HOURS:
            print(f"快取已過期（{age_hours:.1f} 小時），重新抓取 …")
            return None

        try:
            df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            if len(df) > 0:
                print(f"從快取載入 {len(df)} 天歷史數據（{age_hours:.1f} 小時前）")
                return df
        except Exception as e:
            print(f"快取讀取失敗: {e}")
        return None

    def _save_cache(self, stock_code: str, df: pd.DataFrame):
        """將 DataFrame 儲存為 CSV 快取。"""
        cache_path = self._get_cache_path(stock_code)
        try:
            df.to_csv(cache_path)
            print(f"數據已快取至 {cache_path}")
        except Exception as e:
            print(f"快取儲存失敗: {e}")

    def get_stock_info(self, stock_code):
        """獲取股票即時資訊"""
        try:
            url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_code}.tw"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('msgArray') and len(data['msgArray']) > 0:
                return data['msgArray'][0]
            return None
        except Exception as e:
            print(f"獲取即時資訊失敗: {e}")
            return None

    def get_historical_data_twse(self, stock_code, years=3):
        """
        從TWSE獲取歷史數據 (OHLCV)
        返回包含日期、開盤價、最高價、最低價、收盤價、成交量的DataFrame
        """
        try:
            all_data = []
            end_date = datetime.now()

            for year_offset in range(years):
                for month in range(12):
                    check_date = end_date - timedelta(days=(year_offset * 365 + month * 30))
                    date_str = check_date.strftime("%Y%m01")

                    url = f"https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date={date_str}&stockNo={stock_code}"

                    try:
                        response = requests.get(url, headers=self.headers, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('data'):
                                for item in data['data']:
                                    try:
                                        # 解析日期 (民國年轉西元年)
                                        date_parts = item[0].split('/')
                                        year = int(date_parts[0]) + 1911
                                        month = int(date_parts[1])
                                        day = int(date_parts[2])
                                        date = datetime(year, month, day)

                                        # 解析價格和成交量
                                        open_price = float(str(item[3]).replace(',', ''))
                                        high_price = float(str(item[4]).replace(',', ''))
                                        low_price = float(str(item[5]).replace(',', ''))
                                        close_price = float(str(item[6]).replace(',', ''))
                                        volume = int(str(item[8]).replace(',', ''))

                                        all_data.append({
                                            'Date': date,
                                            'Open': open_price,
                                            'High': high_price,
                                            'Low': low_price,
                                            'Close': close_price,
                                            'Volume': volume
                                        })
                                    except Exception:
                                        continue
                        time.sleep(0.3)  # 避免請求過快
                    except Exception as e:
                        print(f"獲取 {date_str} 數據失敗: {e}")
                        continue

            if all_data:
                df = pd.DataFrame(all_data)
                df = df.sort_values('Date').drop_duplicates(subset=['Date']).set_index('Date')
                print(f"成功獲取 {len(df)} 天歷史數據")
                return df
            return None

        except Exception as e:
            print(f"獲取歷史數據失敗: {e}")
            return None

    def get_historical_data_yfinance(self, stock_code, years=3):
        """
        從Yahoo Finance獲取歷史數據 (作為備用方案)
        台股代碼需加上 .TW，如 2330.TW
        """
        try:
            symbol = f"{stock_code}.TW"
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)

            df = yf.download(symbol, start=start_date, end=end_date)

            if not df.empty:
                # 清理數據
                df = df.round(2)
                df.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
                print(f"從Yahoo Finance獲取 {len(df)} 天歷史數據")
                return df
            return None
        except Exception as e:
            print(f"從Yahoo Finance獲取數據失敗: {e}")
            return None

    def get_historical_data(self, stock_code, years=3, prefer_twse=True):
        """
        獲取歷史數據，優先使用TWSE，失敗則使用Yahoo Finance
        """
        if prefer_twse:
            df = self.get_historical_data_twse(stock_code, years)
            if df is not None and len(df) > 0:
                self._save_cache(stock_code, df)
                return df

        df = self.get_historical_data_yfinance(stock_code, years)
        if df is not None and len(df) > 0:
            self._save_cache(stock_code, df)
        return df

    def get_historical_data_cached(self, stock_code: str, years: int = 3,
                                   force_refresh: bool = False):
        """
        獲取歷史數據（附快取）。

        - 優先讀取 CSV 快取（若未過期且範圍足夠）
        - 若無快取或過期，則從 TWSE / Yahoo Finance 抓取並更新快取
        - force_refresh=True 強制略過快取
        """
        if not force_refresh:
            df = self._load_cache(stock_code)
            if df is not None:
                # 檢查快取資料是否涵蓋足夠歷史
                oldest = df.index.min()
                expected_start = datetime.now() - timedelta(days=years * 365)
                if oldest <= expected_start + timedelta(days=30):
                    return df
                # 快取存在但範圍不足，重新抓取
                print("快取資料範圍不足，重新抓取完整歷史 …")

        df = self.get_historical_data(stock_code, years=years)
        return df


if __name__ == "__main__":
    fetcher = TWSEDataFetcher()

    # 測試獲取台積電數據
    print("正在獲取台積電 (2330) 歷史數據...")
    df = fetcher.get_historical_data("2330", years=2)

    if df is not None:
        print("\n數據預覽:")
        print(df.head())
        print(f"\n數據時間範圍: {df.index[0]} 至 {df.index[-1]}")
        df.to_csv("2330_historical_data.csv")
        print("\n數據已保存到 2330_historical_data.csv")

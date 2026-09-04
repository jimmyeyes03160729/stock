import os
import json
import time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import requests
import yfinance as yf

# 欲追蹤的台股標的名單 (示範：台積電、聯發科、鴻海)
WATCHLIST = ["2330", "2454", "2317"]
OUTPUT_DIR = "public/data/stocks"
OVERVIEW_PATH = "public/data/market_overview.json"


def fetch_institutional_investors(date_str: str = None) -> dict:
    """
    從台灣證券交易所 (TWSE) 抓取當日三大法人買賣超日報 (T86)
    
    :param date_str: 格式為 YYYYMMDD (例如 "20260904")，若為 None 則預設當日
    :return: 字典結構 { '2330': {'foreign': 5210, 'trust': 1200, 'dealer': -300, 'total': 6110}, ... } (單位：張)
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")

    url = "https://www.twse.com.tw/rwd/zh/fund/T86"
    params = {
        "date": date_str,
        "selectType": "ALL",  # 全部上市股票
        "response": "json"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    result = {}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"[TWSE] 請求失敗，HTTP 代碼: {resp.status_code}")
            return result

        data = resp.json()
        if data.get("stat") != "OK":
            print(f"[TWSE] 查無資料或非交易日: {data.get('stat')}")
            return result

        # 欄位通常包含：證券代號, 證券名稱, 外陸資買進, 外陸資賣出, 外陸資買賣超,
        #              投信買進, 投信賣出, 投信買賣超, 自營商買賣超, 三大法人買賣超合計
        fields = data.get("fields", [])
        rows = data.get("data", [])

        # 找到關鍵欄位索引
        try:
            code_idx = fields.index("證券代號")
            foreign_net_idx = fields.index("外陸資買賣超股數(不含外資自營商)") if "外陸資買賣超股數(不含外資自營商)" in fields else fields.index("外陸資買賣超股數")
            trust_net_idx = fields.index("投信買賣超股數")
            dealer_net_idx = fields.index("自營商買賣超股數")
            total_net_idx = fields.index("三大法人買賣超股數")
        except ValueError:
            # 容錯：若欄位名稱微調，使用標準順序索引
            code_idx, foreign_net_idx, trust_net_idx, dealer_net_idx, total_net_idx = 0, 4, 7, 10, 11

        for row in rows:
            sym = row[code_idx].strip()
            if sym in WATCHLIST:
                # 轉為數值 (股數 / 1000 = 張數)
                to_lots = lambda val: int(str(val).replace(",", "").strip()) // 1000
                result[sym] = {
                    "foreign_net_lots": to_lots(row[foreign_net_idx]),   # 外資買賣超 (張)
                    "trust_net_lots": to_lots(row[trust_net_idx]),       # 投信買賣超 (張)
                    "dealer_net_lots": to_lots(row[dealer_net_idx]),     # 自營商買賣超 (張)
                    "total_net_lots": to_lots(row[total_net_idx]),       # 合計 (張)
                }

    except Exception as e:
        print(f"[TWSE] 抓取三大法人資料異常: {e}")

    return result


def fetch_tw_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """透過 yfinance 取得還原日 K 資料 (台股代碼後綴 .TW)"""
    ticker = f"{symbol}.TW"
    df = yf.download(ticker, period=period, progress=False)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
        
    df.dropna(inplace=True)
    return df


def calculate_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """計算技術面特徵：布林通道帶寬、乖離率、均線動量"""
    df = df.copy()
    
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA60"] = df["Close"].rolling(window=60).mean()
    rolling_std = df["Close"].rolling(window=20).std()
    df["BB_upper"] = df["MA20"] + (rolling_std * 2)
    df["BB_lower"] = df["MA20"] - (rolling_std * 2)
    df["BB_bandwidth"] = (df["BB_upper"] - df["BB_lower"]) / df["MA20"]
    
    df["Bias_MA20"] = (df["Close"] - df["MA20"]) / df["MA20"]
    df["Bias_MA60"] = (df["Close"] - df["MA60"]) / df["MA60"]
    
    vol_ma5 = df["Volume"].rolling(window=5).mean()
    vol_ma20 = df["Volume"].rolling(window=20).mean()
    df["Vol_Ratio_5_20"] = vol_ma5 / (vol_ma20 + 1e-9)
    
    return df


def run_monte_carlo(price_series: pd.Series, days_ahead: int = 20, simulations: int = 2000) -> dict:
    """幾何布朗運動 (GBM) 蒙地卡羅模擬，產出未來 P10, P50, P90 路徑"""
    np.random.seed(42)
    log_returns = np.log(price_series / price_series.shift(1)).dropna()
    
    mu = log_returns.mean()
    sigma = log_returns.std()
    drift = mu - (0.5 * sigma ** 2)
    
    shock = np.random.normal(0, 1, (days_ahead, simulations))
    daily_returns = np.exp(drift + sigma * shock)
    
    current_price = float(price_series.iloc[-1])
    paths = np.zeros((days_ahead + 1, simulations))
    paths[0] = current_price
    
    for t in range(1, days_ahead + 1):
        paths[t] = paths[t - 1] * daily_returns[t - 1]
        
    p10 = np.percentile(paths, 10, axis=1)
    p50 = np.percentile(paths, 50, axis=1)
    p90 = np.percentile(paths, 90, axis=1)
    
    return {
        "current_price": round(current_price, 2),
        "days_ahead": days_ahead,
        "scenarios": {
            "p10_support": [round(x, 2) for x in p10.tolist()],
            "p50_median": [round(x, 2) for x in p50.tolist()],
            "p90_optimistic": [round(x, 2) for x in p90.tolist()]
        },
        "metrics": {
            "expected_return_p50_pct": round(((p50[-1] / current_price) - 1) * 100, 2),
            "max_risk_p10_pct": round(((p10[-1] / current_price) - 1) * 100, 2),
            "max_gain_p90_pct": round(((p90[-1] / current_price) - 1) * 100, 2),
            "annualized_volatility_pct": round(sigma * np.sqrt(250) * 100, 2)
        }
    }


def estimate_upward_probability(df: pd.DataFrame, chips: dict = None) -> float:
    """結合技術面與三大法人籌碼的綜合勝率推估"""
    latest = df.iloc[-1]
    score = 0.5  # 基準 50%
    
    # 1. 技術面動能
    if latest["Close"] > latest["MA20"] > latest["MA60"]:
        score += 0.12
    if latest["BB_bandwidth"] < df["BB_bandwidth"].quantile(0.25):
        score += 0.08
    if latest["Vol_Ratio_5_20"] > 1.2:
        score += 0.08
    if latest["Bias_MA20"] > 0.08:
        score -= 0.12
        
    # 2. 法人籌碼權重 (若當日投信大幅買超加分)
    if chips:
        # 投信作帳效應加分
        if chips.get("trust_net_lots", 0) > 200:
            score += 0.10
        elif chips.get("trust_net_lots", 0) < -200:
            score -= 0.08
            
        # 三大法人同步大買超
        if chips.get("total_net_lots", 0) > 1000:
            score += 0.08
        elif chips.get("total_net_lots", 0) < -1000:
            score -= 0.08
        
    return float(np.clip(score, 0.05, 0.95))


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    summary_list = []
    
    # 抓取當日三大法人資料 (盤後 15:30 後有資料)
    today_str = datetime.now().strftime("%Y%m%d")
    print(f"正在獲取 {today_str} 證交所三大法人買賣超資料...")
    inst_data = fetch_institutional_investors(today_str)
    
    # 若當日無資料 (例如例假日或 15:30 前執行)，嘗試取前一個工作日
    if not inst_data:
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        print(f"當日尚未開獎或非交易日，回溯嘗試獲取前一日: {yesterday_str}")
        inst_data = fetch_institutional_investors(yesterday_str)

    for symbol in WATCHLIST:
        print(f"Processing {symbol}...")
        df = fetch_tw_stock_data(symbol, period="1y")
        if df.empty:
            continue
            
        df = calculate_technical_features(df)
        mc_data = run_monte_carlo(df["Close"], days_ahead=20)
        
        # 取得個股法人籌碼
        stock_chips = inst_data.get(symbol, {
            "foreign_net_lots": 0,
            "trust_net_lots": 0,
            "dealer_net_lots": 0,
            "total_net_lots": 0
        })
        
        up_prob = estimate_upward_probability(df, stock_chips)
        
        # 轉換歷史日 K
        candles = []
        for idx, row in df.tail(120).iterrows():
            candles.append({
                "time": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"])
            })
            
        stock_payload = {
            "symbol": symbol,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "institutional_investors": stock_chips,
            "signal": {
                "upward_probability_10d": round(up_prob * 100, 1),
                "bias_rating": "Bullish" if up_prob >= 0.65 else ("Bearish" if up_prob <= 0.35 else "Neutral")
            },
            "monte_carlo": mc_data,
            "candles": candles
        }
        
        with open(f"{OUTPUT_DIR}/{symbol}.json", "w", encoding="utf-8") as f:
            json.dump(stock_payload, f, ensure_ascii=False, indent=2)
            
        summary_list.append({
            "symbol": symbol,
            "price": mc_data["current_price"],
            "prob_10d": round(up_prob * 100, 1),
            "rating": stock_payload["signal"]["bias_rating"],
            "trust_buy": stock_chips["trust_net_lots"],
            "total_inst_buy": stock_chips["total_net_lots"],
            "expected_p50": mc_data["metrics"]["expected_return_p50_pct"]
        })

    with open(OVERVIEW_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stocks": summary_list
        }, f, ensure_ascii=False, indent=2)

    print("Data pipeline executed successfully.")


if __name__ == "__main__":
    main()
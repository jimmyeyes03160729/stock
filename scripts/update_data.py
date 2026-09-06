import os
import json
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import requests
import yfinance as yf

WATCHLIST = ["2330", "2454", "2317"]
OUTPUT_DIR = "public/data/stocks"
OVERVIEW_PATH = "public/data/market_overview.json"


def fetch_institutional_investors(date_str: str = None) -> dict:
    """抓取證交所當日三大法人買賣超 (T86)"""
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")

    url = "https://www.twse.com.tw/rwd/zh/fund/T86"
    params = {"date": date_str, "selectType": "ALL", "response": "json"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    result = {}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code != 200:
            return result

        data = resp.json()
        if data.get("stat") != "OK":
            return result

        fields = data.get("fields", [])
        rows = data.get("data", [])

        try:
            code_idx = fields.index("證券代號")
            foreign_net_idx = fields.index("外陸資買賣超股數(不含外資自營商)") if "外陸資買賣超股數(不含外資自營商)" in fields else fields.index("外陸資買賣超股數")
            trust_net_idx = fields.index("投信買賣超股數")
            dealer_net_idx = fields.index("自營商買賣超股數")
            total_net_idx = fields.index("三大法人買賣超股數")
        except ValueError:
            code_idx, foreign_net_idx, trust_net_idx, dealer_net_idx, total_net_idx = 0, 4, 7, 10, 11

        for row in rows:
            sym = row[code_idx].strip()
            if sym in WATCHLIST:
                to_lots = lambda val: int(str(val).replace(",", "").strip()) // 1000
                result[sym] = {
                    "foreign_net_lots": to_lots(row[foreign_net_idx]),
                    "trust_net_lots": to_lots(row[trust_net_idx]),
                    "dealer_net_lots": to_lots(row[dealer_net_idx]),
                    "total_net_lots": to_lots(row[total_net_idx]),
                }
    except Exception as e:
        print(f"[TWSE] 抓取異常: {e}")

    return result


def fetch_tw_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    ticker = f"{symbol}.TW"
    df = yf.download(ticker, period=period, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    df.dropna(inplace=True)
    return df


def calculate_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA60"] = df["Close"].rolling(window=60).mean()
    rolling_std = df["Close"].rolling(window=20).std()
    df["BB_upper"] = df["MA20"] + (rolling_std * 2)
    df["BB_lower"] = df["MA20"] - (rolling_std * 2)
    df["BB_bandwidth"] = (df["BB_upper"] - df["BB_lower"]) / df["MA20"]
    df["Bias_MA20"] = (df["Close"] - df["MA20"]) / df["MA20"]
    vol_ma5 = df["Volume"].rolling(window=5).mean()
    vol_ma20 = df["Volume"].rolling(window=20).mean()
    df["Vol_Ratio_5_20"] = vol_ma5 / (vol_ma20 + 1e-9)
    return df


def run_monte_carlo(price_series: pd.Series, days_ahead: int = 20, simulations: int = 2000) -> dict:
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
    latest = df.iloc[-1]
    score = 0.5
    if latest["Close"] > latest["MA20"] > latest["MA60"]:
        score += 0.12
    if latest["BB_bandwidth"] < df["BB_bandwidth"].quantile(0.25):
        score += 0.08
    if latest["Vol_Ratio_5_20"] > 1.2:
        score += 0.08
    if latest["Bias_MA20"] > 0.08:
        score -= 0.12

    if chips:
        if chips.get("trust_net_lots", 0) > 200:
            score += 0.10
        elif chips.get("trust_net_lots", 0) < -200:
            score -= 0.08
        if chips.get("total_net_lots", 0) > 1000:
            score += 0.08
        elif chips.get("total_net_lots", 0) < -1000:
            score -= 0.08

    return float(np.clip(score, 0.05, 0.95))


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today_str = datetime.now().strftime("%Y%m%d")
    inst_data = fetch_institutional_investors(today_str)
    if not inst_data:
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        inst_data = fetch_institutional_investors(yesterday_str)

    summary_list = []
    for symbol in WATCHLIST:
        print(f"處理標的: {symbol}...")
        df = fetch_tw_stock_data(symbol, period="1y")
        if df.empty:
            continue

        df = calculate_technical_features(df)
        mc_data = run_monte_carlo(df["Close"], days_ahead=20)
        stock_chips = inst_data.get(symbol, {
            "foreign_net_lots": 0, "trust_net_lots": 0, "dealer_net_lots": 0, "total_net_lots": 0
        })
        up_prob = estimate_upward_probability(df, stock_chips)

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

        payload = {
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
            json.dump(payload, f, ensure_ascii=False, indent=2)

        summary_list.append({
            "symbol": symbol,
            "price": mc_data["current_price"],
            "prob_10d": round(up_prob * 100, 1),
            "rating": payload["signal"]["bias_rating"]
        })

    with open(OVERVIEW_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stocks": summary_list
        }, f, ensure_ascii=False, indent=2)

    print("資料管線更新完成。")


if __name__ == "__main__":
    main()

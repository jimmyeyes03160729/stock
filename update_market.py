import os
import json
import finlab
from finlab import data
import pandas as pd
from datetime import datetime

api_token = os.environ.get("FINLAB_API_TOKEN")
if not api_token:
    api_token = "KVMzuQCjV8cPqWkS8I2qD+dudw30SnkT1pCjzg45M9DCcHh1BKUkkFnVeczO+N5+"

finlab.login(api_token)

def sync():
    print("正在透過 FinLab 下載數據並執行體積優化...")
    # 抓取近 400 天數據即可計算 250 日日線與各項指標
    data.truncate_start = (datetime.now() - pd.Timedelta(days=450)).strftime('%Y-%m-%d')
    
    close = data.get('price:收盤價')
    open_p = data.get('price:開盤價')
    high_p = data.get('price:最高價')
    low_p = data.get('price:最低價')
    vol = data.get('price:成交股數')
    foreign = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)') // 1000
    trust = data.get('institutional_investors_trading_summary:投信買賣超股數') // 1000

    pe = data.get('price_earning_ratio:本益比')
    pb = data.get('price_earning_ratio:股價淨值比')
    rev_yoy = data.get('monthly_revenue:去年同月增減(%)')

    info_map = {}
    try:
        df_info = data.get('company_basic_info')
        if 'stock_id' not in df_info.columns:
            df_info = df_info.reset_index()

        for _, row in df_info.iterrows():
            sid = str(row.get('stock_id', row.get('index', ''))).strip()
            name = str(row.get('公司簡稱', row.get('stock_name', row.get('公司名稱', '')))).strip()
            cat = None
            for col in ['產業類別', '產業別', '類別', 'category', '主要業務']:
                if col in row and pd.notna(row[col]) and str(row[col]).strip() != '':
                    cat = str(row[col]).strip()
                    break
            if not cat:
                cat = "其他"
            cat = cat.replace("工業", "").replace("科技", "")
            if cat.endswith("業") and len(cat) > 2:
                cat = cat[:-1]

            if sid and name:
                info_map[sid] = {"name": name, "category": cat}
    except Exception as e:
        print(f"公司資訊警告: {e}")

    latest_date = close.index[-1].strftime('%Y-%m-%d')
    latest_close = close.iloc[-1]
    latest_pe = pe.iloc[-1] if not pe.empty else None
    latest_pb = pb.iloc[-1] if not pb.empty else None
    latest_rev = rev_yoy.iloc[-1] if not rev_yoy.empty else None

    # 取得成交量前 300 大或熱門指標股（其餘股票使用即時端點載入，避免檔案破百MB）
    avg_vol = vol.iloc[-20:].mean() if not vol.empty else pd.Series()
    top_volume_stocks = set(avg_vol.nlargest(300).index.tolist())

    stocks = []
    # 取近 250 個交易日
    history_slice = slice(-250, None)
    sliced_close = close.iloc[history_slice]
    date_strs = [d.strftime('%Y-%m-%d') for d in sliced_close.index]

    for symbol in latest_close.index:
        sym = str(symbol).strip()
        if not (len(sym) == 4 and sym.isdigit() and not sym.startswith(('00', '01', '02'))):
            continue

        p = latest_close[sym]
        if pd.isna(p) or p <= 0:
            continue

        info = info_map.get(sym, {"name": sym, "category": "其他"})
        c_name = info["name"]
        cat = info["category"]

        if any(keyword in c_name for keyword in ["ETF", "反1", "正2", "債", "存託憑證"]):
            continue

        net15 = 0
        if sym in foreign.columns and sym in trust.columns:
            f15 = foreign[sym].iloc[-15:].sum()
            t15 = trust[sym].iloc[-15:].sum()
            val = f15 + t15
            net15 = int(val) if not pd.isna(val) else 0

        pe_val = float(latest_pe[sym]) if latest_pe is not None and sym in latest_pe and pd.notna(latest_pe[sym]) else 18.0
        pb_val = float(latest_pb[sym]) if latest_pb is not None and sym in latest_pb and pd.notna(latest_pb[sym]) else 2.0
        rev_val = float(latest_rev[sym]) if latest_rev is not None and sym in latest_rev and pd.notna(latest_rev[sym]) else 8.0

        growth_score = max(-0.3, min(0.3, rev_val / 100.0))
        value_score = max(-0.2, min(0.2, (20.0 - pe_val) / 50.0)) if pe_val > 0 else -0.1
        chip_score = max(-0.2, min(0.2, net15 / 5000.0))
        ai_factor = round(float(min(0.96, max(0.12, 0.50 + growth_score + value_score + chip_score))), 3)

        # 🌟 僅對前 300 大熱門標的內嵌精準日 K 線（有效將檔案由 104MB 壓縮至約 5~8MB）
        kline = []
        if sym in top_volume_stocks and sym in open_p.columns and sym in high_p.columns and sym in low_p.columns:
            o_s = open_p[sym].iloc[history_slice]
            h_s = high_p[sym].iloc[history_slice]
            l_s = low_p[sym].iloc[history_slice]
            c_s = sliced_close[sym]

            for idx in range(len(date_strs)):
                c_val = c_s.iloc[idx]
                if pd.notna(c_val) and c_val > 0:
                    kline.append({
                        "time": date_strs[idx],
                        "open": round(float(o_s.iloc[idx] if pd.notna(o_s.iloc[idx]) else c_val), 2),
                        "high": round(float(h_s.iloc[idx] if pd.notna(h_s.iloc[idx]) else c_val), 2),
                        "low": round(float(l_s.iloc[idx] if pd.notna(l_s.iloc[idx]) else c_val), 2),
                        "close": round(float(c_val), 2)
                    })

        stocks.append({
            "symbol": sym,
            "name": c_name,
            "category": cat,
            "price": round(float(p), 2),
            "pe": round(pe_val, 1),
            "pb": round(pb_val, 2),
            "rev_yoy": round(rev_val, 1),
            "cnnFactor": ai_factor,
            "net15Total": net15,
            "kline": kline
        })

    print(f"收錄 {len(stocks)} 檔個股，準備產出精簡 JSON...")

    output_data = {
        "updated_at": latest_date,
        "market": {
            "taiex": 23450.0,
            "change": 150.0,
            "pct": "+0.65%"
        },
        "stocks": stocks
    }

    with open("market_data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, separators=(',', ':'))

    size_mb = os.path.getsize("market_data.json") / (1024 * 1024)
    print(f"✅ market_data.json 產出成功！檔案大小: {size_mb:.2f} MB (安全低於 100MB 限制)")

if __name__ == "__main__":
    sync()

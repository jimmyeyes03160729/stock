import re

# 內建常用台股與熱門 ETF 清單 (可擴充完整上市櫃清單或對接證交所 API)
TAIWAN_STOCK_MAP = {
    # 熱門 ETF
    "00878": "國泰永續高股息",
    "0050": "元大台灣50",
    "0056": "元大高股息",
    "00919": "群益台灣精選高息",
    "00929": "復華台灣科技優息",
    "006208": "富邦台50",
    # 被動元件 / 硬體 / 半導體 / 電子
    "6862": "三集瑞-KY",
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
    "2308": "台達電",
    "2327": "國巨",
    "2492": "華新科",
    "6173": "信昌電",
    "3037": "欣興",
    "2603": "長榮",
    "2609": "陽明",
    "2881": "富邦金",
    "2882": "國泰金"
}

# 建立反向字典（名稱 -> 代號）
NAME_TO_SYMBOL_MAP = {v: k for k, v in TAIWAN_STOCK_MAP.items()}

class TaiwanStockService:
    @staticmethod
    def get_stock_info(query: str) -> dict:
        """
        支援輸入 '00878'、'國泰永續高股息'、'6862'、'三集瑞'
        返回統一格式：{ "symbol": "6862", "name": "三集瑞-KY", "display": "三集瑞-KY (6862)" }
        """
        query = query.strip()
        
        # 1. 如果輸入純代號 (數字)
        if query in TAIWAN_STOCK_MAP:
            name = TAIWAN_STOCK_MAP[query]
            return {"symbol": query, "name": name, "display": f"{name} ({query})"}
        
        # 2. 如果輸入中文名稱 (精確或包含)
        for sym, name in TAIWAN_STOCK_MAP.items():
            if query == name or query in name:
                return {"symbol": sym, "name": name, "display": f"{name} ({sym})"}
        
        # 3. 若為未收錄之個股，仍保留代號與名稱預設
        return {"symbol": query, "name": query, "display": f"{query} ({query})"}

    @staticmethod
    def search_stocks(keyword: str) -> list[dict]:
        """模糊搜尋名稱或代號，提供輸入下拉建議"""
        keyword = keyword.strip().lower()
        results = []
        if not keyword:
            return results

        for sym, name in TAIWAN_STOCK_MAP.items():
            if keyword in sym.lower() or keyword in name.lower():
                results.append({
                    "symbol": sym,
                    "name": name,
                    "display": f"{name} ({sym})"
                })
        return results

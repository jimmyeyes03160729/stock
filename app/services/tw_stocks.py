import twstock

class TaiwanStockService:
    @staticmethod
    def get_stock_info(query: str) -> dict:
        """
        支援輸入代號（如 '00878'）或名稱（如 '三集瑞'、'台積電'）
        自動返回標準格式：{ "symbol": "00878", "name": "國泰永續高股息", "display": "國泰永續高股息 (00878)" }
        """
        query = str(query).strip()
        
        # 1. 直接以股票代號查詢
        if query in twstock.codes:
            item = twstock.codes[query]
            return {
                "symbol": item.code,
                "name": item.name,
                "display": f"{item.name} ({item.code})"
            }
        
        # 2. 以名稱精確或包含搜尋 (支援輸入「三集瑞」找到「三集瑞-KY」)
        for code, item in twstock.codes.items():
            if query == item.name or query in item.name:
                return {
                    "symbol": item.code,
                    "name": item.name,
                    "display": f"{item.name} ({item.code})"
                }
        
        # 3. 未找到時的安全 fallback
        return {
            "symbol": query,
            "name": query,
            "display": f"{query} ({query})"
        }

    @staticmethod
    def search_stocks(keyword: str) -> list[dict]:
        """模糊搜尋台股代號與名稱（供前端下拉建議）"""
        keyword = keyword.strip()
        results = []
        if not keyword:
            return results

        count = 0
        for code, item in twstock.codes.items():
            if keyword in code or keyword.lower() in item.name.lower():
                results.append({
                    "symbol": item.code,
                    "name": item.name,
                    "display": f"{item.name} ({item.code})"
                })
                count += 1
                if count >= 10:  # 限制最多回傳 10 筆推薦結果避免過長
                    break
        return results

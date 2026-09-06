from .analyzer import MultiTimeframeAnalyzer

class StockScreener:
    @staticmethod
    def screen_by_price_range(stock_pool: list[dict], min_price: float, max_price: float) -> list[dict]:
        """
        stock_pool 元素格式範例:
        {
            "symbol": "2330",
            "name": "台積電",
            "price": 950.0,
            "daily_prices": [...],
            "monthly_prices": [...],
            "quarterly_prices": [...]
        }
        """
        recommended_list = []

        for stock in stock_pool:
            price = stock.get("price", 0.0)
            if min_price <= price <= max_price:
                # 執行多週期分析
                analysis = MultiTimeframeAnalyzer.evaluate_stock(
                    daily_prices=stock.get("daily_prices", [price]),
                    monthly_prices=stock.get("monthly_prices", [price]),
                    quarterly_prices=stock.get("quarterly_prices", [price])
                )
                
                # 僅篩選出「看漲」或「強烈看多」股票
                if analysis["overall_signal"] in ["BULLISH", "STRONG_BUY"]:
                    recommended_list.append({
                        "symbol": stock["symbol"],
                        "name": stock["name"],
                        "price": price,
                        "overall_signal_zh": analysis["overall_signal_zh"],
                        "score": analysis["weighted_score"],
                        "daily_signal": analysis["timeframes"]["daily"]["signal_zh"],
                        "monthly_signal": analysis["timeframes"]["monthly"]["signal_zh"],
                        "quarterly_signal": analysis["timeframes"]["quarterly"]["signal_zh"]
                    })

        # 根據看漲綜合評分由高到低排序
        recommended_list.sort(key=lambda x: x["score"], reverse=True)
        return recommended_list

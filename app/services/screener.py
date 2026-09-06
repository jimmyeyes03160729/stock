from .analyzer import MultiTimeframeAnalyzer
from .tw_stocks import TaiwanStockService

class StockScreener:
    # 內建模擬台股完整資訊庫
    STOCK_DATA_SOURCE = [
        {
            "symbol": "00878", "price": 22.85,
            "daily_prices": [22.4, 22.5, 22.6, 22.75, 22.85],
            "monthly_prices": [21.5, 21.8, 22.2, 22.85],
            "quarterly_prices": [20.0, 21.2, 22.85]
        },
        {
            "symbol": "6862", "price": 198.5,
            "daily_prices": [185.0, 188.0, 192.0, 195.0, 198.5],
            "monthly_prices": [160.0, 172.0, 185.0, 198.5],
            "quarterly_prices": [140.0, 165.0, 198.5]
        },
        {
            "symbol": "2330", "price": 955.0,
            "daily_prices": [930, 935, 940, 948, 955],
            "monthly_prices": [880, 900, 920, 955],
            "quarterly_prices": [750, 820, 890, 955]
        },
        {
            "symbol": "2317", "price": 178.5,
            "daily_prices": [180, 179, 178.5, 178.5, 178.5],
            "monthly_prices": [170, 175, 180, 178.5],
            "quarterly_prices": [150, 160, 178.5]
        },
        {
            "symbol": "2454", "price": 1210.0,
            "daily_prices": [1180, 1190, 1200, 1205, 1210],
            "monthly_prices": [1100, 1150, 1180, 1210],
            "quarterly_prices": [1000, 1080, 1210]
        },
        {
            "symbol": "2327", "price": 635.0,
            "daily_prices": [610, 620, 625, 630, 635],
            "monthly_prices": [580, 600, 615, 635],
            "quarterly_prices": [550, 590, 635]
        }
    ]

    @classmethod
    def screen_by_price_range(cls, min_price: float, max_price: float) -> list[dict]:
        """依輸入價位區間篩選，並按看漲評分推薦排序"""
        results = []
        for item in cls.STOCK_DATA_SOURCE:
            price = item["price"]
            if min_price <= price <= max_price:
                stock_info = TaiwanStockService.get_stock_info(item["symbol"])
                
                analysis = MultiTimeframeAnalyzer.evaluate_stock(
                    daily_prices=item["daily_prices"],
                    monthly_prices=item["monthly_prices"],
                    quarterly_prices=item["quarterly_prices"]
                )

                # 推薦看漲標的
                if analysis["overall_signal"] in ["BULLISH", "STRONG_BUY"]:
                    results.append({
                        "symbol": item["symbol"],
                        "name": stock_info["name"],
                        "display_name": stock_info["display"],  # 格式：名稱 (代號)
                        "price": price,
                        "overall_signal_zh": analysis["overall_signal_zh"],
                        "score": analysis["weighted_score"],
                        "daily_signal": analysis["timeframes"]["daily"]["signal_zh"],
                        "monthly_signal": analysis["timeframes"]["monthly"]["signal_zh"],
                        "quarterly_signal": analysis["timeframes"]["quarterly"]["signal_zh"]
                    })

        # 分數由高至低排列
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

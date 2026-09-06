import pandas as pd
import numpy as np

# 中文訊號對照表
SIGNAL_TRANSLATION = {
    "STRONG_BUY": "強烈看多",
    "BULLISH": "看漲",
    "NEUTRAL": "中立盤整",
    "BEARISH": "看跌",
    "STRONG_SELL": "強烈看空"
}

class MultiTimeframeAnalyzer:
    """日線 / 月線 / 季線 多週期分析器"""

    @staticmethod
    def calculate_ma(prices: list[float], window: int) -> float:
        if len(prices) < window:
            return prices[-1] if prices else 0.0
        return float(pd.Series(prices).rolling(window=window).mean().iloc[-1])

    @classmethod
    def analyze_cycle(cls, prices: list[float]) -> dict:
        """單一週期趨勢評估"""
        if not prices:
            return {"signal": "NEUTRAL", "signal_zh": SIGNAL_TRANSLATION["NEUTRAL"], "score": 50}
        
        current_price = prices[-1]
        ma5 = cls.calculate_ma(prices, 5)
        ma20 = cls.calculate_ma(prices, 20)
        
        # 評分機制
        score = 50
        if current_price > ma5:
            score += 20
        else:
            score -= 15
            
        if ma5 > ma20:
            score += 25
        else:
            score -= 20

        # 分數對應多空
        if score >= 85:
            signal_key = "STRONG_BUY"
        elif score >= 65:
            signal_key = "BULLISH"
        elif score <= 30:
            signal_key = "STRONG_SELL"
        elif score <= 45:
            signal_key = "BEARISH"
        else:
            signal_key = "NEUTRAL"

        return {
            "signal": signal_key,
            "signal_zh": SIGNAL_TRANSLATION[signal_key],
            "score": score,
            "ma5": round(ma5, 2),
            "ma20": round(ma20, 2)
        }

    @classmethod
    def evaluate_stock(cls, daily_prices: list[float], monthly_prices: list[float], quarterly_prices: list[float]):
        """多週期共振評估：日線、月線、季線"""
        daily_res = cls.analyze_cycle(daily_prices)
        monthly_res = cls.analyze_cycle(monthly_prices)
        quarterly_res = cls.analyze_cycle(quarterly_prices)

        # 權重：日線 40%、月線 35%、季線 25%
        weighted_score = (daily_res["score"] * 0.40) + (monthly_res["score"] * 0.35) + (quarterly_res["score"] * 0.25)
        
        if weighted_score >= 80:
            overall_key = "STRONG_BUY"
        elif weighted_score >= 65:
            overall_key = "BULLISH"
        elif weighted_score <= 35:
            overall_key = "BEARISH"
        elif weighted_score <= 20:
            overall_key = "STRONG_SELL"
        else:
            overall_key = "NEUTRAL"

        return {
            "overall_signal": overall_key,
            "overall_signal_zh": SIGNAL_TRANSLATION[overall_key],
            "weighted_score": round(weighted_score, 1),
            "timeframes": {
                "daily": daily_res,
                "monthly": monthly_res,
                "quarterly": quarterly_res
            }
        }

# StockVision Trading System (v2.1.0)

具備固定即時大盤行情、自選個股群組、股價區間推薦、歷年股利查詢與日/月/季多週期指標分析之股票系統。

## 本次更新重點 (Changelog v2.1.0)
1. **向下相容與版本系統**：API 路由全面升級 `/api/v2/`，並向下相容舊版模型。
2. **個股群組系統**：支援建立多個自選觀察群組。
3. **即時大盤專區**：置頂加權指數（TAIEX）儀表板，鎖定不可刪除，並以 WebSocket 進行即時跳動推播。
4. **全介面中文化**：全面將 Bullish、Bearish、Neutral 轉為「看漲」、「看跌」、「中立盤整」、「強烈看多」。
5. **價格區間推薦系統**：可輸入最低與最高價，自動運算並輸出具備看漲強度的推薦標的。
6. **歷年股利模組**：支援查詢近數年現金股利、股票股利與年均殖利率。
7. **多週期分析**：技術評估拉升至「日線」、「月線」、「季線」，支援長短線多週期共振判定。

## 本地快速啟動

```bash
# 1. 建立虛擬環境並安裝相依套件
python -m venv venv
source venv/bin/activate  # Windows 請用 venv\Scripts\activate
pip install -r requirements.txt

# 2. 啟動伺服器
uvicorn app.main:app --reload --port 8000

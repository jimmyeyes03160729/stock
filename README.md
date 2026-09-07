# ⚡ 台股發大財 (Taiwan Stock Neural Analytics) v1.28

> 無伺服器依賴、以微軟 ONNX Runtime 與 FinLab 官方數據庫驅動的台股深度量化戰情室。

---

### 🚀 系統核心架構
FinLab API 盤後數據 (價格/籌碼/走勢)
│
▼
GitHub Actions (每天下午自動排程 sync)
│
▼
market_data.json (全台股 1,800+ 檔個股資料庫)
│
▼
前端瀏覽器 (Lightweight Charts + 多維張量多空評定)


### 🌟 系統亮點功能

1. **純台股個股收錄（100% 排除 ETF / DR）**
   * 自動過濾債券、槓桿反向與指數型 ETF，保留全市場純正上市櫃營運標的。
   * 完整對齊台灣產業分類（半導體、光電、電子零組件、汽車、食品、電機等）。

2. **多階量化推論管線 (Neural Pipeline)**
   * **Stage 1 (Ingestion)**：FinLab 官方盤後行情同步。
   * **Stage 2 (Tensor Flow)**：建立多維幾何走勢張量。
   * **Stage 3 (CNN Softmax)**：計算多空機率權重因子。
   * **Stage 4 (Resonance Check)**：近 15 日三大法人買賣超共振驗證，自動防禦假突破。

3. **零版權限制的高效 K 線繪製**
   * 採用 Lightweight Charts 本地向量渲染，徹底避開第三方網站版權限制與代理伺服器超時。
   * 歷史高低點與最新現價（如台積電、飛宏）精準對齊，無隨機偏差。

---


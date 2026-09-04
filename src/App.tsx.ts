import React, { useEffect, useState } from 'react';
import { StockForecastChart } from './components/StockForecastChart';
import { StockDetailPayload } from './types/stock';

export default function App() {
  const [stockData, setStockData] = useState<StockDetailPayload | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('2330');

  useEffect(() => {
    // 讀取由 GitHub Actions 產生的靜態 JSON
    fetch(`/data/stocks/${selectedSymbol}.json`)
      .then((res) => res.json())
      .then((data: StockDetailPayload) => setStockData(data))
      .catch((err) => console.error('載入個股資料失敗:', err));
  }, [selectedSymbol]);

  return (
    <div style={{ minHeight: '100vh', background: '#0a0e17', padding: '24px', color: '#e0e0e0', fontFamily: 'sans-serif' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ color: '#fff', fontSize: '24px' }}>台股量化分析與情境預判看板</h1>
        <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
          {['2330', '2454', '2317'].map((sym) => (
            <button
              key={sym}
              onClick={() => setSelectedSymbol(sym)}
              style={{
                padding: '6px 16px',
                background: selectedSymbol === sym ? '#29b6f6' : '#1e222d',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              {sym}
            </button>
          ))}
        </div>
      </header>

      <main style={{ maxWidth: '1100px' }}>
        {stockData ? (
          <StockForecastChart data={stockData} />
        ) : (
          <div style={{ color: '#888' }}>載入數據中...</div>
        )}
      </main>
    </div>
  );
}
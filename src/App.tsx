import React, { useEffect, useState } from 'react';
import { StockForecastChart } from './components/StockForecastChart';
import { StockDetailPayload } from './types/stock';

const STOCKS = [
  { symbol: '2330', name: '台積電' },
  { symbol: '2454', name: '聯發科' },
  { symbol: '2317', name: '鴻海' },
];

export default function App() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('2330');
  const [stockData, setStockData] = useState<StockDetailPayload | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    setLoading(true);
    // 使用相對於當前頁面的路徑，避免 GitHub Pages /stock/ 子目錄 404
    fetch(`./data/stocks/${selectedSymbol}.json`)
      .then((res) => {
        if (!res.ok) throw new Error('資料載入失敗');
        return res.json();
      })
      .then((data: StockDetailPayload) => {
        setStockData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedSymbol]);

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px 16px' }}>
      <header style={{ marginBottom: '24px', borderBottom: '1px solid #232733', paddingBottom: '16px' }}>
        <h1 style={{ fontSize: '24px', color: '#fff', marginBottom: '8px' }}>
          台股量化分析與情境預判看板
        </h1>
        <p style={{ fontSize: '14px', color: '#888' }}>
          基於幾何布朗運動蒙地卡羅模擬與三大法人籌碼多因子評分（開源量化研究用途）
        </p>

        <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
          {STOCKS.map((s) => (
            <button
              key={s.symbol}
              onClick={() => setSelectedSymbol(s.symbol)}
              style={{
                padding: '8px 16px',
                background: selectedSymbol === s.symbol ? '#29b6f6' : '#1a1f2c',
                color: selectedSymbol === s.symbol ? '#000' : '#fff',
                border: '1px solid #2e3546',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 'bold',
                transition: 'all 0.2s',
              }}
            >
              {s.name} ({s.symbol})
            </button>
          ))}
        </div>
      </header>

      <main>
        {loading ? (
          <div style={{ padding: '60px', textAlign: 'center', color: '#888' }}>數據計算中...</div>
        ) : stockData ? (
          <div>
            {/* 個股籌碼即時卡片 */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
              <div style={{ background: '#131722', padding: '16px', borderRadius: '8px', border: '1px solid #232733' }}>
                <div style={{ color: '#888', fontSize: '12px' }}>現價</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff', marginTop: '4px' }}>
                  {stockData.monte_carlo.current_price} 元
                </div>
              </div>
              <div style={{ background: '#131722', padding: '16px', borderRadius: '8px', border: '1px solid #232733' }}>
                <div style={{ color: '#888', fontSize: '12px' }}>外資買賣超</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: stockData.institutional_investors.foreign_net_lots >= 0 ? '#ef5350' : '#26a69a', marginTop: '4px' }}>
                  {stockData.institutional_investors.foreign_net_lots > 0 ? '+' : ''}{stockData.institutional_investors.foreign_net_lots} 張
                </div>
              </div>
              <div style={{ background: '#131722', padding: '16px', borderRadius: '8px', border: '1px solid #232733' }}>
                <div style={{ color: '#888', fontSize: '12px' }}>投信買賣超</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: stockData.institutional_investors.trust_net_lots >= 0 ? '#ef5350' : '#26a69a', marginTop: '4px' }}>
                  {stockData.institutional_investors.trust_net_lots > 0 ? '+' : ''}{stockData.institutional_investors.trust_net_lots} 張
                </div>
              </div>
              <div style={{ background: '#131722', padding: '16px', borderRadius: '8px', border: '1px solid #232733' }}>
                <div style={{ color: '#888', fontSize: '12px' }}>三大法人合計</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: stockData.institutional_investors.total_net_lots >= 0 ? '#ef5350' : '#26a69a', marginTop: '4px' }}>
                  {stockData.institutional_investors.total_net_lots > 0 ? '+' : ''}{stockData.institutional_investors.total_net_lots} 張
                </div>
              </div>
            </div>

            {/* 主圖表 */}
            <StockForecastChart data={stockData} />
          </div>
        ) : (
          <div style={{ padding: '60px', textAlign: 'center', color: '#ef5350' }}>尚無該股票資料。</div>
        )}
      </main>

      <footer style={{ marginTop: '40px', textAlign: 'center', fontSize: '12px', color: '#555', borderTop: '1px solid #1a1f2c', paddingTop: '20px' }}>
        免責聲明：本網站內容僅供學術量化研究與策略回測展示，不構成任何證券之投資建議。
      </footer>
    </div>
  );
}

import React, { useEffect, useRef } from 'react';
import {
  createChart,
  ColorType,
  LineStyle,
  IChartApi,
  CandlestickData,
  Time,
} from 'lightweight-charts';
import { StockDetailPayload } from '../types/stock';

interface Props {
  data: StockDetailPayload;
}

function generateFutureBusinessDays(startDateStr: string, count: number): string[] {
  const dates: string[] = [];
  const current = new Date(startDateStr);

  while (dates.length < count) {
    current.setDate(current.getDate() + 1);
    const dayOfWeek = current.getDay();
    if (dayOfWeek !== 0 && dayOfWeek !== 6) {
      const yyyy = current.getFullYear();
      const mm = String(current.getMonth() + 1).padStart(2, '0');
      const dd = String(current.getDate()).padStart(2, '0');
      dates.push(`${yyyy}-${mm}-${dd}`);
    }
  }
  return dates;
}

export const StockForecastChart: React.FC<Props> = ({ data }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.candles.length === 0) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 480,
      layout: {
        background: { type: ColorType.Solid, color: '#131722' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#242732' },
        horzLines: { color: '#242732' },
      },
      timeScale: {
        borderColor: '#2B2B43',
        timeVisible: true,
        rightOffset: 15,
      },
    });

    chartRef.current = chart;

    // 台股色彩規格：紅漲綠跌
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#ef5350',
      downColor: '#26a69a',
      borderUpColor: '#ef5350',
      borderDownColor: '#26a69a',
      wickUpColor: '#ef5350',
      wickDownColor: '#26a69a',
    });
    candleSeries.setData(data.candles as CandlestickData<Time>[]);

    // 蒙地卡羅情境預測線
    const lastCandle = data.candles[data.candles.length - 1];
    const lastDateStr = lastCandle.time as string;
    const futureDates = generateFutureBusinessDays(lastDateStr, data.monte_carlo.days_ahead);

    const timeline = [lastDateStr, ...futureDates];
    const p10Vals = [data.monte_carlo.current_price, ...data.monte_carlo.scenarios.p10_support];
    const p50Vals = [data.monte_carlo.current_price, ...data.monte_carlo.scenarios.p50_median];
    const p90Vals = [data.monte_carlo.current_price, ...data.monte_carlo.scenarios.p90_optimistic];

    const p90Series = chart.addLineSeries({
      color: 'rgba(38, 166, 154, 0.8)',
      lineWidth: 1,
      title: 'P90 樂觀目標',
    });
    p90Series.setData(timeline.map((d, i) => ({ time: d as Time, value: p90Vals[i] })));

    const p50Series = chart.addLineSeries({
      color: '#29b6f6',
      lineWidth: 2,
      lineStyle: LineStyle.Dashed,
      title: 'P50 中位基準',
    });
    p50Series.setData(timeline.map((d, i) => ({ time: d as Time, value: p50Vals[i] })));

    const p10Series = chart.addLineSeries({
      color: 'rgba(239, 83, 80, 0.8)',
      lineWidth: 1,
      title: 'P10 悲觀支撐',
    });
    p10Series.setData(timeline.map((d, i) => ({ time: d as Time, value: p10Vals[i] })));

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data]);

  return (
    <div style={{ background: '#131722', padding: '16px', borderRadius: '12px', border: '1px solid #232733' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h2 style={{ fontSize: '20px', color: '#fff', margin: 0 }}>{data.symbol} 趨勢預判</h2>
            <span style={{
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 'bold',
              background: data.signal.bias_rating === 'Bullish' ? '#ef535022' : '#26a69a22',
              color: data.signal.bias_rating === 'Bullish' ? '#ef5350' : '#26a69a',
              border: `1px solid ${data.signal.bias_rating === 'Bullish' ? '#ef5350' : '#26a69a'}`
            }}>
              {data.signal.bias_rating}
            </span>
          </div>
          <p style={{ margin: '6px 0 0 0', fontSize: '13px', color: '#888' }}>
            更新時間：{data.updated_at} | 10 日突破機率：<strong style={{ color: '#29b6f6' }}>{data.signal.upward_probability_10d}%</strong>
          </p>
        </div>
        <div style={{ display: 'flex', gap: '16px', fontSize: '13px', fontFamily: 'monospace' }}>
          <span style={{ color: '#26a69a' }}>● P90: {data.monte_carlo.scenarios.p90_optimistic.slice(-1)[0]}</span>
          <span style={{ color: '#29b6f6' }}>-- P50: {data.monte_carlo.scenarios.p50_median.slice(-1)[0]}</span>
          <span style={{ color: '#ef5350' }}>● P10: {data.monte_carlo.scenarios.p10_support.slice(-1)[0]}</span>
        </div>
      </div>
      <div ref={containerRef} style={{ width: '100%' }} />
    </div>
  );
};

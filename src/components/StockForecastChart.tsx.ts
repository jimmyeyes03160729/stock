import React, { useEffect, useRef } from 'react';
import {
  createChart,
  ColorType,
  LineStyle,
  IChartApi,
  CandlestickData,
  LineData,
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
      height: 520,
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

    // K 線系列 (台股慣例：紅漲綠跌)
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#ef5350',
      downColor: '#26a69a',
      borderUpColor: '#ef5350',
      borderDownColor: '#26a69a',
      wickUpColor: '#ef5350',
      wickDownColor: '#26a69a',
    });
    candleSeries.setData(data.candles as CandlestickData<Time>[]);

    // 蒙地卡羅情境軌跡
    const lastCandle = data.candles[data.candles.length - 1];
    const lastDateStr = lastCandle.time as string;
    const futureDates = generateFutureBusinessDays(lastDateStr, data.monteCarlo.days_ahead);

    const timeline = [lastDateStr, ...futureDates];
    const p10Vals = [data.monteCarlo.current_price, ...data.monteCarlo.scenarios.p10_support];
    const p50Vals = [data.monteCarlo.current_price, ...data.monteCarlo.scenarios.p50_median];
    const p90Vals = [data.monteCarlo.current_price, ...data.monteCarlo.scenarios.p90_optimistic];

    const p90Series = chart.addLineSeries({
      color: 'rgba(38, 166, 154, 0.7)',
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
      color: 'rgba(239, 83, 80, 0.7)',
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
    <div style={{ background: '#131722', padding: '16px', borderRadius: '8px', color: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div>
          <h3 style={{ margin: 0 }}>{data.symbol} 股價預測與情境走勢</h3>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#888' }}>
            更新時間：{data.updated_at} | 10 日上漲突破機率：{data.signal.upward_probability_10d}%
          </p>
        </div>
        <div style={{ fontSize: '13px', fontFamily: 'monospace' }}>
          <span style={{ color: '#26a69a', marginRight: '12px' }}>● P90 樂觀目標</span>
          <span style={{ color: '#29b6f6', marginRight: '12px' }}>-- P50 預期基準</span>
          <span style={{ color: '#ef5350' }}>● P10 悲觀支撐</span>
        </div>
      </div>
      <div ref={containerRef} style={{ width: '100%' }} />
    </div>
  );
};
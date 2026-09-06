import asyncio
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .database import engine, Base, get_db
from .models import UserWatchlistGroup, WatchlistItem, StockDividend
from .services.analyzer import MultiTimeframeAnalyzer
from .services.screener import StockScreener
from .services.market_stream import market_manager, real_time_market_ticker

# 建立資料表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="StockVision Trading System",
    version="2.1.0",  # 版本標記 (Requirement 1)
    description="具備即時大盤、自選群組、多週期技術分析與股利查詢之選股系統"
)

# 模擬股票池 (實際應用可對接台股 API 或 DB)
MOCK_STOCK_POOL = [
    {
        "symbol": "2330", "name": "台積電", "price": 955.0,
        "daily_prices": [930, 935, 940, 948, 955],
        "monthly_prices": [880, 900, 920, 940, 955],
        "quarterly_prices": [750, 820, 890, 955]
    },
    {
        "symbol": "2317", "name": "鴻海", "price": 178.5,
        "daily_prices": [182, 180, 179, 178.5, 178.5],
        "monthly_prices": [170, 175, 180, 178.5],
        "quarterly_prices": [150, 160, 178.5]
    },
    {
        "symbol": "2454", "name": "聯發科", "price": 1210.0,
        "daily_prices": [1180, 1190, 1200, 1205, 1210],
        "monthly_prices": [1100, 1150, 1180, 1210],
        "quarterly_prices": [1000, 1080, 1210]
    },
    {
        "symbol": "2603", "name": "長榮", "price": 185.0,
        "daily_prices": [180, 181, 182, 184, 185],
        "monthly_prices": [170, 175, 180, 185],
        "quarterly_prices": [160, 165, 185]
    }
]

@app.on_event("startup")
async def startup_event():
    # 預先填入示範股利資料
    db = next(get_db())
    if not db.query(StockDividend).first():
        sample_dividends = [
            StockDividend(symbol="2330", year=2024, cash_dividend=13.0, stock_dividend=0.0, yield_rate=1.4),
            StockDividend(symbol="2330", year=2023, cash_dividend=11.0, stock_dividend=0.0, yield_rate=1.8),
            StockDividend(symbol="2330", year=2022, cash_dividend=10.0, stock_dividend=0.0, yield_rate=2.1),
            StockDividend(symbol="2317", year=2024, cash_dividend=5.4, stock_dividend=0.0, yield_rate=3.1),
            StockDividend(symbol="2454", year=2024, cash_dividend=55.0, stock_dividend=0.0, yield_rate=4.6),
            StockDividend(symbol="2603", year=2024, cash_dividend=10.0, stock_dividend=0.0, yield_rate=5.5),
        ]
        db.add_all(sample_dividends)
        
        # 建立預設群組
        default_group = UserWatchlistGroup(name="主力觀察組", user_id="default_user")
        db.add(default_group)
        db.commit()
        db.refresh(default_group)
        
        item = WatchlistItem(group_id=default_group.id, symbol="2330", name="台積電")
        db.add(item)
        db.commit()
    db.close()

    # 啟動即時行情背景推播迴圈
    asyncio.create_task(real_time_market_ticker())

# --- REST API v2 ---
class GroupCreate(BaseModel):
    name: str

class ItemAdd(BaseModel):
    symbol: str
    name: str

@app.get("/api/v2/system/info")
def get_system_info():
    """版本系統資訊"""
    return {
        "system_version": "v2.1.0",
        "compatible_with": "v1.x",
        "features": ["即時大盤鎖定", "多群組自選", "多週期技術分析", "股價區間推薦", "歷年股利"]
    }

# 2. 自訂群組 API
@app.get("/api/v2/watchlists")
def get_watchlists(db: Session = Depends(get_db)):
    groups = db.query(UserWatchlistGroup).all()
    result = []
    for g in groups:
        result.append({
            "id": g.id,
            "name": g.name,
            "items": [{"id": it.id, "symbol": it.symbol, "name": it.name} for it in g.items]
        })
    return result

@app.post("/api/v2/watchlists")
def create_watchlist(payload: GroupCreate, db: Session = Depends(get_db)):
    grp = UserWatchlistGroup(name=payload.name)
    db.add(grp)
    db.commit()
    db.refresh(grp)
    return {"id": grp.id, "name": grp.name, "items": []}

@app.post("/api/v2/watchlists/{group_id}/items")
def add_item_to_group(group_id: int, item: ItemAdd, db: Session = Depends(get_db)):
    new_item = WatchlistItem(group_id=group_id, symbol=item.symbol, name=item.name)
    db.add(new_item)
    db.commit()
    return {"status": "success", "message": "成功加入群組"}

# 5. 股價區間看漲推薦 API
@app.get("/api/v2/screener/bullish")
def screen_bullish_stocks(min_price: float = 0.0, max_price: float = 9999.0):
    return StockScreener.screen_by_price_range(MOCK_STOCK_POOL, min_price, max_price)

# 6. 歷年股利 API
@app.get("/api/v2/stocks/{symbol}/dividends")
def get_dividends(symbol: str, db: Session = Depends(get_db)):
    records = db.query(StockDividend).filter(StockDividend.symbol == symbol).order_by(StockDividend.year.desc()).all()
    return [
        {
            "year": r.year,
            "cash_dividend": r.cash_dividend,
            "stock_dividend": r.stock_dividend,
            "yield_rate": r.yield_rate
        } for r in records
    ]

# 7. 多週期技術分析 API
@app.get("/api/v2/stocks/{symbol}/multi-cycle-analysis")
def get_analysis(symbol: str):
    stock = next((s for s in MOCK_STOCK_POOL if s["symbol"] == symbol), None)
    if not stock:
        return {"error": "找不到個股資訊"}
    return MultiTimeframeAnalyzer.evaluate_stock(
        stock["daily_prices"], stock["monthly_prices"], stock["quarterly_prices"]
    )

# WebSocket 即時推播端點
@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    await market_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        market_manager.disconnect(websocket)

# 前端主頁
@app.get("/", response_class=HTMLResponse)
def index_page():
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

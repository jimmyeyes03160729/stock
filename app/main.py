import asyncio
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .database import engine, Base, get_db
from .models import UserWatchlistGroup, WatchlistItem, StockDividend
from .services.tw_stocks import TaiwanStockService
from .services.analyzer import MultiTimeframeAnalyzer
from .services.screener import StockScreener
from .services.market_stream import market_manager, real_time_market_ticker

Base.metadata.create_all(bind=engine)

app = FastAPI(title="台股智慧戰情與推薦系統", version="2.2.0")

class WatchlistAddRequest(BaseModel):
    query: str  # 可以是 00878 也可以是 "三集瑞"

class GroupCreate(BaseModel):
    name: str

@app.on_event("startup")
async def startup():
    # 預設股利與自選群組初始化
    db = next(get_db())
    if not db.query(StockDividend).first():
        db.add_all([
            StockDividend(symbol="00878", year=2024, cash_dividend=1.60, stock_dividend=0.0, yield_rate=7.0),
            StockDividend(symbol="00878", year=2023, cash_dividend=1.24, stock_dividend=0.0, yield_rate=6.4),
            StockDividend(symbol="6862", year=2024, cash_dividend=4.50, stock_dividend=0.0, yield_rate=2.8),
            StockDividend(symbol="2330", year=2024, cash_dividend=13.0, stock_dividend=0.0, yield_rate=1.4),
            StockDividend(symbol="2317", year=2024, cash_dividend=5.4, stock_dividend=0.0, yield_rate=3.1),
        ])
        
        # 建立預設群組
        grp = UserWatchlistGroup(name="我的核心持股", user_id="default_user")
        db.add(grp)
        db.commit()
        db.refresh(grp)
        
        # 預設加入：國泰永續高股息 (00878) 與 三集瑞-KY (6862)
        info1 = TaiwanStockService.get_stock_info("00878")
        info2 = TaiwanStockService.get_stock_info("6862")
        db.add(WatchlistItem(group_id=grp.id, symbol=info1["symbol"], name=info1["display"]))
        db.add(WatchlistItem(group_id=grp.id, symbol=info2["symbol"], name=info2["display"]))
        db.commit()
    db.close()

    # 啟動 WebSocket 大盤即時跳動
    asyncio.create_task(real_time_market_ticker())

# --- API 端點 ---

# 3. 搜尋 API：輸入「三集瑞」或「00878」直接搜尋
@app.get("/api/v2/stocks/search")
def search_stocks(q: str):
    return TaiwanStockService.search_stocks(q)

# 2. 自選股群組清單
@app.get("/api/v2/watchlists")
def get_watchlists(db: Session = Depends(get_db)):
    groups = db.query(UserWatchlistGroup).all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "items": [{"id": it.id, "symbol": it.symbol, "display_name": it.name} for it in g.items]
        }
        for g in groups
    ]

@app.post("/api/v2/watchlists")
def create_group(payload: GroupCreate, db: Session = Depends(get_db)):
    grp = UserWatchlistGroup(name=payload.name)
    db.add(grp)
    db.commit()
    return {"id": grp.id, "name": grp.name}

# 1. 新增股票至群組：自動辨識代號或名稱，統一格式化為「名稱 (代號)」
@app.post("/api/v2/watchlists/{group_id}/items")
def add_to_watchlist(group_id: int, payload: WatchlistAddRequest, db: Session = Depends(get_db)):
    stock_info = TaiwanStockService.get_stock_info(payload.query)
    
    item = WatchlistItem(
        group_id=group_id,
        symbol=stock_info["symbol"],
        name=stock_info["display"]  # 儲存為 國泰永續高股息 (00878)
    )
    db.add(item)
    db.commit()
    return {"status": "success", "stock": stock_info}

# 4. 價格區間看漲推薦
@app.get("/api/v2/screener/bullish")
def screen_bullish(min_price: float = 0.0, max_price: float = 9999.0):
    return StockScreener.screen_by_price_range(min_price, max_price)

# 歷年股利 API
@app.get("/api/v2/stocks/{symbol}/dividends")
def get_dividends(symbol: str, db: Session = Depends(get_db)):
    records = db.query(StockDividend).filter(StockDividend.symbol == symbol).order_by(StockDividend.year.desc()).all()
    return records

# WebSocket 大盤廣播
@app.websocket("/ws/market")
async def ws_market(websocket: WebSocket):
    await market_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        market_manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
def index():
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

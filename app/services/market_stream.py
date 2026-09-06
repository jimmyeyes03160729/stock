import asyncio
import random
from fastapi import WebSocket

class MarketStreamManager:
    """管理連線與即時行情推播"""
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass

market_manager = MarketStreamManager()

async def real_time_market_ticker():
    """模擬大盤 (加權指數) 與主力個股即時行情更新廣播"""
    base_market_index = 22150.00
    while True:
        await asyncio.sleep(2)  # 每 2 秒推播一次即時數據
        change = round(random.uniform(-18.5, 22.0), 2)
        base_market_index += change
        pct_change = round((change / base_market_index) * 100, 2)
        
        payload = {
            "type": "MARKET_TICK",
            "market_data": {
                "name": "加權指數 (TAIEX)",
                "locked": True,       # 標記不可刪除
                "price": round(base_market_index, 2),
                "change": change,
                "pct_change": pct_change,
                "volume_est": "3,450 億"
            },
            "sample_stocks": [
                {"symbol": "2330", "price": round(955.0 + random.uniform(-2, 3), 1)},
                {"symbol": "2454", "price": round(1210.0 + random.uniform(-5, 5), 1)},
                {"symbol": "2317", "price": round(178.5 + random.uniform(-1, 1), 1)}
            ]
        }
        await market_manager.broadcast(payload)

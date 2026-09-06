from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class UserWatchlistGroup(Base):
    """自訂個股群組"""
    __tablename__ = "watchlist_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, default="default_user", index=True)
    name = Column(String, nullable=False)
    
    items = relationship("WatchlistItem", back_populates="group", cascade="all, delete-orphan")

class WatchlistItem(Base):
    """群組內的個股清單"""
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("watchlist_groups.id"))
    symbol = Column(String, nullable=False)
    name = Column(String, nullable=False)

    group = relationship("UserWatchlistGroup", back_populates="items")

class StockDividend(Base):
    """歷年股利資料"""
    __tablename__ = "stock_dividends"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    year = Column(Integer, nullable=False)
    cash_dividend = Column(Float, default=0.0)      # 現金股利
    stock_dividend = Column(Float, default=0.0)     # 股票股利
    yield_rate = Column(Float, default=0.0)         # 殖利率 (%)

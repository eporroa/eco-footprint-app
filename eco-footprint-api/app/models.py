from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON, UniqueConstraint

class Merchant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    shop_domain: str = Field(index=True, unique=True)
    config_placement: Optional[str] = None
    config_verbiage: Optional[str] = None
    # NEW: optional per-merchant rate (fallback to global settings.rate)
    config_rate: Optional[float] = None
    api_key: Optional[str] = None

class OptIn(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("merchant_id", "cart_token", "created_ym"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    merchant_id: int = Field(index=True, foreign_key="merchant.id")
    cart_token: str = Field(index=True)
    currency: str = Field(default="USD")
    subtotal_cents: int
    estimate_cents: int
    payload: Dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_ym: str = Field(index=True)
    checkout_id: Optional[str] = None
    order_id: Optional[str] = None
    email: Optional[str] = None
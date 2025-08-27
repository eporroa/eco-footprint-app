from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class WidgetConfigResponse(BaseModel):
    placement: str
    verbiage: str

class MerchantConfig(BaseModel):
    placement: str
    verbiage: str
    rate: float

class CartItem(BaseModel):
    price_cents: int
    quantity: int
    grams: int | None = None
    product_type: str | None = None
    vendor: str | None = None

class EstimateRequest(BaseModel):
    shop: str
    currency: str = "USD"
    items: List[CartItem]

class EstimateResponse(BaseModel):
    currency: str
    subtotal_cents: int
    estimate_cents: int
    rate: float
    breakdown: Dict[str, Any] = Field(default_factory=dict)

class OptInRequest(BaseModel):
    shop: str
    cart_token: str
    currency: str = "USD"
    subtotal_cents: int
    estimate_cents: int
    payload: Dict[str, Any] = Field(default_factory=dict)

class InvoicePreview(BaseModel):
    shop: str
    month: str
    total_estimate_cents: int
    opt_in_count: int

class OptInRow(BaseModel):
    created_at: str
    cart_token: str
    subtotal_cents: int
    estimate_cents: int
    currency: str
    payload: Dict[str, Any]
from app.config import settings
from app.main import estimate, EstimateRequest, CartItem  # type: ignore

def test_estimate_formula(monkeypatch):
    req = EstimateRequest(shop="x", currency="USD", items=[
        CartItem(price_cents=1000, quantity=2),
        CartItem(price_cents=500, quantity=1),
    ])
    res = estimate(req)
    assert res.subtotal_cents == 2500
    assert res.estimate_cents == int(round(2500 * settings.rate))
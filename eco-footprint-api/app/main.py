from fastapi import FastAPI, Depends, Query, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from datetime import datetime
from .db import init_db, get_session
from .config import settings
from .schemas import (
    WidgetConfigResponse, EstimateRequest, EstimateResponse,
    OptInRequest, InvoicePreview, MerchantConfig, OptInRow
)
from .crud import get_or_create_merchant, save_opt_in, invoice_preview, list_optins
from .models import Merchant
import os

app = FastAPI(title="Carbon Offset Estimator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_allow_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "987654321cba")

def admin_auth(authorization: str | None = Header(None)):
    if not ADMIN_TOKEN:
        return True  # dev mode
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")
    return True

@app.on_event("startup")
def _startup():
    init_db()

# Static: also serves /admin/*
app.mount("/", StaticFiles(directory="app/static", html=False), name="static")

@app.get("/v1/config", response_model=WidgetConfigResponse)
def get_config(shop: str = Query(...), session: Session = Depends(get_session)):
    merchant = get_or_create_merchant(session, shop)
    return WidgetConfigResponse(
        placement=merchant.config_placement or settings.default_placement,
        verbiage=merchant.config_verbiage or settings.default_verbiage,
    )

@app.post("/v1/estimate", response_model=EstimateResponse)
def estimate(req: EstimateRequest, session: Session = Depends(get_session)):
    merchant = get_or_create_merchant(session, req.shop)
    rate = merchant.config_rate if merchant.config_rate is not None else settings.rate
    subtotal = sum(i.price_cents * i.quantity for i in req.items)
    estimate = int(round(subtotal * rate))
    return EstimateResponse(
        currency=req.currency,
        subtotal_cents=subtotal,
        estimate_cents=estimate,
        rate=rate,
        breakdown={"items": len(req.items)}
    )

@app.post("/v1/opt-in")
def opt_in(req: OptInRequest, session: Session = Depends(get_session)):
    merchant = get_or_create_merchant(session, req.shop)
    ym = datetime.utcnow().strftime("%Y-%m")
    save_opt_in(
        session,
        merchant_id=merchant.id,
        cart_token=req.cart_token,
        currency=req.currency,
        subtotal_cents=req.subtotal_cents,
        estimate_cents=req.estimate_cents,
        payload=req.payload,
        created_ym=ym,
    )
    return {"status": "ok"}

@app.get("/v1/invoices/preview", response_model=InvoicePreview)
def invoices_preview(shop: str, month: str, session: Session = Depends(get_session)):
    merchant = get_or_create_merchant(session, shop)
    total_cents, count = invoice_preview(session, merchant.id, month)
    return InvoicePreview(shop=shop, month=month, total_estimate_cents=total_cents, opt_in_count=count)

# ---------- Admin API ----------

@app.get("/v1/admin/merchant", response_model=MerchantConfig, dependencies=[Depends(admin_auth)])
def admin_get_merchant(shop: str, session: Session = Depends(get_session)):
    m = get_or_create_merchant(session, shop)
    rate = m.config_rate if m.config_rate is not None else settings.rate
    return MerchantConfig(
        placement=m.config_placement or settings.default_placement,
        verbiage=m.config_verbiage or settings.default_verbiage,
        rate=rate,
    )

@app.put("/v1/admin/merchant", response_model=MerchantConfig, dependencies=[Depends(admin_auth)])
def admin_update_merchant(shop: str, patch: MerchantConfig, session: Session = Depends(get_session)):
    m: Merchant = get_or_create_merchant(session, shop)
    m.config_placement = patch.placement
    m.config_verbiage = patch.verbiage
    m.config_rate = patch.rate
    session.add(m); session.commit(); session.refresh(m)
    return patch

@app.get("/v1/admin/invoices", response_model=InvoicePreview, dependencies=[Depends(admin_auth)])
def admin_invoices(shop: str, month: str, session: Session = Depends(get_session)):
    m = get_or_create_merchant(session, shop)
    total_cents, count = invoice_preview(session, m.id, month)
    return InvoicePreview(shop=shop, month=month, total_estimate_cents=total_cents, opt_in_count=count)

@app.get("/v1/admin/opt-ins", response_model=list[OptInRow], dependencies=[Depends(admin_auth)])
def admin_list_optins(shop: str, month: str, limit: int = 50, session: Session = Depends(get_session)):
    m = get_or_create_merchant(session, shop)
    rows = list_optins(session, m.id, month, limit)
    return [
        OptInRow(
            created_at=o.created_at.isoformat(),
            cart_token=o.cart_token,
            subtotal_cents=o.subtotal_cents,
            estimate_cents=o.estimate_cents,
            currency=o.currency,
            payload=o.payload
        ) for o in rows
    ]
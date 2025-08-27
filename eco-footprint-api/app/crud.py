from typing import List
from sqlmodel import Session, select, func
from .models import Merchant, OptIn

def get_or_create_merchant(session: Session, shop_domain: str) -> Merchant:
    m = session.exec(select(Merchant).where(Merchant.shop_domain == shop_domain)).first()
    if not m:
        m = Merchant(shop_domain=shop_domain)
        session.add(m)
        session.commit()
        session.refresh(m)
    return m

def save_opt_in(session: Session, merchant_id: int, **kwargs) -> OptIn:
    oi = OptIn(merchant_id=merchant_id, **kwargs)
    session.add(oi)
    session.commit()
    session.refresh(oi)
    return oi

def invoice_preview(session: Session, merchant_id: int, ym: str):
    q = select(
        func.coalesce(func.sum(OptIn.estimate_cents), 0),
        func.count(OptIn.id),
    ).where(OptIn.merchant_id == merchant_id, OptIn.created_ym == ym)
    total_cents, count = session.exec(q).one()
    return int(total_cents or 0), int(count or 0)

def list_optins(session: Session, merchant_id: int, ym: str, limit: int = 50) -> List[OptIn]:
    q = (
        select(OptIn)
        .where(OptIn.merchant_id == merchant_id, OptIn.created_ym == ym)
        .order_by(OptIn.created_at.desc())
        .limit(limit)
    )
    return list(session.exec(q).all())
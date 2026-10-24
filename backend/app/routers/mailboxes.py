from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from ..db import get_db
from ..auth import get_current_admin
from ..models import Mailbox
from datetime import datetime

router = APIRouter(prefix="/mailboxes", tags=["mailboxes"])


class MailboxCreate(BaseModel):
    email: str
    smtp_host: str
    smtp_port: int = 587
    username: str
    password: str
    daily_cap: int = 5
    warmup_enabled: bool = True
    status: str = "warming"


class MailboxUpdate(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    daily_cap: Optional[int] = None
    warmup_enabled: Optional[bool] = None
    status: Optional[str] = None


@router.get("/")
async def list_mailboxes(db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    res = await db.execute(select(Mailbox).order_by(Mailbox.created_at.desc()))
    items = []
    for m in res.scalars():
        items.append({
            "id": str(m.id),
            "email": m.email,
            "domain": m.domain,
            "smtp_host": m.smtp_host,
            "smtp_port": m.smtp_port,
            "daily_cap": m.daily_cap,
            "warmup_enabled": m.warmup_enabled,
            "emails_sent_today": m.emails_sent_today,
            "total_sent": m.total_sent,
            "status": m.status,
            "consecutive_errors": m.consecutive_errors,
            "last_error_at": m.last_error_at.isoformat() if m.last_error_at else None,
            "username": m.username,
            "password": m.password,
            "created_at": m.created_at.isoformat(),
        })
    return {"items": items}


@router.post("/")
async def create_mailbox(req: MailboxCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    domain = req.email.split('@')[-1].lower()
    m = Mailbox(
        email=req.email.lower(),
        domain=domain,
        smtp_host=req.smtp_host,
        smtp_port=req.smtp_port,
        username=req.username,
        password=req.password,
        daily_cap=req.daily_cap,
        warmup_enabled=req.warmup_enabled,
        status=req.status,
        warmup_started_at=datetime.utcnow() if req.status == "warming" else None,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return {"id": str(m.id)}


@router.put("/{mailbox_id}")
async def update_mailbox(mailbox_id: str, req: MailboxUpdate, db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    from uuid import UUID
    res = await db.execute(select(Mailbox).where(Mailbox.id == UUID(mailbox_id)))
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in req.dict(exclude_unset=True).items():
        setattr(m, k, v)
    m.updated_at = datetime.utcnow()
    await db.commit()
    return {"ok": True}


@router.delete("/{mailbox_id}")
async def delete_mailbox(mailbox_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    from uuid import UUID
    res = await db.execute(select(Mailbox).where(Mailbox.id == UUID(mailbox_id)))
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(m)
    await db.commit()
    return {"ok": True}


@router.post("/{mailbox_id}/test")
async def test_mailbox(
    mailbox_id: str,
    to_email: str = "test@example.com",
    subject: str = "Test",
    body: str = "Hello",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_admin),
):
    from uuid import UUID
    from ..services.sender import send_via_mailbox
    res = await db.execute(select(Mailbox).where(Mailbox.id == UUID(mailbox_id)))
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    result = await send_via_mailbox(m, to_email, subject, body)
    return {"ok": result.success, "error": result.error}

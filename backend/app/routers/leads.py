from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from pydantic import BaseModel
from typing import Optional, List
import csv
import io
from uuid import UUID
from ..db import get_db
from ..auth import get_current_admin
from ..models import Lead, Suppression, CampaignLead
from ..services.suppression import is_suppressed

router = APIRouter(prefix="/leads", tags=["leads"])


class LeadCreate(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    custom_fields: Optional[dict] = None
    source: Optional[str] = None


class BulkAction(BaseModel):
    lead_ids: List[str]
    action: str  # suppress|unsuppress|delete|activate


@router.get("/")
async def list_leads(limit: int = 500, offset: int = 0, q: str = None, status: str = None, db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    stmt = select(Lead).order_by(Lead.created_at.desc())
    if status:
        stmt = stmt.where(Lead.status == status)
    if q:
        stmt = stmt.where(Lead.email.ilike(f"%{q}%") | Lead.first_name.ilike(f"%{q}%") | Lead.last_name.ilike(f"%{q}%") | Lead.company.ilike(f"%{q}%"))
    res = await db.execute(stmt.offset(offset).limit(limit))
    total = await db.execute(select(func.count(Lead.id)))
    items = []
    for l in res.scalars():
        items.append({
            "id": str(l.id),
            "email": l.email,
            "first_name": l.first_name,
            "last_name": l.last_name,
            "company": l.company,
            "title": l.title,
            "phone": l.phone,
            "website": l.website,
            "status": l.status,
            "source": l.source,
            "created_at": l.created_at.isoformat(),
        })
    return {"items": items, "total": total.scalar_one()}


@router.post("/")
async def create_lead(req: LeadCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    email_l = req.email.lower().strip()
    if await is_suppressed(db, email_l):
        raise HTTPException(status_code=400, detail="Email suppressed")
    lead = Lead(
        email=email_l,
        first_name=req.first_name,
        last_name=req.last_name,
        company=req.company,
        title=req.title,
        website=req.website,
        phone=req.phone,
        custom_fields=req.custom_fields or {},
        source=req.source or "manual",
    )
    db.add(lead)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Lead exists or invalid")
    await db.refresh(lead)
    return {"id": str(lead.id)}


@router.post("/upload")
async def upload_leads(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    content = await file.read()
    text = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(text))
    added = 0
    skipped = 0
    for row in reader:
        email = (row.get('email') or row.get('Email') or '').lower().strip()
        if not email:
            skipped += 1
            continue
        if await is_suppressed(db, email):
            skipped += 1
            continue
        res = await db.execute(select(Lead).where(Lead.email == email))
        if res.scalar_one_or_none():
            skipped += 1
            continue
        lead = Lead(
            email=email,
            first_name=row.get('first_name') or row.get('First Name') or row.get('firstName') or row.get('first_name'),
            last_name=row.get('last_name') or row.get('Last Name') or row.get('lastName'),
            company=row.get('company') or row.get('Company'),
            title=row.get('title') or row.get('Title'),
            website=row.get('website') or row.get('Website'),
            phone=row.get('phone') or row.get('Phone'),
            custom_fields={k: v for k, v in row.items() if k.lower() not in ['email', 'first_name', 'firstname', 'last_name', 'lastname', 'company', 'title', 'website', 'phone'] and v},
            source="csv",
        )
        db.add(lead)
        added += 1
    await db.commit()
    return {"added": added, "skipped": skipped}


@router.post("/bulk")
async def bulk_action(action: BulkAction, db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    if not action.lead_ids:
        raise HTTPException(status_code=400, detail="No leads selected")
    if action.action == "delete":
        for lid in action.lead_ids:
            try:
                await db.execute(delete(Lead).where(Lead.id == UUID(lid)))
            except Exception:
                continue
        await db.commit()
        return {"ok": True, "action": "delete"}
    elif action.action == "suppress":
        for lid in action.lead_ids:
            try:
                res = await db.execute(select(Lead).where(Lead.id == UUID(lid)))
                lead = res.scalar_one_or_none()
                if lead and lead.status != "suppressed":
                    lead.status = "suppressed"
                    db.add(Suppression(email=lead.email.lower(), reason="manual"))
            except Exception:
                continue
        await db.commit()
        return {"ok": True, "action": "suppress"}
    elif action.action == "activate":
        for lid in action.lead_ids:
            try:
                res = await db.execute(select(Lead).where(Lead.id == UUID(lid)))
                lead = res.scalar_one_or_none()
                if lead:
                    lead.status = "active"
            except Exception:
                continue
        await db.commit()
        return {"ok": True, "action": "activate"}
    elif action.action == "unsuppress":
        for lid in action.lead_ids:
            try:
                res = await db.execute(select(Lead).where(Lead.id == UUID(lid)))
                lead = res.scalar_one_or_none()
                if lead:
                    lead.status = "active"
                await db.execute(delete(Suppression).where(Suppression.email == lead.email.lower() if lead else ""))
            except Exception:
                continue
        await db.commit()
        return {"ok": True, "action": "unsuppress"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

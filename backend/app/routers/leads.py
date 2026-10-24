from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
import csv
import io
from ..db import get_db
from ..auth import get_current_admin
from ..models import Lead, Suppression
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


@router.get("/")
async def list_leads(limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    res = await db.execute(select(Lead).order_by(Lead.created_at.desc()).limit(limit).offset(offset))
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
            first_name=row.get('first_name') or row.get('First Name') or row.get('firstName'),
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

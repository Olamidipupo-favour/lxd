from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from ..db import get_db
from ..models import EmailMessage, TrackingEvent, Lead
from ..config import settings
from ..utils import gen_tracking_token
import base64

router = APIRouter()

PIXEL = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==")


@router.get("/o/{token}.gif")
async def open_pixel(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    # log open
    res = await db.execute(select(EmailMessage).where(EmailMessage.tracking_token == token))
    em = res.scalar_one_or_none()
    if em:
        await db.execute(update(EmailMessage).where(EmailMessage.id == em.id).values(opened_at=em.opened_at or datetime.utcnow()))
        ev = TrackingEvent(
            tracking_token=token,
            email_message_id=em.id,
            lead_id=em.lead_id,
            campaign_id=em.campaign_id,
            event_type="open",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            referer=request.headers.get("referer"),
            meta={},
        )
        db.add(ev)
        await db.commit()
    return Response(content=PIXEL, media_type="image/gif")


@router.get("/c/{token}")
async def click_redirect(token: str, request: Request, to: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(EmailMessage).where(EmailMessage.tracking_token == token))
    em = res.scalar_one_or_none()
    if em:
        await db.execute(update(EmailMessage).where(EmailMessage.id == em.id).values(clicked_at=em.clicked_at or datetime.utcnow()))
        ev = TrackingEvent(
            tracking_token=token,
            email_message_id=em.id,
            lead_id=em.lead_id,
            campaign_id=em.campaign_id,
            event_type="click",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            referer=request.headers.get("referer"),
            target_url=to,
            meta={},
        )
        db.add(ev)
        await db.commit()
    return RedirectResponse(url=to, status_code=302)


@router.get(settings.UNSUB_PATH)
async def unsubscribe(request: Request, token: str = None, db: AsyncSession = Depends(get_db)):
    if not token:
        return HTMLResponse("<html><body>Invalid unsubscribe link</body></html>", status_code=400)
    res = await db.execute(select(EmailMessage).where(EmailMessage.tracking_token == token))
    em = res.scalar_one_or_none()
    if em and em.lead_id:
        lead_res = await db.execute(select(Lead).where(Lead.id == em.lead_id))
        lead = lead_res.scalar_one_or_none()
        if lead:
            lead.status = "unsubscribed"
        await db.execute(update(EmailMessage).where(EmailMessage.id == em.id).values(unsubscribed_at=datetime.utcnow()))
        from ..models import Suppression
        # add suppression
        from sqlalchemy import select as sselect
        sres = await db.execute(sselect(Suppression).where(Suppression.email == em.to_email.lower()))
        if not sres.scalar_one_or_none():
            db.add(Suppression(email=em.to_email.lower(), reason="unsubscribe"))
        ev = TrackingEvent(
            tracking_token=token,
            email_message_id=em.id,
            lead_id=em.lead_id,
            campaign_id=em.campaign_id,
            event_type="unsubscribe",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            meta={},
        )
        db.add(ev)
        await db.commit()
    return HTMLResponse("<html><body><h2>Unsubscribed</h2><p>You have been unsubscribed successfully.</p></body></html>")

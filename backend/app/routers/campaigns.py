from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import asyncio
from ..db import get_db
from ..auth import get_current_admin
from ..models import Campaign, CampaignLead, Lead, Mailbox, EmailMessage, TrackingEvent
from ..services.suppression import is_suppressed
from ..services.sender import send_via_mailbox
from ..services.personalization import personalize
from ..utils import gen_tracking_token, build_tracking_pixel_url, build_click_url, build_unsub_url
from ..config import settings

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class CampaignCreate(BaseModel):
    name: str
    subject_template: str
    body_template: str
    from_name: Optional[str] = None
    mailbox_id: Optional[str] = None
    domain_filter: Optional[str] = None
    throttle_per_hour: int = 200
    daily_limit: int = 10000
    status: str = "draft"
    schedule_at: Optional[datetime] = None
    unsubscribe_enabled: bool = True
    track_opens: bool = True
    track_clicks: bool = True


@router.get("/")
async def list_campaigns(db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    res = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    items = []
    for c in res.scalars():
        items.append({
            "id": str(c.id),
            "name": c.name,
            "status": c.status,
            "daily_limit": c.daily_limit,
            "created_at": c.created_at.isoformat(),
        })
    return {"items": items}


@router.post("/")
async def create_campaign(req: CampaignCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    data = req.dict()
    if data.get("mailbox_id") == "":
        data["mailbox_id"] = None
    c = Campaign(**data)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return {"id": str(c.id)}


@router.post("/{campaign_id}/populate")
async def populate_campaign(campaign_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    from uuid import UUID
    res = await db.execute(select(Campaign).where(Campaign.id == UUID(campaign_id)))
    campaign = res.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Not found")
    # add all active leads not suppressed
    leads_res = await db.execute(select(Lead).where(Lead.status == "active"))
    added = 0
    for lead in leads_res.scalars():
        if await is_suppressed(db, lead.email):
            continue
        cl = CampaignLead(campaign_id=campaign.id, lead_id=lead.id, status="pending")
        db.add(cl)
        try:
            await db.flush()
            added += 1
        except Exception:
            await db.rollback()
            continue
    await db.commit()
    return {"added": added}


@router.post("/{campaign_id}/run")
async def run_campaign(campaign_id: str, db: AsyncSession = Depends(get_db), x_cron_secret: Optional[str] = Header(None)):
    if settings.INTERNAL_CRON_SECRET and x_cron_secret != settings.INTERNAL_CRON_SECRET:
        raise HTTPException(status_code=401, detail="unauthorized")
    from uuid import UUID
    res = await db.execute(select(Campaign).where(Campaign.id == UUID(campaign_id)))
    campaign = res.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Not found")
    if campaign.status not in ["scheduled", "running", "draft"]:  # allow manual trigger
        pass
    if campaign.status == "completed":
        return {"ok": False, "reason": "completed"}
    campaign.status = "running"
    await db.commit()

    # pick mailbox
    mb_res = await db.execute(select(Mailbox).where(Mailbox.status.in_(["active", "warming"])))
    mailboxes = list(mb_res.scalars())
    if not mailboxes:
        return {"ok": False, "reason": "no_mailboxes"}

    sent = 0
    # get pending leads
    cl_res = await db.execute(select(CampaignLead).where(CampaignLead.campaign_id == campaign.id, CampaignLead.status == "pending").limit(campaign.daily_limit))
    for cl in cl_res.scalars():
        if sent >= campaign.daily_limit:
            break
        lres = await db.execute(select(Lead).where(Lead.id == cl.lead_id))
        lead = lres.scalar_one_or_none()
        if not lead or lead.status != "active" or await is_suppressed(db, lead.email):
            cl.status = "skipped"
            await db.commit()
            continue
        # pick mailbox with capacity
        mailbox = None
        for m in mailboxes:
            if m.emails_sent_today < m.daily_cap:
                mailbox = m
                break
        if not mailbox:
            break  # no capacity
        # personalize
        lead_dict = {"email": lead.email, "first_name": lead.first_name, "last_name": lead.last_name, "company": lead.company, "title": lead.title, "custom_fields": lead.custom_fields or {}}
        subject = personalize(campaign.subject_template, lead_dict)
        body = personalize(campaign.body_template, lead_dict)
        token = gen_tracking_token()
        # inject tracking
        pixel = build_tracking_pixel_url(settings.API_BASE_URL, settings.TRACKING_DOMAIN, token)
        pixel_tag = f'<img src="{pixel}" width="1" height="1" style="display:none;" />' if campaign.track_opens else ''
        # rewrite links for clicks - simple: replace http links
        import re
        def repl_link(m):
            url = m.group(0)
            c_url = build_click_url(settings.API_BASE_URL, settings.TRACKING_DOMAIN, token, url)
            return c_url
        html_body = body
        if campaign.track_clicks:
            html_body = re.sub(r'https?://[^\s"\'>]+', repl_link, html_body)
        html_body = html_body + pixel_tag
        unsub_tag = ''
        if campaign.unsubscribe_enabled:
            unsub_url = build_unsub_url(settings.API_BASE_URL, settings.TRACKING_DOMAIN, token)
            unsub_tag = f'<br><br><a href="{unsub_url}">Unsubscribe</a>'
            html_body = html_body + unsub_tag
        # send
        res_send = await send_via_mailbox(mailbox, lead.email, subject, html_body, None, campaign.from_name)
        if res_send.success:
            em = EmailMessage(campaign_id=campaign.id, lead_id=lead.id, mailbox_id=mailbox.id, message_id=res_send.message_id, to_email=lead.email, from_email=mailbox.email, subject=subject, tracking_token=token, status="sent")
            db.add(em)
            cl.status = "sent"
            cl.sent_at = datetime.utcnow()
            mailbox.emails_sent_today += 1
            mailbox.total_sent += 1
            sent += 1
            await db.commit()
        else:
            cl.status = "failed"
            cl.error = res_send.error
            mailbox.consecutive_errors += 1
            mailbox.last_error = res_send.error
            mailbox.last_error_at = datetime.utcnow()
            if mailbox.consecutive_errors >= 5:
                mailbox.status = "quarantined"
            await db.commit()
        await asyncio.sleep(1)  # basic throttle
    return {"ok": True, "sent": sent}

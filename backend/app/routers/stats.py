from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..db import get_db
from ..auth import get_current_admin
from ..models import EmailMessage, TrackingEvent, Lead, Campaign, Mailbox

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db), user=Depends(get_current_admin)):
    sent = await db.execute(select(func.count(EmailMessage.id)))
    opens = await db.execute(select(func.count(EmailMessage.id)).where(EmailMessage.opened_at.isnot(None)))
    clicks = await db.execute(select(func.count(EmailMessage.id)).where(EmailMessage.clicked_at.isnot(None)))
    replies = await db.execute(select(func.count(EmailMessage.id)).where(EmailMessage.replied_at.isnot(None)))
    unsubs = await db.execute(select(func.count(EmailMessage.id)).where(EmailMessage.unsubscribed_at.isnot(None)))
    leads = await db.execute(select(func.count(Lead.id)))
    campaigns = await db.execute(select(func.count(Campaign.id)))
    mailboxes = await db.execute(select(func.count(Mailbox.id)).where(Mailbox.status == "active"))
    return {
        "sent": sent.scalar_one(),
        "opens": opens.scalar_one(),
        "clicks": clicks.scalar_one(),
        "replies": replies.scalar_one(),
        "unsubs": unsubs.scalar_one(),
        "leads": leads.scalar_one(),
        "campaigns": campaigns.scalar_one(),
        "active_mailboxes": mailboxes.scalar_one(),
    }

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Suppression, Lead


async def is_suppressed(db: AsyncSession, email: str) -> bool:
    email_l = email.lower().strip()
    res = await db.execute(select(Suppression).where(Suppression.email == email_l))
    if res.scalar_one_or_none():
        return True
    res = await db.execute(select(Lead).where(Lead.email == email_l, Lead.status.in_(["bounced", "unsubscribed", "suppressed"])))
    if res.scalar_one_or_none():
        return True
    return False


async def add_suppression(db: AsyncSession, email: str, reason: str = "manual"):
    email_l = email.lower().strip()
    from ..models import Suppression
    sup = Suppression(email=email_l, reason=reason)
    db.add(sup)
    await db.commit()
    return sup

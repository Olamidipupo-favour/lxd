import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, BigInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .db import Base


def gen_uuid():
    return uuid.uuid4()


class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    role = Column(String(32), default="admin")  # admin|user|viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)


class Mailbox(Base):
    __tablename__ = "mailboxes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, nullable=False, default=587)
    username = Column(String(255), nullable=False)
    password = Column(Text, nullable=False)  # app password / token (store encrypted in prod ideally)
    daily_cap = Column(Integer, default=5)
    warmup_enabled = Column(Boolean, default=True)
    warmup_started_at = Column(DateTime, nullable=True)
    emails_sent_today = Column(Integer, default=0)
    total_sent = Column(BigInteger, default=0)
    status = Column(String(32), default="warming")  # active|warming|quarantined|paused
    last_error_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    consecutive_errors = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Lead(Base):
    __tablename__ = "leads"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    company = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)
    custom_fields = Column(JSON, default=dict)
    source = Column(String(64), nullable=True)
    status = Column(String(32), default="active")  # active|bounced|unsubscribed|suppressed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint("email", name="uq_lead_email"),)


class Suppression(Base):
    __tablename__ = "suppressions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    reason = Column(String(64), nullable=True)  # unsubscribe|bounce|complaint|manual
    created_at = Column(DateTime, default=datetime.utcnow)


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subject_template = Column(Text, nullable=False)
    body_template = Column(Text, nullable=False)  # html or text; supports {{first_name}} etc
    from_name = Column(String(128), nullable=True)
    mailbox_id = Column(UUID(as_uuid=True), ForeignKey("mailboxes.id"), nullable=True)
    domain_filter = Column(String(255), nullable=True)
    throttle_per_hour = Column(Integer, default=200)
    daily_limit = Column(Integer, default=10000)
    status = Column(String(32), default="draft")  # draft|scheduled|running|paused|completed
    schedule_at = Column(DateTime, nullable=True)
    unsubscribe_enabled = Column(Boolean, default=True)
    track_opens = Column(Boolean, default=True)
    track_clicks = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    mailbox = relationship("Mailbox")


class CampaignLead(Base):
    __tablename__ = "campaign_leads"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), default="pending")  # pending|sent|failed|skipped
    sent_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("campaign_id", "lead_id", name="uq_campaign_lead"),)


class EmailMessage(Base):
    __tablename__ = "email_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True, index=True)
    mailbox_id = Column(UUID(as_uuid=True), ForeignKey("mailboxes.id"), nullable=True, index=True)
    message_id = Column(String(512), nullable=True)
    to_email = Column(String(255), nullable=False, index=True)
    from_email = Column(String(255), nullable=False)
    subject = Column(Text, nullable=True)
    tracking_token = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(32), default="sent")  # sent|failed|bounced
    sent_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    unsubscribed_at = Column(DateTime, nullable=True)


class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_token = Column(String(64), index=True, nullable=False)
    email_message_id = Column(UUID(as_uuid=True), ForeignKey("email_messages.id"), nullable=True)
    lead_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    campaign_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    event_type = Column(String(32), nullable=False)  # open|click|reply|unsubscribe
    ip = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    referer = Column(Text, nullable=True)
    target_url = Column(Text, nullable=True)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

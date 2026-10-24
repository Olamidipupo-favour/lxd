-- Cold Email System Schema for Supabase/Postgres

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS admin_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  last_login_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mailboxes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  domain VARCHAR(255) NOT NULL,
  smtp_host VARCHAR(255) NOT NULL,
  smtp_port INTEGER NOT NULL DEFAULT 587,
  username VARCHAR(255) NOT NULL,
  password TEXT NOT NULL,
  daily_cap INTEGER DEFAULT 5,
  warmup_enabled BOOLEAN DEFAULT TRUE,
  warmup_started_at TIMESTAMP,
  emails_sent_today INTEGER DEFAULT 0,
  total_sent BIGINT DEFAULT 0,
  status VARCHAR(32) DEFAULT 'warming',
  last_error_at TIMESTAMP,
  last_error TEXT,
  consecutive_errors INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  first_name VARCHAR(128),
  last_name VARCHAR(128),
  company VARCHAR(255),
  title VARCHAR(255),
  website VARCHAR(255),
  phone VARCHAR(64),
  custom_fields JSONB DEFAULT '{}'::jsonb,
  source VARCHAR(64),
  status VARCHAR(32) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS suppressions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  reason VARCHAR(64),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  subject_template TEXT NOT NULL,
  body_template TEXT NOT NULL,
  from_name VARCHAR(128),
  mailbox_id UUID REFERENCES mailboxes(id),
  domain_filter VARCHAR(255),
  throttle_per_hour INTEGER DEFAULT 200,
  daily_limit INTEGER DEFAULT 10000,
  status VARCHAR(32) DEFAULT 'draft',
  schedule_at TIMESTAMP,
  unsubscribe_enabled BOOLEAN DEFAULT TRUE,
  track_opens BOOLEAN DEFAULT TRUE,
  track_clicks BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS campaign_leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE NOT NULL,
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE NOT NULL,
  status VARCHAR(32) DEFAULT 'pending',
  sent_at TIMESTAMP,
  error TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(campaign_id, lead_id)
);

CREATE TABLE IF NOT EXISTS email_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID REFERENCES campaigns(id),
  lead_id UUID REFERENCES leads(id),
  mailbox_id UUID REFERENCES mailboxes(id),
  message_id VARCHAR(512),
  to_email VARCHAR(255) NOT NULL,
  from_email VARCHAR(255) NOT NULL,
  subject TEXT,
  tracking_token VARCHAR(64) UNIQUE NOT NULL,
  status VARCHAR(32) DEFAULT 'sent',
  sent_at TIMESTAMP DEFAULT NOW(),
  opened_at TIMESTAMP,
  clicked_at TIMESTAMP,
  replied_at TIMESTAMP,
  unsubscribed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tracking_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tracking_token VARCHAR(64) NOT NULL,
  email_message_id UUID REFERENCES email_messages(id),
  lead_id UUID,
  campaign_id UUID,
  event_type VARCHAR(32) NOT NULL,
  ip VARCHAR(64),
  user_agent TEXT,
  referer TEXT,
  target_url TEXT,
  meta JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_mailboxes_domain ON mailboxes(domain);
CREATE INDEX IF NOT EXISTS idx_email_messages_token ON email_messages(tracking_token);
CREATE INDEX IF NOT EXISTS idx_tracking_events_token ON tracking_events(tracking_token);
CREATE INDEX IF NOT EXISTS idx_campaign_leads_status ON campaign_leads(campaign_id, status);

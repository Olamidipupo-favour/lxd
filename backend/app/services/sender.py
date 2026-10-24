import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid
from typing import Optional, Dict, Any
from ..models import Mailbox


class SendResult:
    def __init__(self, success: bool, message_id: Optional[str] = None, error: Optional[str] = None):
        self.success = success
        self.message_id = message_id
        self.error = error


async def send_via_mailbox(mailbox: Mailbox, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None, from_name: Optional[str] = None, extra_headers: Optional[Dict[str, str]] = None) -> SendResult:
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((from_name or mailbox.email.split('@')[0], mailbox.email))
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Message-ID'] = make_msgid(domain=mailbox.domain)
        if extra_headers:
            for k, v in extra_headers.items():
                msg[k] = v
        if text_body:
            part1 = MIMEText(text_body, 'plain')
            msg.attach(part1)
        part2 = MIMEText(html_body, 'html')
        msg.attach(part2)

        await aiosmtplib.send(
            msg,
            hostname=mailbox.smtp_host,
            port=mailbox.smtp_port,
            username=mailbox.username,
            password=mailbox.password,
            start_tls=True,
            timeout=30,
        )
        return SendResult(success=True, message_id=msg['Message-ID'])
    except Exception as e:
        return SendResult(success=False, error=str(e))

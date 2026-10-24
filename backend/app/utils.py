import secrets
import string
from urllib.parse import quote_plus


def gen_tracking_token(n: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(n))


def build_tracking_pixel_url(api_base: str, tracking_domain: str, token: str) -> str:
    base = tracking_domain or api_base
    # if tracking_domain is set, construct URL to backend via that host (reverse proxy should route /o)
    if tracking_domain:
        return f"https://{tracking_domain}/o/{token}.gif"
    return f"{api_base}/o/{token}.gif"


def build_click_url(api_base: str, tracking_domain: str, token: str, real_url: str) -> str:
    base = tracking_domain or api_base
    if tracking_domain:
        return f"https://{tracking_domain}/c/{token}?to={quote_plus(real_url)}"
    return f"{api_base}/c/{token}?to={quote_plus(real_url)}"


def build_unsub_url(api_base: str, tracking_domain: str, token: str) -> str:
    base = tracking_domain or api_base
    if tracking_domain:
        return f"https://{tracking_domain}/unsubscribe?token={token}"
    return f"{api_base}/unsubscribe?token={token}"

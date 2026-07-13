"""HTML escaping and URL hardening for unsafe_allow_html surfaces."""
from __future__ import annotations

import html
from urllib.parse import urlparse

_ALLOWED_URL_SCHEMES = frozenset({"http", "https"})


def esc(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def esc_attr(value) -> str:
    """Escape for use inside HTML attribute double-quotes."""
    return esc(value)


def safe_url(value, *, fallback: str = "#") -> str:
    """Allow only http/https URLs (blocks javascript:, data:, etc.)."""
    if value is None:
        return fallback
    raw = str(value).strip()
    if not raw:
        return fallback
    parsed = urlparse(raw)
    scheme = (parsed.scheme or "").lower()
    if scheme not in _ALLOWED_URL_SCHEMES:
        return fallback
    if not parsed.netloc:
        return fallback
    return esc_attr(raw)


def safe_img_url(value, *, fallback: str = "") -> str:
    """Same as safe_url but empty fallback for optional <img src>."""
    if value is None or (isinstance(value, float) and value != value):
        return fallback
    raw = str(value).strip()
    if not raw:
        return fallback
    return safe_url(raw, fallback=fallback)

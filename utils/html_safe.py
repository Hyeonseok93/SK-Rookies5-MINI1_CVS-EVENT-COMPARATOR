"""HTML escaping helpers for unsafe_allow_html surfaces."""
from __future__ import annotations

import html


def esc(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def esc_attr(value) -> str:
    """Escape for use inside HTML attribute double-quotes."""
    return esc(value)

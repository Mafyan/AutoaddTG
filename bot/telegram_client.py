"""Helpers for constructing Telegram clients with proxy support."""

from __future__ import annotations

import logging
from typing import Optional

from telegram import Bot
from telegram.ext import Application
from telegram.request import HTTPXRequest

from config import settings

logger = logging.getLogger(__name__)


def _build_request(proxy_url: Optional[str] = None) -> HTTPXRequest:
    proxy_url = (proxy_url or settings.TELEGRAM_PROXY_URL or "").strip()
    # curl supports socks5h:// (remote DNS), but httpx/telegram expects socks5://.
    # If user configured socks5h://, normalize it to socks5:// to avoid startup failure.
    if proxy_url.lower().startswith("socks5h://"):
        proxy_url = "socks5://" + proxy_url[len("socks5h://") :]
        logger.warning("Proxy scheme socks5h:// is not supported here; using %s", proxy_url)
    timeouts = {
        "connect_timeout": settings.TELEGRAM_CONNECT_TIMEOUT,
        "read_timeout": settings.TELEGRAM_READ_TIMEOUT,
        "write_timeout": settings.TELEGRAM_WRITE_TIMEOUT,
        "pool_timeout": settings.TELEGRAM_POOL_TIMEOUT,
    }
    if proxy_url:
        if proxy_url.startswith("socks") and proxy_url.endswith(":1080"):
            logger.info("Using SOCKS proxy for Telegram: %s", proxy_url)
        else:
            logger.info("Using proxy for Telegram: %s", proxy_url)
        return HTTPXRequest(proxy_url=proxy_url, **timeouts)
    return HTTPXRequest(**timeouts)


def get_bot(token: str, proxy_url: Optional[str] = None) -> Bot:
    """Create a Bot configured to use the proxy (if set)."""
    return Bot(token=token, request=_build_request(proxy_url))


def get_application(token: str, proxy_url: Optional[str] = None) -> Application:
    """Create an Application configured to use the proxy (if set)."""
    return Application.builder().token(token).request(_build_request(proxy_url)).build()


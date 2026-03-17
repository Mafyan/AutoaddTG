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
    if proxy_url:
        if proxy_url.startswith("socks") and proxy_url.endswith(":1080"):
            logger.info("Using SOCKS proxy for Telegram: %s", proxy_url)
        else:
            logger.info("Using proxy for Telegram: %s", proxy_url)
        return HTTPXRequest(proxy_url=proxy_url)
    return HTTPXRequest()


def get_bot(token: str, proxy_url: Optional[str] = None) -> Bot:
    """Create a Bot configured to use the proxy (if set)."""
    return Bot(token=token, request=_build_request(proxy_url))


def get_application(token: str, proxy_url: Optional[str] = None) -> Application:
    """Create an Application configured to use the proxy (if set)."""
    return Application.builder().token(token).request(_build_request(proxy_url)).build()


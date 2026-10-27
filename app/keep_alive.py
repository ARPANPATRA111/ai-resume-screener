"""Keep the free Render instance from going to sleep.

Render spins a free web service down after 15 minutes without incoming
traffic. While the app is running, this task calls its own public URL every
few minutes, which counts as incoming traffic and keeps the instance awake.
"""

import asyncio
import logging
import os
import urllib.request

logger = logging.getLogger("uvicorn.error")

DEFAULT_INTERVAL = 300  # seconds, well under Render's 15 minute idle limit


def get_public_url() -> str | None:
    """Public URL of this app, or None when running locally."""
    # Render sets RENDER_EXTERNAL_URL automatically, KEEP_ALIVE_URL covers other hosts
    url = os.getenv("KEEP_ALIVE_URL") or os.getenv("RENDER_EXTERNAL_URL")
    return url.rstrip("/") if url else None


def ping(url: str) -> int:
    with urllib.request.urlopen(f"{url}/api/health", timeout=30) as response:
        return response.status


async def keep_alive(url: str, interval: int) -> None:
    logger.info("Keep-alive enabled: pinging %s every %ss", url, interval)
    while True:
        await asyncio.sleep(interval)
        try:
            status = await asyncio.to_thread(ping, url)
            logger.info("Keep-alive ping returned %s", status)
        except Exception as error:
            logger.warning("Keep-alive ping failed: %s", error)


def start_keep_alive() -> asyncio.Task | None:
    url = get_public_url()
    if url is None:
        return None
    interval = int(os.getenv("KEEP_ALIVE_INTERVAL", DEFAULT_INTERVAL))
    return asyncio.create_task(keep_alive(url, interval))

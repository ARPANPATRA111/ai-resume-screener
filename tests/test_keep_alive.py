import asyncio

from app import keep_alive


def test_disabled_when_no_public_url(monkeypatch):
    monkeypatch.delenv("KEEP_ALIVE_URL", raising=False)
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    assert keep_alive.get_public_url() is None


def test_uses_render_url(monkeypatch):
    monkeypatch.delenv("KEEP_ALIVE_URL", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://screener.onrender.com/")
    assert keep_alive.get_public_url() == "https://screener.onrender.com"


def test_pings_health_endpoint_and_survives_errors(monkeypatch):
    calls = []

    def fake_ping(url):
        calls.append(url)
        if len(calls) == 1:
            raise OSError("network down")
        return 200

    monkeypatch.setattr(keep_alive, "ping", fake_ping)

    async def run():
        task = asyncio.create_task(keep_alive.keep_alive("https://example.com", interval=0.01))
        await asyncio.sleep(0.1)
        task.cancel()

    asyncio.run(run())
    assert len(calls) >= 2

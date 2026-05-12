from __future__ import annotations

import asyncio

import httpx


async def fetch_bytes(
    url: str,
    auth: tuple[str, str] | None,
    timeout_seconds: int,
    max_retries: int,
) -> bytes:
    """Fetch bytes with retries."""
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
                response = await client.get(url, auth=auth)
                response.raise_for_status()
                return response.content
        except httpx.HTTPError as exc:
            last_error = exc
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError("Failed to fetch bytes")

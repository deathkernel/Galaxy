import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

NASA_BASE = "https://api.nasa.gov"
JPL_SBDB = "https://ssd-api.jpl.nasa.gov/sbdb.api"


class SpaceLookup:
    """Aggregate public astronomy data into one normalized response."""

    def __init__(self) -> None:
        self.api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")

    async def _get(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def _nasa_apod(self, query: str) -> dict[str, Any] | None:
        # APOD is not a general object database, but it gives useful
        # astronomy context when the name appears in its imagery metadata.
        try:
            data = await self._get(
                f"{NASA_BASE}/planetary/apod",
                {"api_key": self.api_key, "count": 20},
            )
        except (httpx.HTTPError, ValueError):
            return None

        items = data if isinstance(data, list) else [data]
        needle = query.casefold()
        for item in items:
            haystack = " ".join(
                str(item.get(key, "")) for key in ("title", "explanation", "copyright")
            ).casefold()
            if needle in haystack:
                return {
                    "title": item.get("title"),
                    "date": item.get("date"),
                    "media_type": item.get("media_type"),
                    "url": item.get("url"),
                    "hdurl": item.get("hdurl"),
                    "explanation": item.get("explanation"),
                }
        return None

    async def _jpl_small_body(self, query: str) -> dict[str, Any] | None:
        try:
            data = await self._get(JPL_SBDB, {"sstr": query})
        except (httpx.HTTPError, ValueError):
            return None

        if data.get("code") and data.get("code") != "200":
            return None
        if not data.get("object"):
            return None

        obj = data["object"]
        return {
            "name": obj.get("fullname") or obj.get("des") or query,
            "designation": obj.get("des"),
            "kind": obj.get("kind"),
            "orbit_id": (data.get("orbit") or {}).get("orbit_id"),
            "jpl_url": obj.get("prefix"),
            "source": "JPL Small-Body Database",
        }

    async def search(self, query: str) -> dict[str, Any]:
        clean = " ".join(query.strip().split())
        if not clean:
            return {"query": query, "matches": [], "message": "Enter a space object name."}

        asteroid = await self._jpl_small_body(clean)
        apod = await self._nasa_apod(clean)

        matches: list[dict[str, Any]] = []

        if asteroid:
            matches.append({
                "type": "small_body",
                "name": asteroid.get("name"),
                "details": asteroid,
            })

        if apod:
            matches.append({
                "type": "astronomy_picture",
                "name": apod.get("title"),
                "details": apod,
            })

        if not matches:
            return {
                "query": clean,
                "matches": [],
                "message": (
                    "No match was found in the V1 sources. "
                    "More astronomy catalogs will be added next."
                ),
                "sources": ["NASA APOD", "JPL Small-Body Database"],
            }

        return {
            "query": clean,
            "matches": matches,
            "sources": ["NASA APOD", "JPL Small-Body Database"],
        }

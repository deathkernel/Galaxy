import asyncio
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

NASA_BASE = "https://api.nasa.gov"
JPL_SBDB = "https://ssd-api.jpl.nasa.gov/sbdb.api"
WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary"

SOLAR_SYSTEM: dict[str, dict[str, Any]] = {
    "sun": {"type": "star", "name": "Sun", "mass": "1.989 × 10^30 kg", "radius": "696,340 km", "description": "The star at the center of the Solar System."},
    "mercury": {"type": "planet", "name": "Mercury", "distance_from_sun": "57.9 million km", "radius": "2,439.7 km", "moons": 0, "description": "The smallest planet and the closest planet to the Sun."},
    "venus": {"type": "planet", "name": "Venus", "distance_from_sun": "108.2 million km", "radius": "6,051.8 km", "moons": 0, "description": "A rocky planet with a dense carbon-dioxide atmosphere."},
    "earth": {"type": "planet", "name": "Earth", "distance_from_sun": "149.6 million km", "radius": "6,371 km", "moons": 1, "description": "The third planet from the Sun and the only world currently known to support life."},
    "mars": {"type": "planet", "name": "Mars", "distance_from_sun": "227.9 million km", "radius": "3,389.5 km", "moons": 2, "description": "A cold, rocky planet known for its iron-rich surface and polar ice caps."},
    "jupiter": {"type": "planet", "name": "Jupiter", "distance_from_sun": "778.5 million km", "radius": "69,911 km", "moons": 95, "description": "The largest planet in the Solar System and a gas giant."},
    "saturn": {"type": "planet", "name": "Saturn", "distance_from_sun": "1.43 billion km", "radius": "58,232 km", "moons": 274, "description": "A gas giant famous for its extensive ring system."},
    "uranus": {"type": "planet", "name": "Uranus", "distance_from_sun": "2.87 billion km", "radius": "25,362 km", "moons": 28, "description": "An ice giant rotating with an extreme axial tilt."},
    "neptune": {"type": "planet", "name": "Neptune", "distance_from_sun": "4.50 billion km", "radius": "24,622 km", "moons": 16, "description": "The farthest recognized planet from the Sun."},
    "pluto": {"type": "dwarf planet", "name": "Pluto", "distance_from_sun": "5.91 billion km average", "radius": "1,188.3 km", "moons": 5, "description": "A dwarf planet in the Kuiper Belt."},
    "moon": {"type": "natural satellite", "name": "Moon", "distance_from_earth": "384,400 km average", "radius": "1,737.4 km", "description": "Earth's natural satellite."},
}
ALIASES = {"terra": "earth", "sol": "sun", "luna": "moon", "the moon": "moon"}


class SpaceLookup:
    def __init__(self) -> None:
        self.api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")

    async def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=12.0, headers={"User-Agent": "Galaxy/0.2"}) as client:
            response = await client.get(url, params=params or {})
            response.raise_for_status()
            return response.json()

    async def solar_system(self, query: str) -> dict[str, Any] | None:
        item = SOLAR_SYSTEM.get(ALIASES.get(query.casefold(), query.casefold()))
        return {**item, "source": "Galaxy Solar System catalog"} if item else None

    async def wikipedia(self, query: str) -> dict[str, Any] | None:
        try:
            data = await self._get(f"{WIKI_API}/{query.replace(' ', '_')}")
        except (httpx.HTTPError, ValueError):
            return None
        if data.get("type", "").endswith("/not_found"):
            return None
        return {
            "title": data.get("title"), "description": data.get("description"),
            "extract": data.get("extract"), "thumbnail": (data.get("thumbnail") or {}).get("source"),
            "url": (data.get("content_urls") or {}).get("desktop", {}).get("page"),
            "source": "Wikipedia REST API",
        }

    async def jpl_small_body(self, query: str) -> dict[str, Any] | None:
        try:
            data = await self._get(JPL_SBDB, {"sstr": query})
        except (httpx.HTTPError, ValueError):
            return None
        if not data.get("object"):
            return None
        obj, orbit = data["object"], data.get("orbit") or {}
        return {
            "name": obj.get("fullname") or obj.get("des") or query,
            "designation": obj.get("des"), "kind": obj.get("kind"),
            "orbit_id": orbit.get("orbit_id"), "eccentricity": orbit.get("e"),
            "inclination": orbit.get("i"), "period_days": orbit.get("period"),
            "source": "JPL Small-Body Database",
        }

    async def apod(self, query: str) -> dict[str, Any] | None:
        try:
            data = await self._get(f"{NASA_BASE}/planetary/apod", {"api_key": self.api_key, "count": 20})
        except (httpx.HTTPError, ValueError):
            return None
        for item in (data if isinstance(data, list) else [data]):
            text = " ".join(str(item.get(k, "")) for k in ("title", "explanation"))
            if query.casefold() in text.casefold():
                return {k: item.get(k) for k in ("title", "date", "media_type", "url", "hdurl", "explanation")}
        return None

    async def search(self, query: str) -> dict[str, Any]:
        clean = " ".join(query.strip().split())
        if not clean:
            return {"query": query, "matches": [], "message": "Enter a space object name."}

        solar, jpl, wiki, apod = await asyncio.gather(
            self.solar_system(clean), self.jpl_small_body(clean),
            self.wikipedia(clean), self.apod(clean),
        )
        matches: list[dict[str, Any]] = []
        if solar:
            matches.append({"type": solar["type"], "name": solar["name"], "details": solar})
        if jpl and not solar:
            matches.append({"type": "small body", "name": jpl["name"], "details": jpl})
        if wiki:
            matches.append({"type": "reference", "name": wiki.get("title") or clean, "details": wiki})
        if apod:
            matches.append({"type": "astronomy picture", "name": apod.get("title"), "details": apod})
        return {
            "query": clean, "matches": matches,
            "sources": ["NASA APOD", "JPL Small-Body Database", "Wikipedia REST API", "Galaxy Solar System catalog"],
            "message": None if matches else "No match found in the current public sources.",
        }

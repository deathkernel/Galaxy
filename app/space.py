import asyncio
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

NASA_BASE = "https://api.nasa.gov"
NASA_IMAGES = "https://images-api.nasa.gov/search"
JPL_SBDB = "https://ssd-api.jpl.nasa.gov/sbdb.api"
WIKI_API = "https://en.wikipedia.org/w/api.php"
EXO_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

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

    async def _get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": "Galaxy/0.3"}) as client:
            response = await client.get(url, params=params or {})
            response.raise_for_status()
            return response.json()

    async def solar_system(self, query: str) -> dict[str, Any] | None:
        item = SOLAR_SYSTEM.get(ALIASES.get(query.casefold(), query.casefold()))
        return {**item, "source": "Galaxy Solar System catalog"} if item else None

    async def wikipedia(self, query: str) -> dict[str, Any] | None:
        try:
            data = await self._get(WIKI_API, {"action": "query", "list": "search", "srsearch": query, "srlimit": 5, "format": "json", "origin": "*"})
        except (httpx.HTTPError, ValueError):
            return None
        hits = (data.get("query") or {}).get("search") or []
        if not hits:
            return None
        hit = hits[0]
        try:
            summary = await self._get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{hit['title'].replace(' ', '_')}")
        except (httpx.HTTPError, ValueError, KeyError):
            summary = {}
        return {
            "title": hit.get("title"),
            "description": summary.get("description") or hit.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
            "extract": summary.get("extract"),
            "thumbnail": (summary.get("thumbnail") or {}).get("source"),
            "url": (summary.get("content_urls") or {}).get("desktop", {}).get("page"),
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

    async def nasa_images(self, query: str) -> dict[str, Any] | None:
        try:
            data = await self._get(NASA_IMAGES, {"q": query, "media_type": "image", "page_size": 8})
        except (httpx.HTTPError, ValueError):
            return None
        items = (data.get("collection") or {}).get("items") or []
        images = []
        for item in items[:6]:
            links = item.get("links") or []
            thumb = next((x.get("href") for x in links if x.get("rel") == "preview"), None)
            fields = item.get("data", [{}])[0]
            if thumb:
                images.append({"title": fields.get("title"), "date": fields.get("date_created"), "thumbnail": thumb, "nasa_id": fields.get("nasa_id")})
        return {"query": query, "images": images, "source": "NASA Image and Video Library"} if images else None

    async def exoplanet(self, query: str) -> dict[str, Any] | None:
        escaped = query.replace("'", "''")
        adql = "SELECT TOP 1 pl_name,hostname,pl_rade,pl_bmasse,pl_orbper,pl_orbsmax,sy_dist,discoverymethod FROM pscomppars WHERE lower(pl_name)=lower('" + escaped + "')"
        try:
            data = await self._get(EXO_TAP, {"query": adql, "format": "json"})
        except (httpx.HTTPError, ValueError):
            return None
        rows = data.get("data") or []
        if not rows:
            return None
        cols = data.get("metadata") or []
        names = [c.get("name") for c in cols]
        row = dict(zip(names, rows[0]))
        return {"name": row.get("pl_name"), "host_star": row.get("hostname"), "radius_earth": row.get("pl_rade"), "mass_earth": row.get("pl_bmasse"), "orbital_period_days": row.get("pl_orbper"), "semi_major_axis_au": row.get("pl_orbsmax"), "distance_pc": row.get("sy_dist"), "discovery_method": row.get("discoverymethod"), "source": "NASA Exoplanet Archive"}

    async def search(self, query: str) -> dict[str, Any]:
        clean = " ".join(query.strip().split())
        if not clean:
            return {"query": query, "matches": [], "message": "Enter anything space-related to search."}

        solar, jpl, wiki, apod, images, exoplanet = await asyncio.gather(
            self.solar_system(clean), self.jpl_small_body(clean), self.wikipedia(clean),
            self.apod(clean), self.nasa_images(clean), self.exoplanet(clean),
        )
        matches: list[dict[str, Any]] = []
        if solar:
            matches.append({"type": solar["type"], "name": solar["name"], "details": solar})
        if exoplanet and not solar:
            matches.append({"type": "exoplanet", "name": exoplanet["name"], "details": exoplanet})
        if jpl and not solar:
            matches.append({"type": "small body", "name": jpl["name"], "details": jpl})
        if wiki:
            matches.append({"type": "space reference", "name": wiki.get("title") or clean, "details": wiki})
        if apod:
            matches.append({"type": "astronomy picture", "name": apod.get("title"), "details": apod})
        if images:
            matches.append({"type": "NASA image results", "name": f"NASA images for {clean}", "details": images})
        return {"query": clean, "matches": matches, "sources": ["NASA APIs", "NASA Image and Video Library", "NASA Exoplanet Archive", "JPL Small-Body Database", "Wikipedia REST API"], "message": None if matches else "No match found in the current public sources."}

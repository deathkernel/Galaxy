from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.space import DWARF_PLANET_QUERIES, DWARF_PLANETS, SpaceLookup

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Galaxy", version="0.6.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

lookup = SpaceLookup()


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Galaxy search failed on the server.",
            "error_type": type(exc).__name__,
            "error": str(exc),
        },
    )


@app.get("/")
async def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "galaxy", "version": "0.6.0"}


@app.get("/api/search")
async def search(q: str = Query(min_length=2, max_length=120)):
    clean = " ".join(q.strip().split())
    if clean.casefold() in DWARF_PLANET_QUERIES:
        matches = [
            {"type": item["type"], "name": item["name"], "details": item}
            for item in DWARF_PLANETS.values()
        ]
        return {
            "query": clean,
            "matches": matches,
            "sources": ["NASA Dwarf Planets"],
            "message": None,
        }

    try:
        result = await lookup.search(clean)
        return JSONResponse(content=result)
    except Exception as exc:
        return JSONResponse(
            status_code=502,
            content={
                "query": clean,
                "matches": [],
                "message": "Galaxy could not complete this search right now.",
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )

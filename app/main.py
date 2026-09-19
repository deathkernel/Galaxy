from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.space import SpaceLookup

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Galaxy", version="0.5.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

lookup = SpaceLookup()


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Galaxy search failed on the server. Please try again.",
            "error_type": type(exc).__name__,
            "error": str(exc),
        },
    )


@app.get("/")
async def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "galaxy"}


@app.get("/api/search")
async def search(q: str = Query(min_length=2, max_length=120)):
    clean = " ".join(q.strip().split())
    try:
        return JSONResponse(content=await lookup.search(clean))
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

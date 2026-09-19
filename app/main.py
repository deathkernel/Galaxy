from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.space import SpaceLookup

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Galaxy", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

lookup = SpaceLookup()


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Galaxy search failed on the server. Please try again."},
    )


@app.get("/")
async def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "galaxy"}


@app.get("/api/search")
async def search(q: str = Query(min_length=2, max_length=120)):
    return await lookup.search(q)

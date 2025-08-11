import json

from fastapi import APIRouter, Query, Depends
from starlette.concurrency import run_in_threadpool
from app.services.scraper import scrape_amazon
from app.services.purify import normalize_children_text
from app.core.config import RAW_FILE, DATA_FILE
from app.core.auth import require_jwt

router = APIRouter(
    prefix="/scrape",
    tags=["scrape"],
    dependencies=[Depends(require_jwt)]   # 👈 protege todo el router
)

@router.post("")
async def scrape_and_purify(url: str = Query(..., description="URL de búsqueda de Amazon")):
    raw_data = await run_in_threadpool(scrape_amazon, url)
    RAW_FILE.write_text(json.dumps(raw_data, indent=2, ensure_ascii=False), encoding="utf-8")

    structured = []
    for idx, prod in enumerate(raw_data, start=1):
        if isinstance(prod, dict) and "children_text" in prod:
            clean = normalize_children_text(prod["children_text"])
            if clean:
                clean["id"] = idx
                structured.append(clean)

    DATA_FILE.write_text(json.dumps(structured, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "status": "success",
        "url": url,
        "saved_raw": str(RAW_FILE.resolve()),
        "saved_structured": str(DATA_FILE.resolve()),
        "raw_items": len(raw_data),
        "structured_items": len(structured)
    }

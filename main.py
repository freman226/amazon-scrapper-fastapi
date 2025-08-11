import json
from fastapi import FastAPI, Query
from scraper import scrape_amazon
from starlette.concurrency import run_in_threadpool
from pathlib import Path
import sys, asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="Amazon Scraper Service")

OUTPUT_FILE = Path("scrapped_info.json")

@app.get("/scrape")
async def scrape_endpoint(url: str = Query(..., description="URL de búsqueda de Amazon")):
    raw_data = await run_in_threadpool(scrape_amazon, url)
    OUTPUT_FILE.write_text(json.dumps(raw_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "status": "success",
        "url": url,
        "saved_file": str(OUTPUT_FILE.resolve()),
        "total_items": len(raw_data)
    }

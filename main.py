import sys
import asyncio
import json
import re
from pathlib import Path
from fastapi import FastAPI, Query
from starlette.concurrency import run_in_threadpool
from scraper import scrape_amazon  # síncrono
from datetime import datetime, timezone


# ✅ Recomendado en Windows para evitar problemas con subprocess (Playwright)
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="Amazon Scraper Service")

SERVICE_NAME = "amazon-scraper"
VERSION = "1.0.0"
STARTED_AT = datetime.now(timezone.utc)

@app.get("/health")
def health():
    """Liveness: el proceso está arriba."""
    now = datetime.now(timezone.utc)
    uptime = (now - STARTED_AT).total_seconds()
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": VERSION,
        "uptime_seconds": int(uptime),
    }

RAW_FILE = Path("scrapped_info.json")
DATA_FILE = Path("data.json")

# =========================
#   Heurísticas de purify
# =========================
PRICE_REGEX   = re.compile(r"\$\d{1,4}(?:,\d{3})*(?:\.\d{2})?")
RATING_REGEX  = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:out of 5 stars|de 5 estrellas)", re.IGNORECASE)
REVIEWS_REGEX = re.compile(r"^\s*[\d\u00A0,\.]+\+?\s*$")  # admite NBSP y , .
DELIVERY_REGEX= re.compile(
    r"(FREE delivery.*|delivery .*|Envío GRATIS.*|Entrega GRATIS.*|Entrega .*|Llega .*|Recíbelo .*)",
    re.IGNORECASE
)

BADGE_KEYWORDS = [
    # EN
    "Add to cart", "See options", "More Buying Choices", "Only", "List:", "Exclusively for Prime Members",
    # ES (añade variaciones comunes)
    "Agregar al carrito", "Añadir a la cesta", "Ver opciones", "Más opciones de compra", "Solo quedan",
    "Exclusivo para miembros Prime"
]

def _join_lines(lines):
    return [l.strip() for l in lines if l and l.strip()]

def _find_rating(lines):
    for line in lines:
        m = RATING_REGEX.search(line)
        if m:
            # normaliza coma decimal -> punto
            num = m.group(1).replace(',', '.')
            try:
                return float(num)
            except:
                return num
    return None

def _find_reviews(lines):
    # normalmente la línea siguiente al rating es el número de reseñas
    for i, line in enumerate(lines):
        if RATING_REGEX.search(line) and i + 1 < len(lines):
            nxt = lines[i+1].strip().replace('\u00A0', '')  # quita NBSP
            if REVIEWS_REGEX.match(nxt):
                return nxt.replace(' ', '')
    # fallback: primera línea que parezca conteo
    for line in lines:
        candidate = line.strip().replace('\u00A0', '')
        if REVIEWS_REGEX.match(candidate):
            return candidate.replace(' ', '')
    return None

def _reconstruct_split_price(lines, idx):
    try:
        p1 = lines[idx].strip()
        p2 = lines[idx + 1].strip()
        p3 = lines[idx + 2].strip()
        if p1.startswith("$") and p2 == "." and p3.isdigit() and len(p3) == 2:
            return f"{p1.replace(' ', '')}.{p3}"
    except IndexError:
        pass
    return None

def _find_price(lines):
    for line in lines:
        m = PRICE_REGEX.search(line.replace(" ", ""))
        if m:
            return m.group(0)
    for idx, line in enumerate(lines):
        if line.strip().startswith("$"):
            rec = _reconstruct_split_price(lines, idx)
            if rec:
                return rec
    for line in lines:
        if "List:" in line:
            m = PRICE_REGEX.search(line)
            if m:
                return m.group(0)
    return None

def _find_delivery(lines):
    for line in lines:
        m = DELIVERY_REGEX.search(line)
        if m:
            return m.group(0).strip()
    return None

def _find_badges(lines):
    badges = []
    for line in lines:
        for kw in BADGE_KEYWORDS:
            if kw.lower() in line.lower():
                if kw.lower().startswith("list"):
                    badges.append(line.strip())
                else:
                    badges.append(kw)
    seen, out = set(), []
    for b in badges:
        if b not in seen:
            seen.add(b); out.append(b)
    return out

def _find_title(lines):
    rating_idx = None
    price_idx = None
    for i, line in enumerate(lines):
        if rating_idx is None and RATING_REGEX.search(line):
            rating_idx = i
        if price_idx is None and PRICE_REGEX.search(line.replace(" ", "")):
            price_idx = i

    cut_idx = None
    if rating_idx is not None and price_idx is not None:
        cut_idx = min(rating_idx, price_idx)
    elif rating_idx is not None:
        cut_idx = rating_idx
    elif price_idx is not None:
        cut_idx = price_idx

    if cut_idx is None:
        return lines[0].strip() if lines else None

    title_lines = lines[:cut_idx]
    title_lines = [l for l in title_lines if not l.lower().startswith("price, product page")]
    import re as _re
    title = " ".join(title_lines).strip()
    title = _re.sub(r"\s{2,}", " ", title)
    return title if title else (lines[0].strip() if lines else None)

def normalize_children_text(children_text_obj: dict):
    if not isinstance(children_text_obj, dict):
        return None
    text = "\n".join([v for v in children_text_obj.values() if isinstance(v, str)])
    lines = _join_lines(text.splitlines())
    return {
        "title":   _find_title(lines),
        "rating":  _find_rating(lines),
        "reviews": _find_reviews(lines),
        "price":   _find_price(lines),
        "delivery":_find_delivery(lines),
        "badges":  _find_badges(lines),
    }

# =========================
#         Endpoints
# =========================
@app.get("/scrape")
async def scrape_and_purify(url: str = Query(..., description="URL de búsqueda de Amazon")):
    """
    1) Scrapea y guarda scrapped_info.json
    2) Purifica (children_text -> campos útiles) y guarda data.json
    """
    # 1) scraping (sin bloquear el loop)
    raw_data = await run_in_threadpool(scrape_amazon, url)

    # guardar bruto
    RAW_FILE.write_text(json.dumps(raw_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2) purificar
    structured = []
    for idx, prod in enumerate(raw_data, start=1):
        if isinstance(prod, dict) and "children_text" in prod:
            clean = normalize_children_text(prod["children_text"])
            if clean:
                clean["id"] = idx
                structured.append(clean)

    # guardar limpio
    DATA_FILE.write_text(json.dumps(structured, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "status": "success",
        "url": url,
        "saved_raw": str(RAW_FILE.resolve()),
        "saved_structured": str(DATA_FILE.resolve()),
        "raw_items": len(raw_data),
        "structured_items": len(structured)
    }

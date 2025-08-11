# app/services/purify.py
import re
from typing import Any

PRICE_REGEX   = re.compile(r"\$\d{1,4}(?:,\d{3})*(?:\.\d{2})?")
RATING_REGEX  = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:out of 5 stars|de 5 estrellas)", re.IGNORECASE)
REVIEWS_REGEX = re.compile(r"^\s*[\d\u00A0,\.]+\+?\s*$")
DELIVERY_REGEX= re.compile(
    r"(FREE delivery.*|delivery .*|Envío GRATIS.*|Entrega GRATIS.*|Entrega .*|Llega .*|Recíbelo .*)",
    re.IGNORECASE
)
BADGE_KEYWORDS = [
    "Add to cart", "See options", "More Buying Choices", "Only", "List:", "Exclusively for Prime Members",
    "Agregar al carrito", "Añadir a la cesta", "Ver opciones", "Más opciones de compra", "Solo quedan",
    "Exclusivo para miembros Prime"
]

def _join_lines(lines: list[str]) -> list[str]:
    return [l.strip() for l in lines if l and l.strip()]

def _find_rating(lines: list[str]):
    for line in lines:
        m = RATING_REGEX.search(line)
        if m:
            num = m.group(1).replace(',', '.')
            try: return float(num)
            except: return num
    return None

def _find_reviews(lines: list[str]):
    for i, line in enumerate(lines):
        if RATING_REGEX.search(line) and i + 1 < len(lines):
            nxt = lines[i+1].strip().replace('\u00A0', '')
            if REVIEWS_REGEX.match(nxt):
                return nxt.replace(' ', '')
    for line in lines:
        candidate = line.strip().replace('\u00A0', '')
        if REVIEWS_REGEX.match(candidate):
            return candidate.replace(' ', '')
    return None

def _reconstruct_split_price(lines: list[str], idx: int) -> str | None:
    try:
        p1, p2, p3 = lines[idx].strip(), lines[idx+1].strip(), lines[idx+2].strip()
        if p1.startswith("$") and p2 == "." and p3.isdigit() and len(p3) == 2:
            return f"{p1.replace(' ', '')}.{p3}"
    except IndexError:
        pass
    return None

def _find_price(lines: list[str]) -> str | None:
    for line in lines:
        m = PRICE_REGEX.search(line.replace(" ", ""))
        if m:
            return m.group(0)
    for idx, line in enumerate(lines):
        if line.strip().startswith("$"):
            rec = _reconstruct_split_price(lines, idx)
            if rec: return rec
    for line in lines:
        if "List:" in line:
            m = PRICE_REGEX.search(line)
            if m: return m.group(0)
    return None

def _find_delivery(lines: list[str]) -> str | None:
    for line in lines:
        m = DELIVERY_REGEX.search(line)
        if m: return m.group(0).strip()
    return None

def _find_badges(lines: list[str]) -> list[str]:
    badges: list[str] = []
    for line in lines:
        for kw in BADGE_KEYWORDS:
            if kw.lower() in line.lower():
                badges.append(line.strip() if kw.lower().startswith("list") else kw)
    # dedup preservando orden
    seen, out = set(), []
    for b in badges:
        if b not in seen:
            seen.add(b); out.append(b)
    return out

def _find_title(lines: list[str]) -> str | None:
    rating_idx = price_idx = None
    for i, line in enumerate(lines):
        if rating_idx is None and RATING_REGEX.search(line): rating_idx = i
        if price_idx  is None and PRICE_REGEX.search(line.replace(" ", "")): price_idx = i
    cut_idx = None
    if rating_idx is not None and price_idx is not None: cut_idx = min(rating_idx, price_idx)
    elif rating_idx is not None: cut_idx = rating_idx
    elif price_idx  is not None: cut_idx = price_idx
    if cut_idx is None:
        return lines[0].strip() if lines else None
    title_lines = [l for l in lines[:cut_idx] if not l.lower().startswith("price, product page")]
    import re as _re
    title = _re.sub(r"\s{2,}", " ", " ".join(title_lines).strip())
    return title or (lines[0].strip() if lines else None)

def normalize_children_text(children_text_obj: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(children_text_obj, dict): return None
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

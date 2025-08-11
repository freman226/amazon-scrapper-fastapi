# app/api/routers/ask.py
import json
from fastapi import APIRouter
from app.schemas.ask import AskBody
from app.services.gemini import ask_gemini
from app.core.config import DATA_FILE

router = APIRouter(prefix="/ask", tags=["ask"])

@router.post("")
def ask(body: AskBody):
    if not DATA_FILE.exists():
        return {"status": "error", "message": "data.json no existe. Ejecuta primero /scrape."}
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    ans = ask_gemini(data, body.question)
    return {"status": "success", "answer": ans}

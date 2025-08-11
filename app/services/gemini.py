# app/services/gemini.py
import json
import google.generativeai as genai
from app.core.config import GOOGLE_API_KEY, GEMINI_MODEL

if not GOOGLE_API_KEY:
    raise RuntimeError("Falta GOOGLE_API_KEY en .env")

genai.configure(api_key=GOOGLE_API_KEY)

def ask_gemini(data: list[dict], question: str) -> str:
    prompt = f"""
Tengo una lista de productos en JSON (campos: title, rating, reviews, price, delivery, badges, id).
Responde de forma clara y en español. Si algo no está en los datos, dilo.

Datos:
{json.dumps(data, ensure_ascii=False, indent=2)}

Pregunta del usuario:
{question}
"""
    model = genai.GenerativeModel(GEMINI_MODEL)
    resp = model.generate_content(prompt)
    return resp.text

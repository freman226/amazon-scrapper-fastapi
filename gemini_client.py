import os
import google.generativeai as genai

def ask_gemini(products, question):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    productos_texto = "\n\n".join([f"Producto {p['id']}: {p['text']}" for p in products])
    prompt = f"""
Tengo la siguiente lista de productos extraída de Amazon:
{productos_texto}

Pregunta del usuario: {question}
Responde de forma clara y concisa.
"""
    response = model.generate_content(prompt)
    return response.text

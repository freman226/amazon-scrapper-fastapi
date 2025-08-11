import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

# 1. Cargar variables desde .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("No se encontró GOOGLE_API_KEY en el .env")

# 2. Configurar Gemini
genai.configure(api_key=api_key)

# 3. Cargar archivo data.json
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 4. Pedir pregunta al usuario
prompt_usuario = input("Pregunta sobre los datos: ")

# 5. Crear prompt para Gemini
prompt = f"""
Tengo un archivo JSON con información de productos de Amazon.
Aquí está el contenido:

{json.dumps(data, ensure_ascii=False, indent=2)}

Por favor, responde a la siguiente pregunta sobre estos datos:
{prompt_usuario}
"""

# 6. Enviar a Gemini
model = genai.GenerativeModel("gemini-2.5-flash-lite")
response = model.generate_content(prompt)

print("\n--- Respuesta de Gemini ---\n")
print(response.text)

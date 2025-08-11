Amazon Scraper Service (FastAPI + Playwright + Gemini + JWT)

Microservicio para scrapear listados de Amazon, purificar la información y hacer consultas con Gemini sobre los datos resultantes. Arquitectura modular lista para crecer con base de datos y autenticación JWT (HS256).

------------------------------------------------------------
# Características
------------------------------------------------------------
- Autenticación JWT simétrica (HS256): emisión de tokens y validación de firma/expiración.
- /scrape (protegido): Playwright → extrae tarjetas, guarda
  - data/scrapped_info.json (bruto)
  - data/data.json (estructurado: title, rating, reviews, price, delivery, badges, id)
- /ask (protegido): consulta Gemini sobre data/data.json.
- /healthz (público) y /readiness (público u opcionalmente protegido): salud y preparación.
- Windows-friendly: WindowsProactorEventLoopPolicy y arranque sin reload para evitar errores con Playwright.

# Arquitectura

```
amazon_service/
|
|- app/
|  |- main.py
|  |- core/
|  |  |- config.py
|  |  |- security.py        # creación/validación JWT (HS256)
|  |  |- auth.py            # dependencia FastAPI: require_jwt
|  |- api/
|  |  |- routers/
|  |     |- auth.py         # /auth/token (emite JWT)
|  |     |- health.py       # /healthz, /readiness
|  |     |- scrape.py       # /scrape (protegido)
|  |     |- ask.py          # /ask (protegido)
|  |- services/
|  |  |- scraper.py         # Playwright (sync) → resultados brutos
|  |  |- purify.py          # Heurísticas para estructurar data
|  |  |- gemini.py          # Cliente Gemini
|  |- schemas/
|     |- ask.py
|
|- data/                    # salidas .json (se crea automáticamente)
|- start.py                 # arranque estable para Windows (sin reload)
|- requirements.txt
|- .env                     # claves y configuración
|- .gitignore
```

Asegúrate de que cada carpeta dentro de app/ tenga su __init__.py.

------------------------------------------------------------
# Requisitos
------------------------------------------------------------
- Python 3.10+
- Playwright
- FastAPI / Uvicorn
- Google Generative AI SDK (para /ask)
- python-jose[cryptography] (JWT)

------------------------------------------------------------
Configuración (.env)
------------------------------------------------------------
Ejemplo de .env mínimamente necesario:

# Gemini
GOOGLE_API_KEY=tu_api_key
GEMINI_MODEL=gemini-2.5-flash-lite

# JWT (firma simétrica)
JWT_SECRET=una_llave_muy_larga_y_aleatoria
JWT_EXPIRES_MINUTES=60

# Credenciales para emitir tokens
AUTH_CLIENT_ID=mi-cliente
AUTH_CLIENT_SECRET=mi-secreto-ultra

# DB (futuro)
# DATABASE_URL=postgresql+psycopg://user:pass@host:5432/dbname

------------------------------------------------------------
Instalación y arranque
------------------------------------------------------------
1) Instalar dependencias
   pip install -r requirements.txt

2) Instalar navegadores para Playwright
   playwright install

3) Arrancar el servidor (Windows-friendly, sin reload)
   python start.py

Servirá en: http://127.0.0.1:8000
Docs:      http://127.0.0.1:8000/docs

En Windows evitamos el --reload para no romper Playwright con procesos hijos y forzamos ProactorEventLoopPolicy en start.py.

------------------------------------------------------------
Autenticación (JWT HS256)
------------------------------------------------------------
1) Obtener token
   Endpoint: POST /auth/token
   Body (JSON):
     { "client_id": "mi-cliente", "client_secret": "mi-secreto-ultra" }
   Respuesta:
     {
       "access_token": "eyJhbGciOiJIUzI1NiIs...",
       "token_type": "bearer",
       "expires_in": 3600
     }

2) Usar token (Authorization: Bearer)
   curl "http://127.0.0.1:8000/scrape?url=https://www.amazon.com/s?k=gpus"      -H "Authorization: Bearer TU_JWT_AQUI"

En /docs, pulsa Authorize y pega: Bearer TU_JWT_AQUI

------------------------------------------------------------
Endpoints
------------------------------------------------------------
Health
- GET /healthz       -> confirma que el proceso está vivo.
- GET /readiness     -> checks rápidos (import de Playwright, CLI disponible, escritura en FS).

Auth
- POST /auth/token   -> emite JWT (HS256) con expiración.

Scraping + Purify (protegido)
- GET /scrape?url=<URL de búsqueda de Amazon>

Ejemplo:
GET /scrape?url=https://www.amazon.com/s?k=gpus

Respuesta:
{
  "status": "success",
  "url": "...",
  "saved_raw": "D:/.../data/scrapped_info.json",
  "saved_structured": "D:/.../data/data.json",
  "raw_items": 15,
  "structured_items": 15
}

Consultas con IA (protegido)
- POST /ask
Body:
{ "question": "¿Cuál es la tarjeta gráfica más barata y su precio?" }

Respuesta:
{ "status": "success", "answer": "La más barata es ... por $XXX.XX ..." }

Requiere data/data.json (ejecuta /scrape primero) y GOOGLE_API_KEY en .env.

------------------------------------------------------------
¿Qué datos se extraen?
------------------------------------------------------------
De cada tarjeta, las heurísticas de purify.py intentan construir:
- title    : título “limpio” (corta antes de rating o precio, filtra “Price, product page”)
- rating   : número decimal (ES/EN: “de 5 estrellas” / “out of 5 stars”)
- reviews  : recuento (tolerante a NBSP y comas)
- price    : detecta $123.45 y reconstruye precios partidos en líneas ($199 . 99)
- delivery : “FREE delivery…”, “Envío GRATIS…”, “Llega…”, “Recíbelo…”
- badges   : “Add to cart”, “See options”, “More Buying Choices”, “List: $…”, etc.

Amazon cambia por región/idioma; las heurísticas son extensibles.

------------------------------------------------------------
.gitignore sugerido
------------------------------------------------------------
- venv/, __pycache__/, .pytest_cache/
- data/*.json (archivos generados)
- .vscode/, .idea/, *.log, Thumbs.db, .DS_Store

------------------------------------------------------------
Problemas comunes & Soluciones
------------------------------------------------------------
NotImplementedError (Windows, Playwright + asyncio)
- Usa python start.py (sin reload) que aplica WindowsProactorEventLoopPolicy.
- Evita uvicorn ... --reload directo en Windows.

ModuleNotFoundError: No module named 'app.services.scraper'
- Falta __init__.py en alguna subcarpeta de app/ o el archivo no está en app/services/scraper.py.
- Verifica imports o usa imports relativos dentro del paquete.

playwright: browsers not found
- Ejecuta: playwright install.

Datos vacíos / bloqueos de Amazon
- Ya usamos User-Agent de desktop. Puedes agregar cabeceras, sleeps aleatorios, proxies (respetando TOS).

------------------------------------------------------------
Roadmap
------------------------------------------------------------
- Persistencia en DB (PostgreSQL/MySQL/SQLite) con SQLAlchemy/Prisma.
- Tareas programadas para refrescar listados.
- Filtros determinísticos (marca, precio, rating) sin IA.
- Tests (pytest) e integración continua.
- Observabilidad: /metrics Prometheus + logs estructurados.
- Validación de scopes por endpoint (ej. scrape, ask).

------------------------------------------------------------
Notas legales
------------------------------------------------------------
Proyecto educativo. Revisa y respeta los Términos de Servicio del sitio a scrapear. Solo scrapea contenido con permiso.

------------------------------------------------------------
Contribuciones
------------------------------------------------------------
¡Bienvenidas! Issues/PR con mejoras, heurísticas o nuevos mercados.

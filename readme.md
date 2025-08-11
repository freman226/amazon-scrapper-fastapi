Amazon Scraper Service (FastAPI + Playwright + Gemini)

Microservicio para scrapear listados de Amazon, purificar la información y hacer consultas con Gemini sobre los datos resultantes. Diseñado para escalar (routers, servicios, config) y preparado para integrar base de datos a futuro.

------------------------------------------------------------
Características
------------------------------------------------------------
- /scrape: navega con Playwright (Chromium), extrae tarjetas de producto, guarda:
  - data/scrapped_info.json (bruto)
  - data/data.json (estructurado: title, rating, reviews, price, delivery, badges, id)
- /ask: consulta Gemini sobre data/data.json.
- /healthz y /readiness: endpoints de salud y readiness.
- Listo para Windows: usa ProactorEventLoop y arranque sin reload para evitar errores de asyncio + Playwright.

------------------------------------------------------------
Arquitectura
------------------------------------------------------------
amazon_service/
|
|- app/
|  |- main.py
|  |- core/
|  |  |- config.py
|  |- api/
|  |  |- routers/
|  |     |- health.py
|  |     |- scrape.py
|  |     |- ask.py
|  |- services/
|  |  |- scraper.py        # Playwright (sync) → resultados brutos
|  |  |- purify.py         # Heurísticas para estructurar data
|  |  |- gemini.py         # Cliente Gemini
|  |- schemas/
|     |- ask.py
|
|- data/                   # salidas .json (se crea automáticamente)
|- start.py                # arranque estable para Windows (sin reload)
|- requirements.txt
|- .env                    # GOOGLE_API_KEY=...
|- .gitignore

Asegúrate de que cada carpeta dentro de app/ tenga su __init__.py.

------------------------------------------------------------
Requisitos
------------------------------------------------------------
- Python 3.10+
- Playwright
- FastAPI / Uvicorn
- (Opcional) Clave de Gemini para /ask

------------------------------------------------------------
Instalación y arranque
------------------------------------------------------------
1) Instalar dependencias
   pip install -r requirements.txt

2) Instalar navegadores para Playwright
   playwright install

3) Configurar Gemini en .env (para /ask)
   echo GOOGLE_API_KEY=tu_api_key > .env
   (opcional) elegir modelo: GEMINI_MODEL=gemini-2.5-flash-lite

4) Arrancar el servidor (Windows-friendly)
   python start.py

Servirá en: http://127.0.0.1:8000
Docs:      http://127.0.0.1:8000/docs

En Windows arrancamos con start.py (sin reload) y forzamos WindowsProactorEventLoopPolicy para que Playwright pueda crear subprocesos sin lanzar el clásico NotImplementedError.

------------------------------------------------------------
Endpoints
------------------------------------------------------------
Health
- GET /healthz        -> confirma que el proceso está vivo.
- GET /readiness      -> checks rápidos (import de Playwright, CLI disponible, escritura en FS).

Scraping + Purify
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

Genera:
- data/scrapped_info.json (crudo)
- data/data.json (limpio con campos útiles)

Consultas con IA (Gemini)
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
- title    : título “limpio” (corta antes de rating o precio, quita textos basura como “Price, product page”)
- rating   : número decimal (funciona en EN y ES: “out of 5 stars” / “de 5 estrellas”)
- reviews  : recuento (tolerante a NBSP, comas)
- price    : detecta $123.45 y reconstruye precios partidos en líneas ($199 . 99)
- delivery : frases tipo “FREE delivery…”, “Envío GRATIS…”, “Llega…”
- badges   : “Add to cart”, “See options”, “More Buying Choices”, “List: $…”, etc.

Las páginas de Amazon varían por región/idioma. Las heurísticas están pensadas para ser robustas y fáciles de extender.

------------------------------------------------------------
Configuración
------------------------------------------------------------
.env
  GOOGLE_API_KEY=tu_api_key
  GEMINI_MODEL=gemini-2.5-flash-lite   # opcional (por defecto)
  # DATABASE_URL=postgresql+psycopg://...

app/core/config.py
  - Define rutas (DATA_DIR, RAW_FILE, DATA_FILE)
  - Modelos y claves de Gemini
  - DATABASE_URL (para futuro)

------------------------------------------------------------
.gitignore recomendado
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
- Falta __init__.py en alguna subcarpeta de app/.
- O el archivo no está en app/services/scraper.py.
- Verifica imports o usa imports relativos.

playwright: browsers not found
- Asegúrate de correr: playwright install.

Datos vacíos / bloqueos de Amazon
- Ya usamos User-Agent de desktop. Puedes agregar cabeceras, retrasos aleatorios, proxies, y respetar TOS.

------------------------------------------------------------
Roadmap (sugerencias)
------------------------------------------------------------
- Persistencia en DB (PostgreSQL/MySQL/SQLite) vía SQLAlchemy o Prisma.
- Tareas programadas para refrescar listados.
- Filtros determinísticos (marca, precio, rating) sin IA.
- Tests (pytest) e integración continua.
- Observabilidad: /metrics Prometheus + logs estructurados.

------------------------------------------------------------
Notas legales
------------------------------------------------------------
Este proyecto es educativo. Revisa y respeta los Términos de Servicio de los sitios que scrapearás. Solo scrapea contenido donde tengas permiso.

------------------------------------------------------------
Contribuciones
------------------------------------------------------------
¡Bienvenidas! Abre un issue/PR con mejoras, heurísticas nuevas o soporte para más idiomas/mercados.

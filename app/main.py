# app/main.py
import sys, asyncio
from fastapi import FastAPI
from app.api.routers import health as health_router
from app.api.routers import scrape as scrape_router
from app.api.routers import ask as ask_router
from .api.routers import auth as auth_router

# Windows: ProactorEventLoop para Playwright
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="Amazon Scraper Service")

app.include_router(health_router.router)
app.include_router(scrape_router.router)
app.include_router(ask_router.router)
app.include_router(auth_router.router)

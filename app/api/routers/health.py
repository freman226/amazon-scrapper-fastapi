# app/api/routers/health.py
from fastapi import APIRouter
from datetime import datetime, timezone
from app.core.config import SERVICE_NAME, VERSION

router = APIRouter(tags=["health"])

STARTED_AT = datetime.now(timezone.utc)

@router.get("/healthz")
def healthz():
    now = datetime.now(timezone.utc)
    uptime = (now - STARTED_AT).total_seconds()
    return {"status": "ok", "service": SERVICE_NAME, "version": VERSION, "uptime_seconds": int(uptime)}

@router.get("/readiness")
def readiness():
    import shutil, importlib
    checks = {}
    try:
        importlib.import_module("playwright")
        checks["playwright_import"] = True
    except Exception as e:
        checks["playwright_import"] = f"error: {e}"
    checks["playwright_cli"] = bool(shutil.which("playwright"))

    # fs write
    try:
        from pathlib import Path
        p = Path(".writetest.tmp"); p.write_text("ok", encoding="utf-8"); p.unlink(missing_ok=True)
        checks["fs_write"] = True
    except Exception as e:
        checks["fs_write"] = f"error: {e}"

    ready = all(v is True for v in checks.values())
    return {"status": "ok" if ready else "degraded", "ready": ready, "checks": checks}

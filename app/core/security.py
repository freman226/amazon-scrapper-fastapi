# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from jose import jwt, JWTError
from app.core.config import JWT_SECRET, JWT_EXPIRES_MINUTES

ALGORITHM = "HS256"

def create_access_token(
    subject: str,
    scopes: Optional[List[str]] = None,
    expires_minutes: int = JWT_EXPIRES_MINUTES,
) -> str:
    if not JWT_SECRET:
        raise RuntimeError("Server misconfigured: JWT_SECRET not set")

    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)
    to_encode: Dict[str, Any] = {
        "sub": subject,
        "scopes": scopes or [],
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    if not JWT_SECRET:
        raise RuntimeError("Server misconfigured: JWT_SECRET not set")
    return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])

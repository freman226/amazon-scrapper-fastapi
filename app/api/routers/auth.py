# app/api/routers/auth.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.core.config import AUTH_CLIENT_ID, AUTH_CLIENT_SECRET, JWT_EXPIRES_MINUTES
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class TokenRequest(BaseModel):
    client_id: str
    client_secret: str

@router.post("/token")
def issue_token(body: TokenRequest):
    if body.client_id != AUTH_CLIENT_ID or body.client_secret != AUTH_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials")

    access_token = create_access_token(subject=body.client_id, scopes=["scrape", "ask"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRES_MINUTES * 60,
    }

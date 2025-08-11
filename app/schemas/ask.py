# app/schemas/ask.py
from pydantic import BaseModel

class AskBody(BaseModel):
    question: str

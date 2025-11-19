from typing import Optional
from pydantic import BaseModel

class SudokuImageResponseSchema(BaseModel):
    id: Optional[int]
    mime: str
    content_base64: str

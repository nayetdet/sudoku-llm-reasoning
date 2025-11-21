from typing import Optional
from pydantic import BaseModel

class SudokuImageSchema(BaseModel):
    id: Optional[int]
    mime: str
    content_base64: Optional[str]

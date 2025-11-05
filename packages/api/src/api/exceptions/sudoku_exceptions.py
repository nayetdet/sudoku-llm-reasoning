from typing import ClassVar
from starlette import status
from api.exceptions import BaseApplicationException

class SudokuNotFoundException(BaseApplicationException):
    STATUS_CODE: ClassVar[int] = status.HTTP_404_NOT_FOUND
    MESSAGE: ClassVar[str] = "The requested sudoku was not found."

from typing import ClassVar
from starlette import status
from api.exceptions import BaseApplicationException

class SudokuInferenceNotFoundException(BaseApplicationException):
    STATUS_CODE: ClassVar[int] = status.HTTP_404_NOT_FOUND
    MESSAGE: ClassVar[str] = "The requested sudoku inference was not found."

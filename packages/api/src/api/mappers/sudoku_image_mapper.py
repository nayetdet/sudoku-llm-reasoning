import base64
from api.schemas.responses.sudoku_image_response_schema import SudokuImageResponseSchema
from api.models.sudoku_image import SudokuImage as SudokuImageModel

class SudokuImageMapper:
    @classmethod
    def to_image(cls, content: bytes) -> SudokuImageModel:
        return SudokuImageModel(content=content)

    @classmethod
    def to_image_response_schema(cls, image: SudokuImageModel) -> SudokuImageResponseSchema:
        return SudokuImageResponseSchema(
            id=image.id,
            content_base64=base64.b64encode(image.content).decode("utf-8"),
            mime=image.mime
        )

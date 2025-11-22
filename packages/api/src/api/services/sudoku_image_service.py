import zipfile
from io import BytesIO
from api.mappers.sudoku_image_mapper import SudokuImageMapper
from api.schemas.queries.base_query_schema import PageSchema, PageableSchema
from api.schemas.queries.sudoku_image_query_schema import SudokuImageQuerySchema
from api.schemas.responses.sudoku_image_response_schema import SudokuImageResponseSchema
from starlette.responses import StreamingResponse
from api.exceptions.sudoku_image_exceptions import SudokuImageNotFoundException
from api.repositories.sudoku_image_repository import SudokuImageRepository
from api.repositories.sudoku_repository import SudokuRepository

class SudokuImageService:
    @classmethod
    def get_all(cls, query: SudokuImageQuerySchema) -> PageSchema[SudokuImageResponseSchema]:
        return PageSchema[SudokuImageResponseSchema](
            content=[
                SudokuImageMapper.to_image_response_schema(model)
                for model in SudokuImageRepository.get_all(
                    sudoku_id=query.sudoku_id,
                    page=query.page,
                    size=query.size
                )
            ],
            pageable=PageableSchema(
                page=query.page,
                size=query.size,
                total_elements=SudokuImageRepository.count(
                    sudoku_id=query.sudoku_id
                )
            )
        )

    @classmethod
    def download_zip(cls) -> StreamingResponse:
        buffer: BytesIO = BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as file:
            for sudoku in SudokuRepository.get_all(has_images=True):
                folder: str = f"{sudoku.n}x{sudoku.n}/{sudoku.candidate_type.simplified_display_name}/sudoku_{sudoku.id}"
                for image in sudoku.images:
                    ext: str = image.mime.split("/")[-1]
                    filename: str = f"{folder}/image_{image.id}.{ext}"
                    file.writestr(filename, image.content)

        buffer.seek(0)
        return StreamingResponse(
            content=buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=images.zip"
            }
        )

    @classmethod
    def delete_by_id(cls, image_id: int) -> None:
        if not SudokuImageRepository.delete_by_id(image_id):
            raise SudokuImageNotFoundException()

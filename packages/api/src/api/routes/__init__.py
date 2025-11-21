from fastapi import FastAPI, APIRouter
from api.routes import sudoku_route, sudoku_inference_route, sudoku_image_route

def register_routes(app: FastAPI) -> None:
    v1_router = APIRouter(prefix="/v1")
    v1_router.include_router(sudoku_route.router, prefix="/sudokus", tags=["Sudoku"])
    v1_router.include_router(sudoku_inference_route.router, prefix="/sudokus/inferences", tags=["Sudoku Inference"])
    v1_router.include_router(sudoku_image_route.router, prefix="/sudokus/images", tags=["Sudoku Image"])
    app.include_router(v1_router)

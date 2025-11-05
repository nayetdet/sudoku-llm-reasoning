from fastapi import FastAPI, APIRouter
from api.routes import sudoku_route

def register_routes(app: FastAPI) -> None:
    v1_router = APIRouter(prefix="/v1")
    v1_router.include_router(sudoku_route.router, prefix="/sudoku", tags=["Sudoku"])
    app.include_router(v1_router)

from fastapi import FastAPI
from api.exceptions import register_exception_handlers
from api.middlewares import register_middlewares
from api.routes import register_routes

app = FastAPI(title="Sudoku LLM Reasoning: API")

register_middlewares(app)
register_exception_handlers(app)
register_routes(app)

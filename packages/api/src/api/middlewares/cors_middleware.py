from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from api.config import Config

def register_cors_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=Config.API.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

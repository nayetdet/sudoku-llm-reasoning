from os import getenv


class Config:
    LLM_API_KEY: str = getenv("LLM_API_KEY")
    LLM_MODEL: str = getenv("LLM_MODEL")

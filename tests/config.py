from os import getenv

class Config:
    class LLM:
        MODEL: str = getenv("LLM_MODEL")
        API_KEY: str = getenv("LLM_API_KEY")

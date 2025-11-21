from os import getenv

class Config:
    class WebUI:
        API_URL: str = getenv("WEBUI_API_URL")

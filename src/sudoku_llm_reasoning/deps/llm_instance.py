import google.generativeai as genai
from typing import Optional
from google.generativeai import GenerativeModel
from src.sudoku_llm_reasoning.config import Config

class LLMInstance:
    __llm: Optional[GenerativeModel] = None

    @classmethod
    def get_llm(cls) -> GenerativeModel:
        if cls.__llm is None:
            genai.configure(api_key=Config.LLM_API_KEY)
            cls.__llm = GenerativeModel(model_name=Config.LLM_MODEL)
        return cls.__llm

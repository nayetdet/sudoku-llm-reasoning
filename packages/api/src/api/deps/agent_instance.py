from typing import Optional
from api.config import Config
from core.sudoku_inference_agent import SudokuInferenceAgent

class AgentInstance:
    __sudoku_inference_agent: Optional[SudokuInferenceAgent] = None

    @classmethod
    def get_sudoku_inference_agent(cls) -> SudokuInferenceAgent:
        if cls.__sudoku_inference_agent is None:
            cls.__sudoku_inference_agent = SudokuInferenceAgent(llm_model=Config.LLM.MODEL, llm_api_key=Config.LLM.API_KEY)
        return cls.__sudoku_inference_agent

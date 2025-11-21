import requests
from typing import List, Tuple, Dict, Any
from webui.config import Config
from webui.schemas.sudoku_schema import SudokuSchema

class SudokuService:
    @classmethod
    def get_all(cls, **filters) -> Tuple[int, List[SudokuSchema]]:
        results: List[SudokuSchema] = []
        response: requests.Response = requests.get(url=f"{Config.WebUI.API_URL}/v1/sudokus/", params=filters)
        response.raise_for_status()

        data: Dict[str, Any] = response.json()
        content: List[Dict[str, Any]] = data.get("content", [])
        if content:
            for element in content:
                results.append(SudokuSchema.model_validate(element))

        total_elements: int = int(data.get("pageable", {}).get("total_elements", 0))
        return total_elements, results

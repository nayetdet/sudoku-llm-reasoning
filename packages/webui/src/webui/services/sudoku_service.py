import requests
from typing import List, Tuple, Dict, Any
from webui.config import Config
from webui.schemas.sudoku_schema import SudokuSchema

class SudokuService:
    @classmethod
    def get_all(cls, **filters) -> Tuple[int, List[SudokuSchema]]:
        sudokus: List[SudokuSchema] = []
        response: requests.Response = requests.get(url=f"{Config.WebUI.API_URL}/v1/sudokus", params=filters)
        response.raise_for_status()

        data: Dict[str, Any] = response.json()
        content: List[Dict[str, Any]] = data.get("content", [])
        if content:
            for element in content:
                sudokus.append(SudokuSchema.model_validate(element))

        total_sudokus: int = int(data.get("pageable", {}).get("total_elements", 0))
        return total_sudokus, sudokus

    @classmethod
    def get_all_pages(cls, **filters) -> List[SudokuSchema]:
        page: int = 0
        all_sudokus: List[SudokuSchema] = []
        while True:
            total_sudokus, sudokus = cls.get_all(**filters, page=page, size=100)
            if not sudokus:
                break

            all_sudokus.extend(sudokus)
            if len(all_sudokus) >= total_sudokus:
                break
            page += 1
        return all_sudokus

import requests
from typing import List, Tuple, Dict, Any
from webui.config import Config
from webui.schemas.sudoku_image_schema import SudokuImageSchema

class SudokuImageService:
    @classmethod
    def get_all(cls, sudoku_id: int, **filters) -> Tuple[int, List[SudokuImageSchema]]:
        images: List[SudokuImageSchema] = []
        response: requests.Response = requests.get(url=f"{Config.WebUI.API_URL}/v1/sudokus/{sudoku_id}/images", params=filters)
        response.raise_for_status()

        data: Dict[str, Any] = response.json()
        content: List[Dict[str, Any]] = data.get("content", [])
        if content:
            for element in content:
                images.append(SudokuImageSchema.model_validate(element))

        total_images: int = int(data.get("pageable", {}).get("total_elements", 0))
        return total_images, images

    @classmethod
    def get_all_pages(cls, sudoku_id: int) -> List[SudokuImageSchema]:
        page: int = 0
        all_images: List[SudokuImageSchema] = []
        while True:
            total_images, images = cls.get_all(sudoku_id, page=page, size=25)
            if not images:
                break

            all_images.extend(images)
            if len(all_images) >= total_images:
                break
            page += 1
        return all_images

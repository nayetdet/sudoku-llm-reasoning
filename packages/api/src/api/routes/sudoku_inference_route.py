from typing import List
from fastapi import APIRouter, status
from api.schemas.requests.sudoku_inference_request_schema import SudokuInferenceRequestSchema
from api.schemas.responses.sudoku_inference_analytics_response_schema import SudokuInferenceAnalyticsResponseSchema
from api.services.sudoku_inference_service import SudokuInferenceService

router = APIRouter()

@router.get("/analytics", response_model=List[SudokuInferenceAnalyticsResponseSchema])
def get_analytics():
    return SudokuInferenceService.get_analytics()

@router.post("/", status_code=status.HTTP_204_NO_CONTENT)
def create(request: SudokuInferenceRequestSchema):
    SudokuInferenceService.create(request)

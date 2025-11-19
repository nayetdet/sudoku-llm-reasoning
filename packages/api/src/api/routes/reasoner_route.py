from fastapi import APIRouter

from api.schemas.responses.reasoner_accuracy_response_schema import ReasonerAccuracyResponseSchema
from api.services.reasoner_accuracy_service import ReasonerAccuracyService

router = APIRouter()


@router.get("/accuracy", response_model=list[ReasonerAccuracyResponseSchema])
def get_reasoner_accuracy() -> list[ReasonerAccuracyResponseSchema]:
    return ReasonerAccuracyService.list_results()

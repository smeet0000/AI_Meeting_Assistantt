from fastapi import APIRouter, HTTPException

from api.schemas.chat import ChatRequest
from api.schemas.responses import ChatResponse
from api.services.rag_session import get_chain
from core.rag_engine import ask_question
from api.exceptions import PipelineException

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post(
    "/",
    response_model=ChatResponse
)
def chat(request: ChatRequest):

    rag_chain = get_chain("default")

    if rag_chain is None:
        raise HTTPException(
            status_code=400,
            detail="No meeting has been analyzed yet."
        )

    try:

        answer = ask_question(
            rag_chain,
            request.question
        )

        return {
            "question": request.question,
            "answer": answer
        }

    except Exception as e:
        raise PipelineException(detail=str(e))

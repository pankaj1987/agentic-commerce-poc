import logging

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.chat_schemas import (
    ChatRequest,
    ChatResponse,
)
from app.services.chat_service import ChatService


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
):
    """
    Process a natural-language commerce request.

    The request is routed to the appropriate commerce agent.
    """

    logger.info(
        "Received /api/chat request. message=%s",
        request.message,
    )

    try:
        result = await ChatService.process_message(
            message=request.message,
            cart_id=request.cart_id,
        )

        logger.info(
            "Completed /api/chat request."
        )

        return result

    except Exception as exc:
        logger.exception(
            "Error while processing /api/chat request."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process chat request.",
        ) from exc
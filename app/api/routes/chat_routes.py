# app/api/routes/chat_routes.py

import logging

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.api.schemas.chat_schemas import (
    ChatRequest,
    ChatResponse,
)
from app.services.chat_service import (
    ChatService,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
) -> ChatResponse:
    """
    Process one commerce conversation turn.

    Browser supplies:
        message
        session_id

    Browser never supplies:
        Shopify cart_id
        LangGraph thread_id
    """

    try:
        result = await ChatService.process_message(
            message=request.message,
            session_id=request.session_id,
        )

        return ChatResponse(
            **result
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        logger.exception(
            "Chat request failed."
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(exc),
        ) from exc
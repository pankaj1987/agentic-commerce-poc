import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.chat_schemas import ChatRequest, ChatResponse
from app.security.auth import get_security_context
from app.security.context import SecurityContext
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    security_context: SecurityContext = Depends(get_security_context),
) -> ChatResponse:
    try:
        result = await ChatService.process_message(
            message=request.message,
            session_id=request.session_id,
            user_id=security_context.user_id,
            security_context=security_context,
        )
        return ChatResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Chat request failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process the commerce request.",
        ) from exc

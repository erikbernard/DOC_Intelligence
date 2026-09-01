from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.core.security import decode_token
from app.services.sse_service import sse_event_generator

router = APIRouter()


@router.get("/stream")
async def stream_realtime_events(
    persona_id: Optional[str] = Query(None),
    token: str = Query(...),
):
    """Stream real-time SSE events (document progress, reviews, completions)."""
    try:
        payload = decode_token(token)
        if not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de autenticação inválido ou expirado."
            )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Não autorizado: {str(exc)}"
        )

    return StreamingResponse(
        sse_event_generator(persona_id=persona_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

"""API v1 Router registry."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    collection_links,
    documents,
    personas,
    public_upload,
    sse,
    templates,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(personas.router, prefix="/personas", tags=["Personas"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(
    collection_links.router, prefix="/collection-links", tags=["Collection Links"]
)
api_router.include_router(
    public_upload.router, prefix="/public", tags=["Public Collection Upload"]
)
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(sse.router, prefix="/events", tags=["Real-time Events SSE"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

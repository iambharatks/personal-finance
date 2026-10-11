from fastapi import APIRouter, Depends, FastAPI, Request

from app.auth import require_session
from app.config import get_settings
from app.routers import auth, dashboard, reference, transactions

settings = get_settings()
settings.validate_for_startup()

# The API schema is only published locally; the client's types are generated from it.
app = FastAPI(
    title="Finance Command Center",
    docs_url=None if settings.is_production else "/api/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/api/openapi.json",
)


@app.middleware("http")
async def private_by_default(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


api = APIRouter(prefix="/api")
api.include_router(auth.router)

# Everything that touches data sits behind the session check.
protected = APIRouter(dependencies=[Depends(require_session)])
protected.include_router(reference.router)
protected.include_router(transactions.router)
protected.include_router(dashboard.router)
api.include_router(protected)


@api.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api)

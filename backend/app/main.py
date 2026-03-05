from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.assignments import router as assignments_router
from app.api.auth import router as auth_router
from app.api.clients import router as clients_router
from app.api.dashboard import router as dashboard_router
from app.api.exercises import router as exercises_router
from app.api.plans import router as plans_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(exercises_router)
app.include_router(clients_router)
app.include_router(plans_router)
app.include_router(assignments_router)
app.include_router(dashboard_router)


@app.get("/health")
def health():
    return {"status": "ok"}

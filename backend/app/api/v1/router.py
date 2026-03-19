from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.projects import router as projects_router
from app.api.v1.events import router as events_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.agents import router as agents_router
from app.api.v1.artifacts import router as artifacts_router
from app.api.v1.comments import router as comments_router
from app.api.v1.settings import router as settings_router
from app.api.v1.agent_api import router as agent_api_router
from app.api.v1.files import router as files_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(tasks_router)
api_router.include_router(projects_router)
api_router.include_router(events_router)
api_router.include_router(sessions_router)
api_router.include_router(agents_router)
api_router.include_router(artifacts_router)
api_router.include_router(comments_router)
api_router.include_router(settings_router)
api_router.include_router(agent_api_router)
api_router.include_router(files_router)

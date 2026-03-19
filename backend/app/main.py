import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_router
from app.ws.hub import ws_router
from app.core.event_bus import event_bus
from app.services.file_watcher import start_file_watcher, stop_file_watcher
from app.services.gateway_poller import start_gateway_poller, stop_gateway_poller
from app.storage.json_store import ensure_data_dirs
from app.storage.agent_repo import agent_repo


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ensure_data_dirs(settings.data_dir)
    await agent_repo.seed_if_empty()
    # Pass running loop explicitly so watchdog thread can schedule coroutines correctly
    loop = asyncio.get_running_loop()
    start_file_watcher(event_bus, settings.openclaw_workspace, openclaw_dir=settings.openclaw_dir, loop=loop)
    start_gateway_poller(event_bus, settings.openclaw_gateway_url, settings.openclaw_gateway_token)
    yield
    # Shutdown
    stop_file_watcher()
    stop_gateway_poller()


app = FastAPI(title="E.D.I.T.H. Ops", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

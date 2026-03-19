from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Auth
    jwt_secret: str = ""
    dashboard_password: str = ""
    ingest_api_key: str = ""

    # Notion
    notion_api_key: str = ""
    notion_tasks_db: str = ""
    notion_projects_db: str = ""

    # OpenClaw Gateway
    openclaw_gateway_url: str = "http://localhost:18789"
    openclaw_gateway_token: str = ""
    openclaw_workspace: str = "C:/Users/Doszhan/.openclaw/workspace"
    openclaw_dir: str = "C:/Users/Doszhan/.openclaw"

    # Server
    backend_port: int = 18790
    data_dir: str = "./data"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

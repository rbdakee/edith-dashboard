from pathlib import Path
from datetime import datetime, timezone

from app.domain.models import AppSettings
from app.storage.json_store import read_json, write_json
from app.config import settings


class ConfigRepository:
    def _settings_path(self) -> Path:
        return Path(settings.data_dir) / "config" / "settings.json"

    async def get_settings(self) -> AppSettings:
        raw = read_json(self._settings_path())
        if raw is None:
            return AppSettings()
        return AppSettings(**raw)

    async def update_settings(self, updates: dict) -> AppSettings:
        current = await self.get_settings()
        data = current.model_dump(mode="json")
        data.update(updates)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        write_json(self._settings_path(), data)
        return AppSettings(**data)


config_repo = ConfigRepository()

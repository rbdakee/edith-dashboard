import httpx
from app.config import settings


class NotionClient:
    BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"

    def __init__(self):
        self.token = settings.notion_api_key
        self.tasks_db = settings.notion_tasks_db
        self.projects_db = settings.notion_projects_db
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.API_VERSION,
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=30.0)

    async def query_database(self, database_id: str, body: dict | None = None) -> dict:
        resp = await self.client.post(
            f"{self.BASE_URL}/databases/{database_id}/query",
            headers=self.headers,
            json=body or {},
        )
        resp.raise_for_status()
        return resp.json()

    async def create_page(self, body: dict) -> dict:
        resp = await self.client.post(
            f"{self.BASE_URL}/pages",
            headers=self.headers,
            json=body,
        )
        resp.raise_for_status()
        return resp.json()

    async def update_page(self, page_id: str, body: dict) -> dict:
        resp = await self.client.patch(
            f"{self.BASE_URL}/pages/{page_id}",
            headers=self.headers,
            json=body,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_page(self, page_id: str) -> dict:
        resp = await self.client.get(
            f"{self.BASE_URL}/pages/{page_id}",
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()

    async def query_tasks(self, filters: dict | None = None) -> list[dict]:
        body = {}
        if filters:
            body["filter"] = filters
        result = await self.query_database(self.tasks_db, body)
        return result.get("results", [])

    async def query_projects(self, filters: dict | None = None) -> list[dict]:
        body = {}
        if filters:
            body["filter"] = filters
        result = await self.query_database(self.projects_db, body)
        return result.get("results", [])

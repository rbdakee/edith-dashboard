import httpx
from app.config import settings


class OpenClawGatewayClient:
    """HTTP client for the OpenClaw gateway at :18789."""

    def __init__(self):
        self.base_url = settings.openclaw_gateway_url
        self.token = settings.openclaw_gateway_token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def get_agents(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self.base_url}/api/agents", headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def get_sessions(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self.base_url}/api/sessions", headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def get_session(self, session_id: str) -> dict:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{self.base_url}/api/sessions/{session_id}", headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()

    async def send_message(self, session_id: str, content: str, role: str = "user") -> dict:
        """Inject a message into an active agent session."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/sessions/{session_id}/messages",
                headers=self.headers,
                json={"content": content, "role": role},
            )
            resp.raise_for_status()
            return resp.json()


gateway_client = OpenClawGatewayClient()

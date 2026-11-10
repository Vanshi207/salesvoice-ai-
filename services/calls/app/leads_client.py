import httpx

from salesvoice_common.auth_deps import CurrentUser

from app.config import settings


async def lead_visible(lead_id: str, user: CurrentUser) -> bool:
    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.get(f"{settings.leads_url}/leads/{lead_id}",
                             headers={"X-User-Id": user.id, "X-User-Role": user.role})
    if r.status_code == 404:
        return False
    r.raise_for_status()
    return True

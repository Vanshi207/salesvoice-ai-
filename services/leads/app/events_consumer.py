import logging

from app.db import db
from app.models import Lead

log = logging.getLogger("leads.events")


async def handle(event_type: str, data: dict) -> None:
    if event_type != "call.analyzed":
        return
    async with db.sessionmaker() as s:
        lead = await s.get(Lead, data["lead_id"])
        if not lead:
            log.warning(f"call.analyzed for unknown lead {data['lead_id']}")
            return
        lead.score = data["lead_score"]
        if data["intent"] == "high" and lead.stage in ("new", "contacted"):
            lead.stage = "hot"
        elif lead.stage == "new":
            lead.stage = "contacted"
        await s.commit()
    log.info(f"lead {lead.id} score -> {lead.score}, stage -> {lead.stage}")

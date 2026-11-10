import httpx
from loguru import logger
from pipecat.adapters.llm.schemas.function_schema import FunctionSchema
from pipecat.adapters.llm.schemas.tools_schema import ToolsSchema
from pipecat.frames.frames import EndTaskFrame
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.llm_service import FunctionCallParams

from app.config import settings
from app.context import CallContext

search_knowledge_schema = FunctionSchema(
    name="search_knowledge",
    description="Search the company's product documents (pricing, plans, EMI, trial, features, refunds). "
                "Use it BEFORE answering any factual product question.",
    properties={"query": {"type": "string", "description": "The question, in English or Hinglish"}},
    required=["query"],
)
book_followup_schema = FunctionSchema(
    name="book_followup",
    description="Book a follow-up call or demo when the customer agrees to a specific date and time.",
    properties={
        "when": {"type": "string", "description": "Date and time in ISO 8601 with +05:30, e.g. 2026-11-12T16:00:00+05:30"},
        "note": {"type": "string", "description": "Short note, e.g. 'demo with partner'"},
    },
    required=["when"],
)
end_call_schema = FunctionSchema(
    name="end_call",
    description="Hang up. Use only AFTER you have said goodbye.",
    properties={},
    required=[],
)
TOOLS = ToolsSchema(standard_tools=[search_knowledge_schema, book_followup_schema, end_call_schema])


def register_tools(llm, ctx: CallContext) -> None:
    async def search_knowledge(params: FunctionCallParams):
        query = params.arguments.get("query", "")
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.post(f"{settings.knowledge_url}/search", headers=ctx.headers(),
                                      json={"query": query, "top_k": 3})
                r.raise_for_status()
            hits = r.json()["hits"]
        except httpx.HTTPError as e:
            logger.warning(f"knowledge search failed: {e!r}")
            hits = None
        if hits is None:
            result = {"error": "knowledge base unavailable, say you will check and get back"}
        elif not hits:
            result = {"found": False, "note": "nothing in the documents, do NOT guess"}
        else:
            result = {"found": True, "facts": [h["text"] for h in hits]}
        await params.result_callback(result)

    async def book_followup(params: FunctionCallParams):
        if not ctx.lead_id:
            await params.result_callback({"error": "no lead linked to this call"})
            return
        body = {"scheduled_at": params.arguments["when"], "note": params.arguments.get("note")}
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.post(f"{settings.leads_url}/leads/{ctx.lead_id}/followups",
                                      headers=ctx.headers(), json=body)
            result = {"booked": True} if r.status_code == 201 else {"booked": False, "reason": r.text[:200]}
        except httpx.HTTPError as e:
            result = {"booked": False, "reason": repr(e)}
        await params.result_callback(result)

    async def end_call(params: FunctionCallParams):
        await params.result_callback({"ok": True})
        await params.llm.push_frame(EndTaskFrame(), FrameDirection.UPSTREAM)

    llm.register_function("search_knowledge", search_knowledge)
    llm.register_function("book_followup", book_followup)
    llm.register_function("end_call", end_call)

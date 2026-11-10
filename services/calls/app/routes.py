import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from salesvoice_common.auth_deps import CurrentUser, admin_only, current_user

from app import storage
from app.config import settings
from app.db import db
from app.leads_client import lead_visible
from app.metrics import compute_metrics
from app.models import Call
from app.schemas import CallDetail, CallOut, CallPage, CallUpdate
from app.worker import analyze_call

router = APIRouter()


async def get_call_for(call_id: str, user: CurrentUser, s: AsyncSession, full: bool = False) -> Call:
    query = select(Call).where(Call.id == call_id)
    if full:
        query = query.options(selectinload(Call.segments), selectinload(Call.analysis))
    call = await s.scalar(query)
    if not call or (not user.is_admin and call.owner_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Call not found")
    return call


@router.post("/calls", response_model=CallOut, status_code=status.HTTP_202_ACCEPTED)
async def upload_call(file: UploadFile = File(...), lead_id: str = Form(...),
                      user: CurrentUser = Depends(current_user),
                      s: AsyncSession = Depends(db.session)):
    filename = file.filename or "call"
    if storage.extension(filename) not in storage.ALLOWED:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Allowed: {sorted(storage.ALLOWED)}")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Max {settings.max_upload_mb} MB")

    try:
        if not await lead_visible(lead_id, user):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Leads service unavailable")

    call = Call(lead_id=lead_id, owner_id=user.id, filename=filename, size_bytes=len(data), audio_path="")
    s.add(call)
    await s.flush()
    call.audio_path = storage.save(call.id, filename, data)
    await s.commit()
    await s.refresh(call)

    analyze_call.delay(call.id)
    return call


@router.get("/calls", response_model=CallPage)
async def list_calls(lead_id: str | None = None,
                     limit: int = Query(default=20, ge=1, le=100),
                     offset: int = Query(default=0, ge=0),
                     user: CurrentUser = Depends(current_user),
                     s: AsyncSession = Depends(db.session)):
    query = select(Call)
    if not user.is_admin:
        query = query.where(Call.owner_id == user.id)
    if lead_id:
        query = query.where(Call.lead_id == lead_id)
    total = await s.scalar(select(func.count()).select_from(query.subquery()))
    rows = await s.scalars(query.order_by(Call.created_at.desc()).limit(limit).offset(offset))
    return CallPage(items=list(rows), total=total, limit=limit, offset=offset)


@router.get("/calls/{call_id}", response_model=CallDetail)
async def get_call(call_id: str, user: CurrentUser = Depends(current_user),
                   s: AsyncSession = Depends(db.session)):
    return await get_call_for(call_id, user, s, full=True)


@router.patch("/calls/{call_id}", response_model=CallDetail)
async def update_call(call_id: str, body: CallUpdate, user: CurrentUser = Depends(current_user),
                      s: AsyncSession = Depends(db.session)):
    call = await get_call_for(call_id, user, s, full=True)
    call.rep_speaker = body.rep_speaker
    if call.analysis:
        call.analysis.metrics = compute_metrics(call.segments, call.rep_speaker, call.duration_s or 0.0)
    await s.commit()
    return await get_call_for(call_id, user, s, full=True)


@router.post("/calls/{call_id}/retry", response_model=CallOut, status_code=status.HTTP_202_ACCEPTED)
async def retry_call(call_id: str, user: CurrentUser = Depends(current_user),
                     s: AsyncSession = Depends(db.session)):
    call = await get_call_for(call_id, user, s)
    if call.status != "failed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Only failed calls can be retried")
    call.status, call.error = "queued", None
    await s.commit()
    analyze_call.delay(call.id)
    return call


@router.delete("/calls/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(call_id: str, user: CurrentUser = Depends(current_user),
                      s: AsyncSession = Depends(db.session)):
    admin_only(user)
    call = await get_call_for(call_id, user, s)
    storage.delete(call.audio_path)
    await s.delete(call)
    await s.commit()

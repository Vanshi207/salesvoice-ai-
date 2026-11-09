from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from salesvoice_common.auth_deps import CurrentUser, admin_only, current_user

from app.db import db
from app.models import FollowUp, Lead
from app.schemas import (FollowUpCreate, FollowUpOut, LeadCreate, LeadOut, LeadPage,
                         LeadUpdate, Stage)

router = APIRouter()


async def get_lead_for(lead_id: str, user: CurrentUser, s: AsyncSession) -> Lead:
    lead = await s.get(Lead, lead_id)
    if not lead or (not user.is_admin and lead.owner_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    return lead


@router.post("/leads", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
async def create_lead(body: LeadCreate, user: CurrentUser = Depends(current_user),
                      s: AsyncSession = Depends(db.session)):
    dup = await s.scalar(select(Lead).where(Lead.phone == body.phone, Lead.owner_id == user.id))
    if dup:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have a lead with this phone number")
    lead = Lead(**body.model_dump(), owner_id=user.id,
                consent_at=datetime.now(timezone.utc) if body.consent else None)
    s.add(lead)
    await s.commit()
    await s.refresh(lead)
    return lead


@router.get("/leads", response_model=LeadPage)
async def list_leads(stage: Stage | None = None,
                     q: str | None = Query(default=None, description="search name, phone, company"),
                     limit: int = Query(default=20, ge=1, le=100),
                     offset: int = Query(default=0, ge=0),
                     user: CurrentUser = Depends(current_user),
                     s: AsyncSession = Depends(db.session)):
    query = select(Lead)
    if not user.is_admin:
        query = query.where(Lead.owner_id == user.id)
    if stage:
        query = query.where(Lead.stage == stage)
    if q:
        like = f"%{q}%"
        query = query.where(or_(Lead.name.ilike(like), Lead.phone.ilike(like), Lead.company.ilike(like)))
    total = await s.scalar(select(func.count()).select_from(query.subquery()))
    rows = await s.scalars(query.order_by(Lead.created_at.desc()).limit(limit).offset(offset))
    return LeadPage(items=list(rows), total=total, limit=limit, offset=offset)


@router.get("/leads/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: str, user: CurrentUser = Depends(current_user),
                   s: AsyncSession = Depends(db.session)):
    return await get_lead_for(lead_id, user, s)


@router.patch("/leads/{lead_id}", response_model=LeadOut)
async def update_lead(lead_id: str, body: LeadUpdate, user: CurrentUser = Depends(current_user),
                      s: AsyncSession = Depends(db.session)):
    lead = await get_lead_for(lead_id, user, s)
    changes = body.model_dump(exclude_unset=True)
    if changes.get("consent") and not lead.consent:
        lead.consent_at = datetime.now(timezone.utc)
    for field, value in changes.items():
        setattr(lead, field, value)
    await s.commit()
    await s.refresh(lead)
    return lead


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(lead_id: str, user: CurrentUser = Depends(current_user),
                      s: AsyncSession = Depends(db.session)):
    admin_only(user)
    lead = await get_lead_for(lead_id, user, s)
    await s.delete(lead)
    await s.commit()


@router.post("/leads/{lead_id}/followups", response_model=FollowUpOut, status_code=status.HTTP_201_CREATED)
async def add_followup(lead_id: str, body: FollowUpCreate, user: CurrentUser = Depends(current_user),
                       s: AsyncSession = Depends(db.session)):
    lead = await get_lead_for(lead_id, user, s)
    if body.scheduled_at <= datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Follow-up must be in the future")
    fu = FollowUp(lead_id=lead.id, scheduled_at=body.scheduled_at, note=body.note, created_by=user.id)
    lead.stage = "follow_up"
    s.add(fu)
    await s.commit()
    await s.refresh(fu)
    return fu


@router.get("/leads/{lead_id}/followups", response_model=list[FollowUpOut])
async def list_followups(lead_id: str, user: CurrentUser = Depends(current_user),
                         s: AsyncSession = Depends(db.session)):
    lead = await get_lead_for(lead_id, user, s)
    rows = await s.scalars(select(FollowUp).where(FollowUp.lead_id == lead.id).order_by(FollowUp.scheduled_at))
    return list(rows)

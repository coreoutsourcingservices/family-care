"""Common consent validation and immutable grant events."""
from datetime import datetime, timezone
from uuid import UUID
from typing import Literal
from pydantic import Field, model_validator
from flask import g, jsonify
from sqlalchemy import select
from core.database import db
from core.models import HealthAccessEvent, User, now
from core.schemas import Schema


class GrantInput(Schema):
    recipient_id: UUID
    permissions: dict[str,Literal['view','edit']] = Field(min_length=1,max_length=15)
    starts_at: datetime | None = None
    expires_at: datetime | None = None

    @model_validator(mode='after')
    def dates(self):
        for field in ('starts_at','expires_at'):
            value=getattr(self,field)
            if value:
                if value.tzinfo is None:raise ValueError('Dates must include a timezone')
                setattr(self,field,value.astimezone(timezone.utc).replace(tzinfo=None))
        if self.expires_at and self.expires_at <= max(self.starts_at or now(),now()):raise ValueError('End must be after the start and in the future')
        return self


def event(profile,grant,action):
    db().add(HealthAccessEvent(profile_id=profile.id,actor_id=g.user.id,recipient_id=grant.recipient_id,
        action=action,permissions=dict(grant.permissions),starts_at=grant.starts_at,expires_at=grant.expires_at))


def history(profile):
    rows=db().scalars(select(HealthAccessEvent).where(HealthAccessEvent.profile_id==profile.id).order_by(HealthAccessEvent.created_at.desc()).limit(200))
    return jsonify(items=[dict(id=r.id,action=r.action,name=db().get(User,r.recipient_id).full_name,permissions=r.permissions,
        created_at=r.created_at.isoformat()+'Z',starts_at=r.starts_at.isoformat()+'Z' if r.starts_at else None,
        expires_at=r.expires_at.isoformat()+'Z' if r.expires_at else None) for r in rows])

from sqlalchemy import Column as C, String as S, Text, DateTime as DT, Integer as I, JSON, ForeignKey as FK, UniqueConstraint as UQ
from sqlalchemy import Uuid
from core.database import Base
from core.models import primary_id, now


class DoctorNotification(Base):
    __tablename__ = 'doctor_notifications'
    __table_args__ = (UQ('user_id', 'event_key'),)
    id = primary_id()
    user_id = C(Uuid(as_uuid=False), FK('familycare.users.id', ondelete='CASCADE'), nullable=False, index=True)
    event_key = C(S(200), nullable=False)
    kind = C(S(40), nullable=False)
    title = C(S(160), nullable=False)
    body = C(S(300), nullable=False)
    path = C(S(160), nullable=False)
    created_at = C(DT, default=now, nullable=False, index=True)
    read_at = C(DT)


class DoctorPushSubscription(Base):
    __tablename__ = 'doctor_push_subscriptions'
    id = primary_id()
    user_id = C(Uuid(as_uuid=False), FK('familycare.users.id', ondelete='CASCADE'), nullable=False, index=True)
    endpoint = C(Text, nullable=False)
    endpoint_hash = C(S(64), nullable=False, unique=True)
    keys = C(JSON, nullable=False)
    created_at = C(DT, default=now, nullable=False)


class DoctorPushDelivery(Base):
    __tablename__ = 'doctor_push_deliveries'
    __table_args__ = (UQ('notification_id', 'subscription_id'),)
    id = primary_id()
    notification_id = C(Uuid(as_uuid=False), FK('familycare.doctor_notifications.id', ondelete='CASCADE'), nullable=False)
    subscription_id = C(Uuid(as_uuid=False), FK('familycare.doctor_push_subscriptions.id', ondelete='CASCADE'), nullable=False)
    status = C(S(20), default='PENDING', nullable=False, index=True)
    attempts = C(I, default=0, nullable=False)
    next_attempt_at = C(DT, default=now, nullable=False, index=True)

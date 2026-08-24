from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Numeric, String, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

from .razorpay import PaymentEvent
from .recovery import InterventionRecord, InterventionStatus


class PersistenceBase(DeclarativeBase):
    pass


class WebhookEvent(PersistenceBase):
    __tablename__ = "webhook_events"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payment_id: Mapped[str | None] = mapped_column(String(128), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class RecoveryIntervention(PersistenceBase):
    __tablename__ = "recovery_interventions"

    reference_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    customer_id: Mapped[str | None] = mapped_column(String(128), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    payment_id: Mapped[str | None] = mapped_column(String(128), index=True)


def init_db(engine) -> None:
    PersistenceBase.metadata.create_all(engine)


def persist_event(session: Session, event: PaymentEvent) -> bool:
    existing = session.get(WebhookEvent, event.event_id)
    if existing is not None:
        return False
    session.add(WebhookEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        payment_id=event.payment_id,
        payload=event.raw,
    ))
    session.commit()
    return True


def persist_intervention(session: Session, record: InterventionRecord) -> None:
    if session.get(RecoveryIntervention, record.reference_id) is not None:
        return
    session.add(RecoveryIntervention(
        reference_id=record.reference_id,
        customer_id=record.customer_id,
        amount=record.amount,
        status=record.status.value,
        paid_amount=record.paid_amount,
        payment_id=record.payment_id,
    ))
    session.commit()


def mark_intervention_paid(session: Session, reference_id: str, payment_id: str, amount: Decimal) -> bool:
    record = session.get(RecoveryIntervention, reference_id)
    if record is None or record.status == InterventionStatus.PAID.value:
        return False
    duplicate = session.scalar(select(RecoveryIntervention).where(RecoveryIntervention.payment_id == payment_id))
    if duplicate is not None:
        return False
    record.status = InterventionStatus.PAID.value
    record.payment_id = payment_id
    record.paid_amount = amount
    session.commit()
    return True

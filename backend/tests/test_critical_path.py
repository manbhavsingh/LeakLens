"""Integration tests for the critical LeakLens data path.

Tests cover:
- Synthetic data generation -> leak injection -> detection -> investigation -> policy -> intervention
- Deterministic demo mode (no external credentials)
- Policy gate blocks low confidence
- Policy gate blocks disallowed action types
- Idempotent event processing (same event_id -> one event)
- Idempotent job creation (same event_id -> one job)
"""
from __future__ import annotations

from decimal import Decimal

from app.detector import detect_cohort_leaks
from app.event_store import EventStore
from app.investigator import investigate
from app.interventions import FakePaymentProvider, InterventionExecutor
from app.jobs import JobQueue
from app.leaks import inject_upi_android_evening_degradation
from app.policy import validate_action
from app.synthetic import generate_transactions
from app.webhook_service import WebhookService


class TestDeterministicDemoMode:
    """LeakLens produces reproducible results without external credentials."""

    def test_generation_is_deterministic_with_same_seed(self) -> None:
        rows_a = generate_transactions(count=500, seed=99)
        rows_b = generate_transactions(count=500, seed=99)
        assert len(rows_a) == len(rows_b)
        assert all(
            a.event_id == b.event_id
            for a, b in zip(rows_a, rows_b)
        )

    def test_leak_injection_is_deterministic_with_same_seed(self) -> None:
        rows = generate_transactions(count=500, seed=42)
        leak_a = inject_upi_android_evening_degradation(rows, seed=42)
        rows2 = generate_transactions(count=500, seed=42)
        leak_b = inject_upi_android_evening_degradation(rows2, seed=42)
        assert leak_a.affected_transaction_ids == leak_b.affected_transaction_ids

    def test_no_external_credentials_required(self) -> None:
        rows = generate_transactions(count=100, seed=1)
        candidates = detect_cohort_leaks(rows)
        investigations = investigate(rows)
        # Both succeed with zero network calls
        assert isinstance(candidates, list)
        assert isinstance(investigations, list)


class TestPolicyGate:
    """Policy engine enforces confidence and action-type bounds."""

    def test_low_confidence_blocks_intervention(self) -> None:
        decision = validate_action(
            "PAYMENT_METHOD_EXPERIMENT",
            confidence=0.50,
            expected_revenue=1000,
        )
        assert decision.allowed is False
        assert "confidence" in decision.reason.lower()

    def test_high_confidence_allows_intervention(self) -> None:
        decision = validate_action(
            "PAYMENT_METHOD_EXPERIMENT",
            confidence=0.90,
            expected_revenue=1000,
        )
        assert decision.allowed is True

    def test_disallowed_action_type_is_rejected(self) -> None:
        decision = validate_action(
            "REFUND_ALL",
            confidence=0.99,
            expected_revenue=1000,
        )
        assert decision.allowed is False
        assert "not in the bounded" in decision.reason

    def test_zero_confidence_blocks_intervention(self) -> None:
        decision = validate_action(
            "RECOVERY_PAYMENT_LINK",
            confidence=0.0,
            expected_revenue=500,
        )
        assert decision.allowed is False

    def test_negative_revenue_is_rejected(self) -> None:
        decision = validate_action(
            "RECOVERY_PAYMENT_LINK",
            confidence=0.85,
            expected_revenue=-100,
        )
        assert decision.allowed is False


class TestInterventionExecutor:
    """InterventionExecutor respects the policy gate."""

    def test_low_confidence_intervention_not_executed(self) -> None:
        executor = InterventionExecutor(FakePaymentProvider())
        result = executor.execute(
            action="PAYMENT_METHOD_EXPERIMENT",
            confidence=0.40,
            expected_revenue=5000,
            reference_id="ref-test-1",
            amount=5000,
        )
        assert result.executed is False
        assert result.reason != ""

    def test_policy_approved_intervention_executed(self) -> None:
        executor = InterventionExecutor(FakePaymentProvider())
        result = executor.execute(
            action="RECOVERY_PAYMENT_LINK",
            confidence=0.85,
            expected_revenue=5000,
            reference_id="ref-test-2",
            amount=5000,
        )
        assert result.executed is True
        assert "plink_test" in result.provider_response.get("id", "")

    def test_do_not_intervene_not_executed(self) -> None:
        executor = InterventionExecutor(FakePaymentProvider())
        result = executor.execute(
            action="DO_NOT_INTERVENE",
            confidence=0.95,
            expected_revenue=0,
            reference_id="ref-test-3",
            amount=0,
        )
        assert result.executed is False
        assert "no intervention" in result.reason.lower()


class TestIdempotentEventProcessing:
    """Event store deduplicates by event_id."""

    def test_same_event_id_returns_false_on_second_add(self) -> None:
        from app.razorpay import PaymentEvent
        store = EventStore()
        event = PaymentEvent(
            event_id="evt-duplicate",
            event_type="payment.failed",
            payment_id="pay_123",
            order_id="order_123",
            amount=49900,
            status="failed",
            raw={"event": "payment.failed"},
        )
        assert store.add_if_new(event) is True
        assert store.add_if_new(event) is False

    def test_webhook_service_deduplicates_events(self) -> None:
        from app.razorpay import PaymentEvent
        store = EventStore()
        queue = JobQueue()
        service = WebhookService(store, queue)
        event = PaymentEvent(
            event_id="evt-dedup-2",
            event_type="payment.failed",
            payment_id="pay_456",
            order_id="order_456",
            amount=79900,
            status="failed",
            raw={"event": "payment.failed"},
        )
        job_id_1 = service.accept(event)
        assert job_id_1 is not None
        job_id_2 = service.accept(event)
        assert job_id_2 is None
        assert store.count() == 1


class TestIdempotentJobCreation:
    """Job queue deduplicates by event_id."""

    def test_same_event_id_creates_only_one_job(self) -> None:
        queue = JobQueue()
        job1 = queue.enqueue(event_id="evt-idempotent", job_type="investigate")
        job2 = queue.enqueue(event_id="evt-idempotent", job_type="investigate")
        assert job1.id == job2.id
        assert len(queue.jobs) == 1

    def test_different_event_ids_create_separate_jobs(self) -> None:
        queue = JobQueue()
        job1 = queue.enqueue(event_id="evt-a", job_type="investigate")
        job2 = queue.enqueue(event_id="evt-b", job_type="investigate")
        assert job1.id != job2.id
        assert len(queue.jobs) == 2


class TestFullPipeline:
    """End-to-end pipeline from synthetic data to intervention decision."""

    def test_pipeline_detects_leak_and_recommends_experiment(self) -> None:
        rows = generate_transactions(count=5000, seed=42)
        inject_upi_android_evening_degradation(rows)

        candidates = detect_cohort_leaks(rows, min_transactions=30, min_drop=0.15)
        assert candidates, "Detector should find the injected cohort leak"

        investigations = investigate(rows)
        assert investigations, "Investigator should return at least one investigation"

        top = investigations[0]
        assert top.finding.revenue_at_risk > 0
        assert top.recommended_action == "PAYMENT_METHOD_EXPERIMENT"

        decision = validate_action(
            top.recommended_action,
            confidence=top.confidence,
            expected_revenue=float(top.finding.revenue_at_risk),
        )
        assert decision.allowed is True

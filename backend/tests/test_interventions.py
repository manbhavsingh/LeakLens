from app.interventions import FakePaymentProvider, InterventionExecutor


def test_recovery_payment_link_executes_only_after_policy() -> None:
    executor = InterventionExecutor(FakePaymentProvider())
    result = executor.execute(
        action="RECOVERY_PAYMENT_LINK",
        confidence=0.90,
        expected_revenue=4999,
        reference_id="recovery-1",
        amount=499900,
    )

    assert result.executed is True
    assert result.provider_response["id"] == "plink_test_recovery-1"


def test_weak_recovery_is_rejected() -> None:
    executor = InterventionExecutor(FakePaymentProvider())
    result = executor.execute(
        action="RECOVERY_PAYMENT_LINK",
        confidence=0.50,
        expected_revenue=4999,
        reference_id="recovery-2",
        amount=499900,
    )

    assert result.executed is False

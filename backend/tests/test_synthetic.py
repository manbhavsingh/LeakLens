from app.synthetic import generate_transactions


def test_generator_is_reproducible() -> None:
    first = generate_transactions(count=25, seed=7)
    second = generate_transactions(count=25, seed=7)

    assert [row.event_id for row in first] == [row.event_id for row in second]
    assert [row.amount for row in first] == [row.amount for row in second]
    assert [row.status for row in first] == [row.status for row in second]

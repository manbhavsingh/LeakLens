from .leaks import inject_upi_android_evening_degradation
from .synthetic import generate_transactions


def build_demo_dataset(count: int = 10_000, seed: int = 42):
    rows = generate_transactions(count=count, seed=seed)
    leak = inject_upi_android_evening_degradation(rows, seed=seed)
    return rows, leak

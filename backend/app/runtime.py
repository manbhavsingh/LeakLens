from __future__ import annotations

import os

from .llm_client import OpenAICompatibleClient
from .razorpay_client import RazorpayPaymentProvider


def build_llm_client() -> OpenAICompatibleClient:
    api_key = os.environ["LEAKLENS_LLM_API_KEY"]
    model = os.getenv("LEAKLENS_LLM_MODEL", "gpt-4.1-mini")
    base_url = os.getenv("LEAKLENS_LLM_BASE_URL", "https://api.openai.com/v1")
    return OpenAICompatibleClient(api_key=api_key, model=model, base_url=base_url)


def build_razorpay_provider() -> RazorpayPaymentProvider:
    return RazorpayPaymentProvider(
        key_id=os.environ["RAZORPAY_KEY_ID"],
        key_secret=os.environ["RAZORPAY_KEY_SECRET"],
    )

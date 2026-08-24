from __future__ import annotations

import base64
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class RazorpayAPIError(RuntimeError):
    pass


class RazorpayPaymentProvider:
    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self, key_id: str, key_secret: str, *, timeout: float = 10.0):
        self.key_id = key_id
        self.key_secret = key_secret
        self.timeout = timeout

    def create_payment_link(self, *, amount: int, reference_id: str, description: str) -> dict[str, Any]:
        payload = json.dumps({
            "amount": amount,
            "currency": "INR",
            "reference_id": reference_id,
            "description": description,
            "reminder_enable": True,
        }).encode()
        credentials = base64.b64encode(f"{self.key_id}:{self.key_secret}".encode()).decode()
        request = Request(
            f"{self.BASE_URL}/payment_links",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read())
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RazorpayAPIError("Razorpay Payment Link creation failed") from exc

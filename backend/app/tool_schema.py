from __future__ import annotations

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_revenue_leaks",
            "description": "Find cohort-level revenue leakage candidates. Read-only.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_payment_failure_breakdown",
            "description": "Count failure reasons, optionally for one payment method. Read-only.",
            "parameters": {
                "type": "object",
                "properties": {"payment_method": {"type": "string"}},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_history",
            "description": "Get aggregate historical payment behavior for a customer. Read-only.",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_time_windows",
            "description": "Compare conversion before and after a supplied split timestamp. Read-only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {"type": "string"},
                    "split": {"type": "string"},
                    "end": {"type": "string"},
                },
                "required": ["start", "split", "end"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_revenue_impact",
            "description": "Estimate revenue at risk relative to an expected conversion baseline. Read-only.",
            "parameters": {
                "type": "object",
                "properties": {"expected_conversion": {"type": "number", "minimum": 0, "maximum": 1}},
                "required": ["expected_conversion"],
                "additionalProperties": False,
            },
        },
    },
]

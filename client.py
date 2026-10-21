"""Webhook Delivery Retry Engine and Exponential Backoff Jitter.
100% Python Standard Library.
"""

import hmac
import hashlib
import time
import random
from typing import Dict, Any, Optional


class WebhookDeliveryEngine:
    """Manages secure webhook event dispatching, cryptographic HMAC-SHA256 payload signing,
    replay protection, and exponential backoff with randomized jitter to eliminate thundering herds."""

    @classmethod
    def sign_payload(cls, secret: str, timestamp: int, payload_str: str) -> str:
        """Generates standard v1 HMAC-SHA256 signature over 'timestamp.payload'."""
        to_sign = f"{timestamp}.{payload_str}".encode("utf-8")
        sig = hmac.new(secret.encode("utf-8"), to_sign, hashlib.sha256).hexdigest()
        return f"t={timestamp},v1={sig}"

    @classmethod
    def verify_signature(
        cls,
        secret: str,
        signature_header: str,
        payload_str: str,
        tolerance_seconds: int = 300,
    ) -> Dict[str, Any]:
        """Validates webhook signature header and enforces timestamp freshness."""
        now = int(time.time())
        parts = {}
        for item in signature_header.split(","):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                parts[k] = v

        timestamp_str = parts.get("t")
        received_sig = parts.get("v1")

        if not timestamp_str or not received_sig:
            return {"valid": False, "reason": "MALFORMED_SIGNATURE_HEADER"}

        try:
            ts = int(timestamp_str)
        except ValueError:
            return {"valid": False, "reason": "INVALID_TIMESTAMP_FORMAT"}

        # Check timestamp drift
        if abs(now - ts) > tolerance_seconds:
            return {"valid": False, "reason": "TIMESTAMP_EXCEEDED_TOLERANCE"}

        # Recompute signature
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            f"{ts}.{payload_str}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, received_sig):
            return {"valid": False, "reason": "SIGNATURE_MISMATCH"}

        return {"valid": True, "timestamp": ts, "reason": "VERIFIED"}

    @classmethod
    def calculate_backoff_delay(
        cls,
        attempt: int,
        base_seconds: float = 1.0,
        max_seconds: float = 300.0,
    ) -> float:
        """Calculates exponential backoff delay with Full Jitter: Sleep = rand(0, min(max, base * 2^attempt))."""
        exponential = min(max_seconds, base_seconds * (2 ** max(0, attempt - 1)))
        # Full jitter between 0 and exponential
        jittered_delay = random.uniform(0.5 * exponential, exponential)
        return round(jittered_delay, 2)

    @classmethod
    def evaluate_delivery_outcome(
        cls,
        event_id: str,
        endpoint_url: str,
        http_status: int,
        attempt: int,
        max_attempts: int = 5,
    ) -> Dict[str, Any]:
        """Evaluates whether an HTTP delivery result is terminal, retryable, or DLQ candidate."""
        is_success = 200 <= http_status < 300
        if is_success:
            return {
                "event_id": event_id,
                "status": "DELIVERED",
                "attempt": attempt,
                "next_retry_seconds": None,
                "move_to_dlq": False,
                "message": f"Webhook delivered successfully with HTTP {http_status}.",
            }

        # 4xx errors (except 429 Too Many Requests and 408 Timeout) are typically non-retryable client bugs
        is_client_fatal = 400 <= http_status < 500 and http_status not in (408, 429)

        if is_client_fatal:
            return {
                "event_id": event_id,
                "status": "FAILED_TERMINAL",
                "attempt": attempt,
                "next_retry_seconds": None,
                "move_to_dlq": True,
                "message": f"Non-retryable client error HTTP {http_status}. Moved to Dead Letter Queue.",
            }

        # Check if attempts exhausted
        if attempt >= max_attempts:
            return {
                "event_id": event_id,
                "status": "EXHAUSTED",
                "attempt": attempt,
                "next_retry_seconds": None,
                "move_to_dlq": True,
                "message": f"Maximum retry attempts ({max_attempts}) reached. Moved to Dead Letter Queue.",
            }

        delay = cls.calculate_backoff_delay(attempt)
        return {
            "event_id": event_id,
            "status": "RETRY_SCHEDULED",
            "attempt": attempt,
            "next_retry_seconds": delay,
            "move_to_dlq": False,
            "message": f"Encountered HTTP {http_status}. Retrying in {delay}s (Attempt {attempt + 1}/{max_attempts}).",
        }

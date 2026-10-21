"""Example usage for Webhook Delivery Retry Engine and Exponential Backoff Jitter."""
import time
from client import WebhookDeliveryEngine


def main():
    secret = "whsec_test_secret_key_99218"
    payload = '{"event": "subscription.renewed", "account_id": "acc_8819", "amount": 2900}'
    now = int(time.time())

    print("=== 1. Signing Outgoing Webhook Payload ===")
    sig_header = WebhookDeliveryEngine.sign_payload(secret, now, payload)
    print("Generated Header:", sig_header)

    print("\n=== 2. Verifying Webhook Header at Receiver ===")
    v_res = WebhookDeliveryEngine.verify_signature(secret, sig_header, payload)
    print("Verification Result:", v_res)
    assert v_res["valid"] is True

    print("\n=== 3. Simulating Transient 503 Server Error (Retry with Jitter) ===")
    retry_decision = WebhookDeliveryEngine.evaluate_delivery_outcome(
        event_id="evt_01J8K9",
        endpoint_url="https://api.partner.com/webhooks",
        http_status=503,
        attempt=1,
    )
    print("Status:", retry_decision["status"])
    print("Next Retry In:", retry_decision["next_retry_seconds"], "seconds")
    print("Message:", retry_decision["message"])

    print("\n=== 4. Simulating Exhausted Retries (Escalation to DLQ) ===")
    dlq_decision = WebhookDeliveryEngine.evaluate_delivery_outcome(
        event_id="evt_01J8K9",
        endpoint_url="https://api.partner.com/webhooks",
        http_status=500,
        attempt=5,
        max_attempts=5,
    )
    print("Status:", dlq_decision["status"])
    print("Move to DLQ:", dlq_decision["move_to_dlq"])
    print("Message:", dlq_decision["message"])


if __name__ == "__main__":
    main()

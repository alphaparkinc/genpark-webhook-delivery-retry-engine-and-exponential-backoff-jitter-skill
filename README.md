# genpark-webhook-delivery-retry-engine-and-exponential-backoff-jitter-skill

Idempotent webhook delivery engine, HMAC signature verifier, exponential backoff with full jitter, and DLQ triager.

100% Python Standard Library implementation with zero external dependencies.

## Key Capabilities

- **HMAC-SHA256 Payload Signing & Verification**: Guarantees authenticity and integrity with timestamped signature headers (`t=...,v1=...`).
- **Replay Attack Mitigation**: Enforces strict timestamp drift tolerances preventing stale replay exploits.
- **Exponential Backoff with Full Jitter**: Prevents downstream system thundering herds during outages via decorrelated randomized wait times.
- **Terminal Fault & Dead Letter Queue (DLQ) Routing**: Distinguishes non-retryable 4xx client errors from retryable 5xx failures, routing exhausted events to DLQ.

## Architecture

```
[Outbound Webhook Event Payload]
               │
               ▼
┌─────────────────────────────────────────────────────┐
│             WebhookDeliveryEngine                   │
│  - HMAC-SHA256 Cryptographic Signer & Verifier      │
│  - Replay Timestamp Drift Enforcement               │
│  - Full Jitter Exponential Backoff Scheduler        │
│  - HTTP Status Code & DLQ Policy Arbiter            │
└─────────────────────────────────────────────────────┘
         │                               │
  (Transient Error)             (Exhausted / Fatal)
         ▼                               ▼
[Jittered Retry Queue]          [Dead Letter Queue (DLQ)]
```

## MCP Server Integration

Run standard MCP stdio server:
```bash
python mcp_server.py
```

Exposed Tools:
- `sign_payload`: Generates HMAC-SHA256 signature header for webhook payload.
- `verify_signature`: Validates incoming webhook HMAC signature and checks timestamp tolerance.
- `evaluate_delivery_outcome`: Evaluates webhook delivery HTTP response to determine retry delay or DLQ escalation.

## Quickstart (Python API)

```python
import time
from client import WebhookDeliveryEngine

secret = "whsec_live_key"
now = int(time.time())
sig = WebhookDeliveryEngine.sign_payload(secret, now, '{"event":"paid"}')
print("Signature:", sig)
```

---

## GenPark Ecosystem

- **Official Website**: [https://www.genpark.ai](https://www.genpark.ai)
- **LinkedIn Page**: [https://www.linkedin.com/company/92955550](https://www.linkedin.com/company/92955550)

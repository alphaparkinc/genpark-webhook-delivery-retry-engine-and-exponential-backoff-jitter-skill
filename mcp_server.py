"""MCP server for Webhook Delivery Retry Engine and Exponential Backoff Jitter."""
import sys
import json
from client import WebhookDeliveryEngine


def handle_request(req):
    method = req.get("method")
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "sign_payload",
                    "description": "Generates HMAC-SHA256 signature header for webhook payload",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "secret": {"type": "string"},
                            "timestamp": {"type": "integer"},
                            "payload_str": {"type": "string"},
                        },
                        "required": ["secret", "timestamp", "payload_str"],
                    },
                },
                {
                    "name": "verify_signature",
                    "description": "Validates incoming webhook HMAC signature and checks timestamp tolerance",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "secret": {"type": "string"},
                            "signature_header": {"type": "string"},
                            "payload_str": {"type": "string"},
                            "tolerance_seconds": {"type": "integer", "default": 300},
                        },
                        "required": ["secret", "signature_header", "payload_str"],
                    },
                },
                {
                    "name": "evaluate_delivery_outcome",
                    "description": "Evaluates webhook delivery HTTP response to determine retry delay or DLQ escalation",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "event_id": {"type": "string"},
                            "endpoint_url": {"type": "string"},
                            "http_status": {"type": "integer"},
                            "attempt": {"type": "integer"},
                            "max_attempts": {"type": "integer", "default": 5},
                        },
                        "required": ["event_id", "endpoint_url", "http_status", "attempt"],
                    },
                },
            ]
        }
    elif method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})
        if tool_name == "sign_payload":
            res = WebhookDeliveryEngine.sign_payload(
                secret=args.get("secret"),
                timestamp=args.get("timestamp"),
                payload_str=args.get("payload_str"),
            )
            return {"content": [{"type": "text", "text": res}]}
        elif tool_name == "verify_signature":
            res = WebhookDeliveryEngine.verify_signature(
                secret=args.get("secret"),
                signature_header=args.get("signature_header"),
                payload_str=args.get("payload_str"),
                tolerance_seconds=args.get("tolerance_seconds", 300),
            )
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
        elif tool_name == "evaluate_delivery_outcome":
            res = WebhookDeliveryEngine.evaluate_delivery_outcome(
                event_id=args.get("event_id"),
                endpoint_url=args.get("endpoint_url"),
                http_status=args.get("http_status"),
                attempt=args.get("attempt"),
                max_attempts=args.get("max_attempts", 5),
            )
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
    return {"error": "Method not found"}


if __name__ == "__main__":
    for line in sys.stdin:
        if line.strip():
            print(json.dumps(handle_request(json.loads(line))))
            sys.stdout.flush()

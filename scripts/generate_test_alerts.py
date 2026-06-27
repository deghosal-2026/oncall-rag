#!/usr/bin/env python3
"""
Generate sample alert files in alerts/inbox/ for testing.

Usage:
  python scripts/generate_test_alerts.py
  python scripts/generate_test_alerts.py --count 20
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

INBOX_DIR = Path("alerts/inbox")
SCRIPTS_DIR = Path(__file__).resolve().parent

ALERT_TEMPLATES = [
    {
        "service": "kubernetes",
        "title": "Pod CrashLoopBackOff",
        "message": "Pod nginx-abc123 in namespace default is in CrashLoopBackOff state. Restart count: 5.",
        "severity": "critical",
        "labels": {"namespace": "default", "pod": "nginx-abc123"},
    },
    {
        "service": "kubernetes",
        "title": "Node Not Ready",
        "message": "Node ip-10-0-1-42 is in NotReady state for 5 minutes.",
        "severity": "critical",
        "labels": {"node": "ip-10-0-1-42"},
    },
    {
        "service": "kubernetes",
        "title": "Service has no endpoints",
        "message": "Service my-app in namespace production has no endpoints for 2 minutes.",
        "severity": "warning",
        "labels": {"namespace": "production", "service": "my-app"},
    },
    {
        "service": "grafana",
        "title": "Grafana OnCall integration failing",
        "message": "Integration webhook-prod is failing to send alerts. HTTP 503 errors.",
        "severity": "warning",
        "labels": {"integration": "webhook-prod"},
    },
    {
        "service": "grafana",
        "title": "Escalation policy not triggering",
        "message": "Escalation policy 'prod-oncall' failed to trigger notification for alert alert-789.",
        "severity": "critical",
        "labels": {"policy": "prod-oncall"},
    },
    {
        "service": "sre",
        "title": "Error budget exhausted",
        "message": "Error budget for service user-api is exhausted (99.9% SLO, current: 99.1%).",
        "severity": "critical",
        "labels": {"service": "user-api", "slo": "99.9"},
    },
    {
        "service": "sre",
        "title": "Incident response required",
        "message": "P1 incident declared: database replica lag exceeding 5 minutes.",
        "severity": "critical",
        "labels": {"incident_id": "INC-2026-001"},
    },
    {
        "service": "unknown",
        "title": "Unknown service error",
        "message": "An unknown error occurred on host server-01.",
        "severity": "info",
        "labels": {"host": "server-01"},
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate test alerts for FIFO pipeline")
    parser.add_argument("--count", type=int, default=8, help="Number of alerts to generate (default: 8)")
    args = parser.parse_args()

    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(INBOX_DIR.glob("*.json"))
    if existing:
        print(f"alerts/inbox/ already has {len(existing)} file(s). Remove them first to regenerate.")
        sys.exit(1)

    for i in range(args.count):
        tmpl = ALERT_TEMPLATES[i % len(ALERT_TEMPLATES)]
        alert = {
            "alert_id": f"{tmpl['service']}-{i+1:04d}",
            "title": tmpl["title"],
            "message": tmpl["message"],
            "service": tmpl["service"],
            "severity": tmpl["severity"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "labels": tmpl["labels"],
        }
        path = INBOX_DIR / f"{alert['alert_id']}.json"
        path.write_text(json.dumps(alert, indent=2))
        print(f"  Created {path.name}")

    print(f"\nGenerated {args.count} alert(s) in {INBOX_DIR}/")
    print("Run `oncall-rag process-alerts` to process them.")


if __name__ == "__main__":
    main()

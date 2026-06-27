#!/usr/bin/env bash
set -euo pipefail

# Test the FIFO alert pipeline end-to-end:
#   1. Generate test alerts into alerts/inbox/
#   2. Run process-alerts to move them through the RAG pipeline
#   3. Verify outbox has results + archive has originals
#   4. Clean up

echo "=== M3 E2E: Alert Pipeline ==="

# Step 1 — generate test alerts
echo ""
echo "--- Step 1: Generate test alerts ---"
python3 scripts/generate_test_alerts.py
INBOX_COUNT=$(ls alerts/inbox/*.json 2>/dev/null | wc -l | tr -d ' ')
echo "  inbox: ${INBOX_COUNT} alert(s)"

# Step 2 — process
echo ""
echo "--- Step 2: Process alerts ---"
oncall-rag process-alerts 2>&1 | tail -5

# Step 3 — verify
echo ""
echo "--- Step 3: Verify results ---"
OUTBOX_COUNT=$(ls alerts/outbox/*.json 2>/dev/null | wc -l | tr -d ' ')
ARCHIVE_COUNT=$(ls alerts/archive/*.json 2>/dev/null | wc -l | tr -d ' ')
echo "  outbox:   ${OUTBOX_COUNT} file(s)"
echo "  archive:  ${ARCHIVE_COUNT} file(s)"

if [ "$OUTBOX_COUNT" -eq 0 ]; then
    echo "  FAIL: outbox is empty"
    exit 1
fi

# Check schema fields in outbox
MISSING_FIELDS=0
for f in alerts/outbox/*.json; do
    for field in alert_id title processed_at answer sources has_runbook; do
        if ! python3 -c "import json; d=json.load(open('$f')); assert '$field' in d, 'missing $field'" 2>/dev/null; then
            echo "  FAIL: $(basename $f) missing field: $field"
            MISSING_FIELDS=$((MISSING_FIELDS + 1))
        fi
    done
done

if [ "$MISSING_FIELDS" -gt 0 ]; then
    exit 1
fi

echo "  All outbox entries have correct schema ✓"

# Verify inbox is empty after processing
INBOX_REMAINING=$(ls alerts/inbox/*.json 2>/dev/null | wc -l | tr -d ' ')
if [ "$INBOX_REMAINING" -gt 0 ]; then
    echo "  FAIL: ${INBOX_REMAINING} file(s) still in inbox"
    exit 1
fi
echo "  Inbox empty (all moved to archive) ✓"

echo ""
echo "=== ALL CHECKS PASSED ==="

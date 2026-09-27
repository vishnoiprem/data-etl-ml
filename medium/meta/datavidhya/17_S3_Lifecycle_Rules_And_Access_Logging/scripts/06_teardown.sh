#!/usr/bin/env bash
# 06_teardown.sh -- lab stage 6: disable logging, then empty + delete both
# buckets. Idempotent: each step is safe to re-run.
set -euo pipefail
: "${DATA_BUCKET:?Run 00_set_buckets.sh first}"
: "${LOG_BUCKET:?Run 00_set_buckets.sh first}"

echo "[lab-stage-6] disabling server access logging"
aws s3api put-bucket-logging --bucket "$DATA_BUCKET" \
    --bucket-logging-status '{}' 2>/dev/null || true

for b in "$DATA_BUCKET" "$LOG_BUCKET"; do
    echo "[lab-stage-6] emptying $b (including all versions)"
    versions="$(aws s3api list-object-versions --bucket "$b" --output json 2>/dev/null \
        | python3 -c 'import json,sys;
d=json.load(sys.stdin); o=[{"Key":v["Key"],"VersionId":v["VersionId"]} for v in d.get("Versions",[])];
m=[{"Key":v["Key"],"VersionId":v["VersionId"]} for v in d.get("DeleteMarkers",[])];
print(json.dumps({"Objects":o+m}))' 2>/dev/null || true)"
    if [[ "$versions" != '{"Objects": null}' && "$versions" != '{}' && -n "$versions" ]]; then
        aws s3api delete-objects --bucket "$b" --delete "$versions" >/dev/null || true
    fi
    aws s3 rm --recursive "s3://$b/" >/dev/null 2>&1 || true
    echo "[lab-stage-6] deleting bucket $b"
    aws s3api delete-bucket --bucket "$b"
done

echo "[lab-stage-6] teardown complete"

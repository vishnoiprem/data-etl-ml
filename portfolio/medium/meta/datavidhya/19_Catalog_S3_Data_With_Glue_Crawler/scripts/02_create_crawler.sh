#!/usr/bin/env bash
# 02_create_crawler.sh -- lab stage 2: define the Glue crawler.
#
# The crawler has:
#   - a name (used by StartCrawler / GetCrawler)
#   - an IAM role (lab pre-provisions GlueCrawlerLabRole-XXXXX)
#   - a target Glue database (where tables are registered)
#   - one S3 target per prefix to crawl
#
# Glue crawls one table per folder of homogeneous files. The lab crawls
# both prefixes in a single crawler so we get two tables out of one run.
set -euo pipefail
: "${BUCKET:?Set BUCKET first -- see 00_set_lab.sh}"
: "${DATABASE:?Set DATABASE first -- see 00_set_lab.sh}"
: "${ROLE_ARN:?Set ROLE_ARN first -- see 00_set_lab.sh}"

CRAWLER="orders-and-customers-crawler"

echo "[lab-stage-2] deleting any pre-existing crawler (idempotent)"
aws glue delete-crawler --name "$CRAWLER" 2>/dev/null || true

echo "[lab-stage-2] creating the crawler"
aws glue create-crawler \
    --name "$CRAWLER" \
    --role "$ROLE_ARN" \
    --database-name "$DATABASE" \
    --targets "{\"S3Targets\":[
        {\"Path\": \"s3://${BUCKET}/raw/orders/\"},
        {\"Path\": \"s3://${BUCKET}/raw/customers/\"}
    ]}"

echo
echo "[lab-stage-2] verify crawler configuration"
aws glue get-crawler --name "$CRAWLER" \
    --query 'Crawler.[Name,DatabaseName,Role,State]' \
    --output text

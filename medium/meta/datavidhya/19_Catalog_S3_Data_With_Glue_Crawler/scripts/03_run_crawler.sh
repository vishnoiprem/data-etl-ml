#!/usr/bin/env bash
# 03_run_crawler.sh -- lab stage 3: start the crawler, wait for it, list tables.
#
# StartCrawler kicks the crawler off. Glue crawlers take 30-90 seconds for
# a small bucket; we poll GetCrawler until State goes from RUNNING to
# READY (READY means the last run completed). CrawlDuration in
# GetCrawlerMetrics tells you how long the run took in seconds.
set -euo pipefail
: "${DATABASE:?Set DATABASE first -- see 00_set_lab.sh}"

CRAWLER="orders-and-customers-crawler"

echo "[lab-stage-3] starting the crawler"
aws glue start-crawler --name "$CRAWLER"
sleep 5

echo "[lab-stage-3] waiting for crawler to finish..."
while true; do
    STATE=$(aws glue get-crawler --name "$CRAWLER" \
              --query 'Crawler.State' --output text)
    echo "    state = $STATE"
    if [ "$STATE" = "READY" ]; then break; fi
    sleep 10
done

echo
echo "[lab-stage-3] crawler done -- tables in the database:"
aws glue get-tables --database-name "$DATABASE" \
    --query 'TableList[].[Name,CreateTime,UpdateTime]' \
    --output text

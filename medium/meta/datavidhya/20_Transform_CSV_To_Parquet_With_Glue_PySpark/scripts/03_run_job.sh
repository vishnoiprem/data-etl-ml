#!/usr/bin/env bash
# 03_run_job.sh -- lab stage 3: start the job + wait for it to finish.
#
# StartJobRun returns a JobRunId immediately; the job runs asynchronously on
# AWS-provisioned Spark workers. We poll GetJobRun until JobRunState goes
# from RUNNING to SUCCEEDED / FAILED / STOPPED.
set -euo pipefail

JOB="sales-etl-q20"

echo "[lab-stage-3] starting the Glue job"
RUN_ID=$(aws glue start-job-run --job-name "$JOB" \
            --query 'JobRunId' --output text)
echo "    JobRunId=$RUN_ID"

echo "[lab-stage-3] waiting for the run to finish..."
while true; do
    STATE=$(aws glue get-job-run --job-name "$JOB" --run-id "$RUN_ID" \
              --query 'JobRun.JobRunState' --output text)
    case "$STATE" in
        SUCCEEDED) echo "    state=SUCCEEDED -- job done"; break ;;
        FAILED|STOPPED|TIMEOUT|ERROR)
            echo "    state=$STATE -- job did not succeed"
            aws glue get-job-run --job-name "$JOB" --run-id "$RUN_ID" \
                --query 'JobRun.ErrorMessage' --output text
            exit 1
            ;;
        *) sleep 15 ;;
    esac
done

echo
echo "[lab-stage-3] job duration:"
aws glue get-job-run --job-name "$JOB" --run-id "$RUN_ID" \
    --query 'JobRun.ExecutionTime' --output text

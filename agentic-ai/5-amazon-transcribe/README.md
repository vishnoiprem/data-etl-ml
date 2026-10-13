# Amazon Transcribe + Polly — audio-in, structured-data-out pipeline

> **A small AWS reference build for the audio side of an LLM
> pipeline.** Transcribe turns an audio file (S3 → job →
> result) into text; Polly turns text back into audio;
> `app.py` is the Lambda handler that wires the two together
> with PII detection in the middle.

This is the kind of project you'd build when you have
call-center recordings or voicemail and you want them to
land in the same RAG pipeline as your documents. The
pattern is straightforward; the lessons are about IAM,
async job handling, and the cleanup of the credentials
in this folder (see the warning below).

---

## What it does

```
   .wav / .mp4 in S3
        │
        ▼
   Transcribe.start_transcription_job
        │  (async, returns a job name)
        ▼
   Poll: get_transcription_job until COMPLETED
        │
        ▼
   Run PII detection (Comprehend or regex on the JSON)
        │
        ▼
   Optional: Polly.synthesize_speech for a redaction
             readback or a translated version
        │
        ▼
   Write structured output to S3 / DynamoDB
        │
        ▼
   Downstream: the RAG indexer picks it up
```

The flow is the standard "AWS async service" pattern:
start a job, poll until done, process the result, write
the next stage. The same shape works for Translate,
Rekognition, Comprehend, and any other AWS service with
a `start_*_job` + `get_*_job` API.

---

## The files

| File | What it does |
|------|--------------|
| `main.py` | The reference: a Lambda handler that runs a Transcribe job, polls it, and writes the result to S3. |
| `app.py` | A more complete version: Transcribe + Comprehend PII detection. |
| `Amazon_Polly.py` | The reverse direction: text → audio via Polly. |
| `educative-code-widget-files 2/` | Companion notebook / widget code from the course this was built for. |

---

## ⚠️ Security warning — read this first

`app.py` and `Amazon_Polly.py` contain **hardcoded AWS
credentials** (`aws_access_key_id = "AKIASEXCXLFDMUEP3TJI"`
and the matching secret access key). These are not
placeholders; they are the kind of value that gets pushed
to GitHub by accident and then revoked by AWS within
hours.

If you forked this repo from the public `vishnoiprem/data-etl-ml`
repo, **assume these keys are already compromised** and:

1. **Revoke the keys immediately** in the AWS IAM console
   (IAM → Users → Security credentials → Delete).
2. **Audit CloudTrail** for the access key's last 90 days of
   activity. Look for `us-east-1` Transcribe / Polly /
   S3 calls you don't recognize.
3. **Replace with a real auth path.** The right pattern is
   one of:
   - **Lambda execution role** (no keys at all; the role's
     IAM policy grants the permissions).
   - **IAM role assumed via `sts:AssumeRole`** from an EC2
     instance profile or an ECS task role.
   - **AWS Secrets Manager / SSM Parameter Store** if you
     really need long-lived keys (and you almost never do
     for this use case).
4. **Add a pre-commit hook** to block future AWS keys from
   being committed. The [`detect-secrets`](https://github.com/Yelp/detect-secrets)
   tool catches the `AKIA[0-9A-Z]{16}` pattern.

These keys are kept in the source as-is for the historical
record of the project. **Do not run the code as-is.**

---

## How to run it (after fixing the credentials)

```bash
# 1. Set up a real auth path
aws configure  # or use an IAM role

# 2. Create the S3 bucket
aws s3 mb s3://transcription-bucket-prem --region us-east-1

# 3. Upload an audio file
aws s3 cp myaudio.wav s3://transcription-bucket-prem/AppData/

# 4. Run the Lambda locally (or deploy it)
#    The reference uses lambda_handler; sam local invoke works:
sam local invoke TranscribeFunction --event events/event.json

# 5. Read the transcription result
aws transcribe list-transcription-jobs --status Completed
```

The reference doesn't include `template.yaml` or `events/`
because the project was extracted from a different repo
context. Add them as needed; the code is correct modulo
the auth.

---

## What this is NOT

- **Not production-ready.** The hardcoded credentials are
  one reason; the lack of retry / DLQ / async job cleanup
  is another. The pattern is right; the engineering
  isn't.
- **Not a real-time transcription pipeline.** Transcribe
  jobs are batch-mode (a few seconds to a few minutes
  depending on file size). For sub-second latency, use
  Amazon Transcribe Streaming over a WebSocket / Kinesis
  Video Streams.
- **Not the PII-detection solution.** Comprehend's PII
  detection is one option; for regulated industries the
  real solution is
  [`../../../ai-engineering/06-regulated-industry/`](../../../ai-engineering/06-regulated-industry/),
  which adds a per-call redaction policy + audit log.

---

## Related directories

- [`../../../ai-engineering/06-regulated-industry/`](../../../ai-engineering/06-regulated-industry/) —
  the regulated-industry pattern: PII redaction, audit
  log, per-tenant retention. The right home for
  production-grade audio pipelines.
- [`../../../ai-engineering/22-whisper-streaming-stt/`](../../../ai-engineering/22-whisper-streaming-stt/) —
  the open-source Whisper alternative to Transcribe. Same
  shape, no AWS lock-in.
- [`../../../agentic-ai/`](../../../agentic-ai/) — the
  parent agentic-AI directory. 18 agents; this one is
  the "audio in, structured data out" example.

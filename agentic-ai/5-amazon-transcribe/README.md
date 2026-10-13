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

## ⚠️ Security — rotation event (2026-10-13)

**This directory used to contain hardcoded AWS credentials
(the previous commit's app.py had an `AKIA…` access key + a
matching 40-char secret). Those values are no longer in source,
and the literal key is not repeated here in case the README
is exported / scraped / cached elsewhere — only the prefix
`AKIA` is referenced below, never the rotated value.**

What changed in this commit:

1. **`app.py` and `Amazon_Polly.py`** now read credentials from
   `os.environ["AWS_ACCESS_KEY_ID"]` and
   `os.environ["AWS_SECRET_ACCESS_KEY"]`. If the env vars are
   unset, the script raises a `RuntimeError` with a clear
   message rather than silently using a hardcoded value.
2. **`AudioRecorder.jsx`** (browser-side code) no longer
   contains any AWS credential. It now uses a presigned-URL
   handoff: the browser calls a backend endpoint
   (`/api/presigned-upload`) which mints a 5–15 min S3 URL
   using the backend's IAM role. The browser uses the URL,
   no credentials in JS. (The backend endpoint is out of
   scope for this educational widget; until it ships, the
   widget is read-only.)
3. **`.env.example`** documents the env vars the scripts need.
   The real `.env` is gitignored.
4. **`tests/test_no_hardcoded_aws_keys.py`** is a regression
   test that scans the 3 source files for the `AKIA[0-9A-Z]{16}`
   pattern and the 40-char base64 secret pattern. If anyone
   re-introduces a hardcoded key, this test fails on the next
   CI run. It also asserts that `app.py` and `Amazon_Polly.py`
   raise a clear `RuntimeError` if the env vars are missing.

**If you forked this repo from the public
`vishnoiprem/data-etl-ml` repo, assume the original
hardcoded keys (the ones that used to be in `app.py`)
are compromised and:**

1. **Revoke the old keys in the AWS IAM console**
   (IAM → Users → Security credentials → Delete the access key
   that matches `AKIA...REDACTED`).
2. **Audit CloudTrail** for the access key's last 90 days of
   activity. Look for `us-east-1` Transcribe / Polly / S3
   calls you don't recognize.
3. **Generate new keys** for a fresh IAM user with
   `AmazonTranscribeFullAccess` + `AmazonPollyFullAccess` (or
   a tighter least-privilege policy). Put the new values in
   your local `.env` file (copy `.env.example`).

**Going forward:** add a pre-commit hook to block future AWS
keys from being committed. The
[`detect-secrets`](https://github.com/Yelp/detect-secrets) tool
catches the `AKIA[0-9A-Z]{16}` pattern and integrates with
pre-commit. The regression test in `tests/` is a belt-and-
suspenders backup for the case where the pre-commit hook is
skipped.

---

## How to run it (after fixing the credentials)

```bash
# 1. Set up a real auth path
#    a) Create a new IAM user + access key (see Security section above)
#    b) Copy .env.example to .env and fill in the new key + secret
cp .env.example .env
#    c) Edit .env with the new values (do NOT commit .env)
$EDITOR .env
#    d) Source .env into your shell
set -a; source .env; set +a

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

If you run `python3 app.py` without the env vars set, you'll
now see:

```
RuntimeError: AWS_ACCESS_KEY_ID is not set. The previous
version of this file hardcoded an AWS access key in source —
that key has been rotated and the new value must be supplied
via environment. Set it in your shell or in a .env file (see
.env.example).
```

That's the intended failure mode. Do not silence it.

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

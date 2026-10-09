"""
Audio Processor - Whisper transcription
========================================
Transcribes an audio file via OpenAI's Whisper API.

Returns the transcript as a structured dict:
{
  "text": "full transcript",
  "segments": [{"start": 0.0, "end": 3.2, "text": "..."}, ...],
  "language": "en",
  "duration_s": 123.4
}
"""

import os
import time
import json
import subprocess
import logging
import httpx

logger = logging.getLogger("sales-coach.audio")

WHISPER_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"
MAX_FILE_BYTES = 25 * 1024 * 1024  # Whisper API hard limit


def get_audio_duration(path: str) -> float:
    """Probe audio duration in seconds via ffprobe."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=10,
        )
        return float(out.stdout.strip() or 0.0)
    except Exception as e:
        logger.warning(f"ffprobe failed: {e}")
        return 0.0


def transcribe_audio(path: str, openai_api_key: str) -> tuple[dict, float, float]:
    """Transcribe an audio file. Returns (transcript_dict, duration_s, cost_usd)."""
    file_size = os.path.getsize(path)
    if file_size > MAX_FILE_BYTES:
        # In production, chunk the file and call Whisper per chunk
        # For MVP, raise clearly
        raise RuntimeError(
            f"File too large for Whisper API: {file_size / 1e6:.1f}MB "
            f"(limit {MAX_FILE_BYTES // 1e6}MB). Add chunking in audio_processor.py"
        )

    duration = get_audio_duration(path) or 0.0
    start = time.time()

    with open(path, "rb") as f:
        # Use verbose_json to get word-level timestamps
        files = {"file": (os.path.basename(path), f, "application/octet-stream")}
        data = {
            "model": "whisper-1",
            "response_format": "verbose_json",
            "timestamp_granularities[]": "segment",
        }
        headers = {"Authorization": f"Bearer {openai_api_key}"}
        resp = httpx.post(WHISPER_ENDPOINT, files=files, data=data, headers=headers, timeout=300.0)
        resp.raise_for_status()
        payload = resp.json()

    elapsed = time.time() - start
    segments = payload.get("segments", [])
    transcript = {
        "text": payload.get("text", ""),
        "language": payload.get("language", "en"),
        "duration_s": payload.get("duration", duration),
        "segments": [
            {"start": s.get("start", 0.0), "end": s.get("end", 0.0), "text": s.get("text", "").strip()}
            for s in segments
        ],
    }
    # Whisper cost: $0.006 per minute
    cost = transcript["duration_s"] / 60.0 * 0.006
    logger.info(
        f"whisper transcribed {transcript['duration_s']:.1f}s "
        f"in {elapsed:.1f}s cost=${cost:.4f}"
    )
    return transcript, transcript["duration_s"], cost

"""Real-Time Voice AI — core service.

A pipeline model for real-time voice assistants (à la OpenAI Realtime,
Amazon Lex, Google Dialogflow CX). We model the three stages:

    1. STT (speech-to-text):    audio chunk  ->  transcript text
    2. LLM (response gen):      transcript  ->  reply text
    3. TTS (text-to-speech):    reply text  ->  audio chunks (out)

Each stage is a deterministic mock — the *pipeline state machine* is
real and runnable. The mock STT echoes a canned phrase derived from the
audio length; the mock LLM composes a template reply; the mock TTS
synthesizes bytes that we tag with metadata so the client can see the
pipeline progressing.

The state machine per session:

    idle ──audio_in──► stt ──► llm ──► tts ──► playing
                       │       │       │
                       └──error─┴──error┴──► error

We also expose a transcript log so the client can see what the system
"heard" and what it said.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from common.storage import KeyValueStore


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


MAX_CHUNK_BYTES = 32_768
PIPELINE_STAGES = ("idle", "stt", "llm", "tts", "playing", "done", "error")
DEFAULT_TTS_CHUNK_SIZE = 256  # bytes per emitted audio chunk


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TranscriptLine:
    role: str  # "user" | "assistant"
    text: str
    created_at: float = field(default_factory=lambda: time.time())
    audio_ms: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AudioChunk:
    """A small packet of synthesized speech for the client to play."""
    chunk_id: int
    data: bytes
    text: str  # the source text this chunk renders
    is_final: bool
    created_at: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> dict:
        # Don't serialize the binary data; just metadata.
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "is_final": self.is_final,
            "size": len(self.data),
            "sha256": hashlib.sha256(self.data).hexdigest()[:16],
            "created_at": self.created_at,
        }


@dataclass
class Session:
    session_id: int
    user_id: str
    created_at: float = field(default_factory=lambda: time.time())
    state: str = "idle"
    last_text: str = ""
    audio_in_bytes: int = 0
    audio_out_bytes: int = 0
    turn_count: int = 0
    error_message: Optional[str] = None
    transcript: list[TranscriptLine] = field(default_factory=list)
    outbox: list[AudioChunk] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "state": self.state,
            "last_text": self.last_text,
            "audio_in_bytes": self.audio_in_bytes,
            "audio_out_bytes": self.audio_out_bytes,
            "turn_count": self.turn_count,
            "error_message": self.error_message,
            "transcript": [t.to_dict() for t in self.transcript],
            "outbox": [c.to_dict() for c in self.outbox],
        }


# ---------------------------------------------------------------------------
# Mock STT / LLM / TTS
# ---------------------------------------------------------------------------


_CANNED_PHRASES = (
    "what's the weather in tokyo",
    "remind me to call mom at five",
    "play some jazz music",
    "set a timer for ten minutes",
    "tell me a fun fact about octopuses",
    "what's on my calendar today",
    "how do I make a sourdough loaf",
    "what time is it in london",
)


def _mock_stt(audio: bytes) -> str:
    """Deterministic STT: pick a canned phrase from the audio hash."""
    if not audio:
        return ""
    h = hashlib.md5(audio).hexdigest()
    idx = int(h[:8], 16) % len(_CANNED_PHRASES)
    return _CANNED_PHRASES[idx]


_LLM_OPENERS = (
    "Sure! ",
    "Got it. ",
    "Happy to help. ",
    "Okay — ",
    "Here's what I can do: ",
)


def _mock_llm(text: str) -> str:
    """Deterministic LLM: template reply based on the transcript."""
    if not text:
        return "I didn't catch that. Could you try again?"
    opener = _LLM_OPENERS[hash(text) % len(_LLM_OPENERS)]
    t = text.lower()
    if "weather" in t:
        body = "It looks like it'll be partly cloudy with a high of 22°C."
    elif "remind" in t or "timer" in t:
        body = "I've set that reminder. I'll let you know when it's time."
    elif "play" in t and "music" in t:
        body = "Playing some smooth jazz for you now."
    elif "fact" in t:
        body = "Octopuses have three hearts and blue blood."
    elif "calendar" in t:
        body = "You have two meetings today: one at 10am and a 1:1 at 2pm."
    elif "time" in t:
        body = "It's currently 3:42 PM in London."
    elif "sourdough" in t:
        body = "Mix 500g flour, 350g water, 100g starter, and 10g salt. Bulk ferment 4-6h."
    else:
        body = "Here's what I found based on what you said."
    return f"{opener}{body}"


def _mock_tts_synth(text: str, chunk_size: int = DEFAULT_TTS_CHUNK_SIZE) -> list[bytes]:
    """Deterministic TTS: split text into fixed-size synthetic byte chunks.

    The bytes are pseudo-audio (just a header + body); the *number* and
    *size* of chunks is what matters for the pipeline design.
    """
    if not text:
        return []
    # Each word becomes a small "phoneme" block. We just hash a per-word
    # seed and pad.
    chunks: list[bytes] = []
    words = text.split()
    for i, _w in enumerate(words):
        seed = f"tts:{text[:32]}:{i}".encode()
        # Make a small deterministic byte string of size chunk_size.
        h = hashlib.sha256(seed).digest()
        body = (h * ((chunk_size // len(h)) + 1))[:chunk_size]
        chunks.append(body)
    return chunks


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class VoiceService:
    """A working real-time voice AI pipeline.

    >>> import tempfile
    >>> root = tempfile.mkdtemp()
    >>> svc = VoiceService(persist_dir=root)
    >>> sid = svc.create_session("u1")
    >>> chunks = svc.push_audio(sid, b"\\x00\\x01\\x02")
    >>> svc.get_session(sid).state in ("done", "playing")
    True
    >>> svc.get_transcript(sid)[-1].role
    'assistant'
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        max_chunk_bytes: int = MAX_CHUNK_BYTES,
    ):
        self.store = store or KeyValueStore("voice_ai")
        self.max_chunk_bytes = max_chunk_bytes
        self._next_id = self._max_id() + 1

    def _max_id(self) -> int:
        best = 0
        for k, _ in self.store.scan("session:"):
            try:
                best = max(best, int(k.split(":")[1]))
            except (IndexError, ValueError):
                continue
        return best

    # ---- session lifecycle --------------------------------------------

    def create_session(self, user_id: str) -> Session:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id is required")
        sid = self._next_id
        self._next_id += 1
        s = Session(session_id=sid, user_id=user_id)
        self._persist(s)
        return s

    def get_session(self, session_id: int) -> Optional[Session]:
        d = self.store.get(f"session:{session_id}")
        if not d:
            return None
        return Session(
            session_id=d["session_id"],
            user_id=d["user_id"],
            created_at=d.get("created_at", 0.0),
            state=d.get("state", "idle"),
            last_text=d.get("last_text", ""),
            audio_in_bytes=d.get("audio_in_bytes", 0),
            audio_out_bytes=d.get("audio_out_bytes", 0),
            turn_count=d.get("turn_count", 0),
            error_message=d.get("error_message"),
            transcript=[TranscriptLine(**t) for t in d.get("transcript", [])],
            outbox=[AudioChunk(**c) for c in d.get("outbox", [])],
        )

    def list_sessions(self) -> list[Session]:
        out: list[Session] = []
        for k, _ in self.store.scan("session:"):
            sid = int(k.split(":")[1])
            s = self.get_session(sid)
            if s:
                out.append(s)
        out.sort(key=lambda s: s.session_id)
        return out

    # ---- pipeline: audio in --------------------------------------------

    def push_audio(self, session_id: int, audio: bytes) -> list[AudioChunk]:
        """Push a chunk of inbound audio. Runs the full pipeline.

        Returns the list of synthesized audio chunks that should be
        played back to the user.
        """
        s = self.get_session(session_id)
        if not s:
            raise ValueError("session not found")
        if not isinstance(audio, (bytes, bytearray)):
            raise ValueError("audio must be bytes")
        if len(audio) > self.max_chunk_bytes:
            raise ValueError(
                f"audio chunk too large (>{self.max_chunk_bytes} bytes)"
            )
        if s.state == "error":
            raise ValueError(f"session is in error: {s.error_message}")

        s.audio_in_bytes += len(audio)

        # Stage 1: STT.
        try:
            s.state = "stt"
            self._persist(s)
            user_text = _mock_stt(bytes(audio))
        except Exception as e:
            s.state = "error"
            s.error_message = f"stt: {e}"
            self._persist(s)
            raise

        if not user_text:
            s.state = "idle"
            self._persist(s)
            return []

        s.transcript.append(
            TranscriptLine(role="user", text=user_text, audio_ms=len(audio) / 32.0)
        )
        s.last_text = user_text
        s.turn_count += 1

        # Stage 2: LLM.
        try:
            s.state = "llm"
            self._persist(s)
            reply_text = _mock_llm(user_text)
        except Exception as e:
            s.state = "error"
            s.error_message = f"llm: {e}"
            self._persist(s)
            raise

        s.transcript.append(
            TranscriptLine(role="assistant", text=reply_text, audio_ms=0.0)
        )
        s.last_text = reply_text

        # Stage 3: TTS.
        try:
            s.state = "tts"
            self._persist(s)
            synth = _mock_tts_synth(reply_text)
        except Exception as e:
            s.state = "error"
            s.error_message = f"tts: {e}"
            self._persist(s)
            raise

        # Stage 4: emit to outbox.
        out_chunks: list[AudioChunk] = []
        for i, data in enumerate(synth):
            chunk = AudioChunk(
                chunk_id=int(time.time() * 1e6) + i,
                data=data,
                text=reply_text,
                is_final=(i == len(synth) - 1),
            )
            s.outbox.append(chunk)
            out_chunks.append(chunk)
            s.audio_out_bytes += len(data)
        s.state = "playing"
        self._persist(s)
        return out_chunks

    # ---- streaming ----------------------------------------------------

    def iter_outbox(self, session_id: int, since: int = 0):
        """Yield outbox chunks newer than ``since`` (chunk_id)."""
        s = self.get_session(session_id)
        if not s:
            return
        for c in s.outbox:
            if c.chunk_id > since:
                yield c

    # ---- transcript / clear -------------------------------------------

    def get_transcript(self, session_id: int) -> list[TranscriptLine]:
        s = self.get_session(session_id)
        if not s:
            return []
        return list(s.transcript)

    def clear_outbox(self, session_id: int) -> int:
        s = self.get_session(session_id)
        if not s:
            return 0
        n = len(s.outbox)
        s.outbox = []
        s.state = "idle"
        self._persist(s)
        return n

    # ---- stats ---------------------------------------------------------

    def stats(self) -> dict:
        n_sessions = sum(1 for _ in self.store.scan("session:"))
        total_in = total_out = total_turns = 0
        for k, _ in self.store.scan("session:"):
            s = self.get_session(int(k.split(":")[1]))
            if s:
                total_in += s.audio_in_bytes
                total_out += s.audio_out_bytes
                total_turns += s.turn_count
        return {
            "sessions": n_sessions,
            "turns": total_turns,
            "audio_in_bytes": total_in,
            "audio_out_bytes": total_out,
        }

    # ---- internals -----------------------------------------------------

    def _persist(self, s: Session) -> None:
        self.store.set(f"session:{s.session_id}", s.to_dict())

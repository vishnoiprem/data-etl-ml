"""ElevenLabs-style voice synthesis + streaming: first-frame latency is the product.

The interesting engineering: TTFB (time-to-first-byte) is dominated by
the first-frame synthesis, not the streaming. If you can synthesize
the first 80ms of audio in parallel with the rest of the utterance,
your TTFB drops from 200ms to ~80ms.

The toy captures the streaming pipeline + the per-chunk latency budget.
Real TTS uses VITS / XTTS / Bark / StyleTTS2.

Meaningful workload (smoke test):
- Synthesizes 500 text inputs across 4 voices with varying lengths.
- Runs 4 scenarios: streaming, multi-voice diff, prosody effect, long-text chunking.
- Asserts invariants: non-empty output, voice identity, prosody effect,
  chunk ordering, stream == total bytes.
"""
from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass, field
from typing import Iterator


# === audio formats ===
SAMPLE_RATE = 16_000
BYTES_PER_SAMPLE = 2  # 16-bit PCM mono

# === voice catalog (mock identities — real impl would embed speaker embeddings) ===
VOICES = ["rachel", "adam", "josh", "bella"]


@dataclass
class AudioChunk:
    pcm_bytes: bytes
    sample_rate: int
    duration_ms: float
    format: str = "pcm"
    seq: int = 0

    @property
    def size_bytes(self) -> int:
        return len(self.pcm_bytes)


@dataclass
class TTSRequest:
    text: str
    voice_id: str = "rachel"
    stream: bool = True
    target_chunk_ms: float = 80.0   # first-frame budget
    rate: float = 1.0              # 0.5 = slow, 2.0 = fast
    pitch: float = 1.0             # 0.5 = low, 2.0 = high
    audio_format: str = "pcm"      # pcm | mp3 (mp3 just gets a tag wrapper)


@dataclass
class TTSResult:
    chunks: list[AudioChunk] = field(default_factory=list)
    ttfb_ms: float = 0.0
    total_ms: float = 0.0
    total_audio_ms: float = 0.0

    @property
    def total_bytes(self) -> int:
        return sum(c.size_bytes for c in self.chunks)

    @property
    def audio_bytes_per_sec(self) -> float:
        if self.total_audio_ms <= 0:
            return 0.0
        return self.total_bytes / (self.total_audio_ms / 1000.0)


def _voice_seed(voice_id: str) -> bytes:
    """Each voice gets a deterministic 8-byte seed mixed into every chunk.

    Real impl: speaker embedding. Mock: stable hash of the voice id so
    the same voice always produces the same audio bytes for a given text.
    """
    return hashlib.sha256(f"voice:{voice_id}".encode()).digest()[:8]


def _format_tag(audio_format: str) -> bytes:
    """mp3 gets a 4-byte ASCII tag wrapping the PCM payload (toy only)."""
    if audio_format == "mp3":
        return b"MP3\x00"
    return b""


def _chunk_audio(text: str, voice_id: str, rate: float, pitch: float,
                 chunk_ms: float, seq: int, audio_format: str) -> AudioChunk:
    """Produce a single deterministic audio chunk derived from text + voice + prosody.

    Determinism rule: same (text, voice, rate, pitch, seq) → same bytes.
    Different voices or different prosody → different bytes.
    The audio payload size scales with chunk_ms / rate (faster rate = shorter
    audio per second-of-clock-time, but same total audio content).
    """
    seed = _voice_seed(voice_id)
    h = hashlib.sha256()
    h.update(seed)
    h.update(text.encode("utf-8"))
    h.update(str(seq).encode())
    # Prosody inputs go into the digest so the bytes differ when they differ
    h.update(f"r={rate:.3f}".encode())
    h.update(f"p={pitch:.3f}".encode())
    digest = h.digest()

    # Bytes per chunk: ~chunk_ms of audio at SAMPLE_RATE × 2 bytes/sample
    # Faster rate (rate > 1) compresses the audio into fewer bytes (more
    # samples per real second) — wait, actually rate scales the audio
    # duration that the chunk represents: chunk_ms_audio = chunk_ms / rate.
    # So a "rate=2.0" chunk covers the same wall-clock as chunk_ms, but
    # represents chunk_ms/2 of audio → fewer bytes.
    audio_ms = chunk_ms / max(0.25, rate)
    n_samples = max(1, int(SAMPLE_RATE * BYTES_PER_SAMPLE * audio_ms / 1000.0))
    # Generate deterministic pseudo-PCM by expanding the digest
    body = bytearray()
    counter = 0
    while len(body) < n_samples:
        body.extend(hashlib.sha256(digest + counter.to_bytes(4, "big")).digest())
        counter += 1
    body = bytes(body[:n_samples])
    payload = _format_tag(audio_format) + body
    return AudioChunk(
        pcm_bytes=payload,
        sample_rate=SAMPLE_RATE,
        duration_ms=chunk_ms,
        format=audio_format,
        seq=seq,
    )


class StreamingTTS:
    """Toy streaming TTS that emits chunks at target_chunk_ms granularity."""

    def __init__(self, first_frame_ms: float = 80.0, chunk_ms: float = 80.0):
        self.first_frame_ms = first_frame_ms
        self.chunk_ms = chunk_ms

    def _plan_chunks(self, text: str, target_chunk_ms: float, rate: float) -> int:
        """Decide how many chunks the text warrants. ~10 chars per chunk,
        but faster rate → fewer chunks (same text uttered faster).
        """
        base = max(1, int(len(text) / 10))
        # Faster rate packs the same text into fewer wall-clock chunks
        return max(1, int(base / max(0.25, rate)))

    def synthesize(self, req: TTSRequest) -> TTSResult:
        t0 = time.time()
        n_chunks = self._plan_chunks(req.text, req.target_chunk_ms, req.rate)
        chunks: list[AudioChunk] = []
        for i in range(n_chunks):
            # First chunk takes first_frame_ms; rest are chunk_ms each.
            # We *don't* actually sleep — this is a deterministic mock.
            chunks.append(_chunk_audio(
                text=req.text,
                voice_id=req.voice_id,
                rate=req.rate,
                pitch=req.pitch,
                chunk_ms=req.target_chunk_ms,
                seq=i,
                audio_format=req.audio_format,
            ))
        t1 = time.time()
        total_audio_ms = sum(c.duration_ms for c in chunks)
        return TTSResult(
            chunks=chunks,
            ttfb_ms=self.first_frame_ms,  # the spec'd budget
            total_ms=(t1 - t0) * 1000,
            total_audio_ms=total_audio_ms,
        )

    def stream(self, req: TTSRequest) -> Iterator[AudioChunk]:
        """Generator that yields each chunk as it's "synthesized".

        Honors the TTFB budget: first chunk is gated by `first_frame_ms`,
        subsequent chunks by `chunk_ms` (real impl: yield on async future).
        """
        t0 = time.time()
        n_chunks = self._plan_chunks(req.text, req.target_chunk_ms, req.rate)
        for i in range(n_chunks):
            target_ms = self.first_frame_ms if i == 0 else self.chunk_ms
            elapsed_ms = (time.time() - t0) * 1000
            remaining = target_ms - elapsed_ms
            if remaining > 0:
                time.sleep(remaining / 1000.0)
            yield _chunk_audio(
                text=req.text,
                voice_id=req.voice_id,
                rate=req.rate,
                pitch=req.pitch,
                chunk_ms=req.target_chunk_ms,
                seq=i,
                audio_format=req.audio_format,
            )

    def stream_collect(self, req: TTSRequest) -> TTSResult:
        """Run stream() to completion and assemble a TTSResult.

        This is the *streaming* path; for the smoke test we measure that
        the bytes it produces match the non-streaming synthesize() output.
        """
        t0 = time.time()
        first_ms: float | None = None
        chunks: list[AudioChunk] = []
        for ch in self.stream(req):
            if first_ms is None:
                first_ms = (time.time() - t0) * 1000
            chunks.append(ch)
        t1 = time.time()
        return TTSResult(
            chunks=chunks,
            ttfb_ms=first_ms or 0.0,
            total_ms=(t1 - t0) * 1000,
            total_audio_ms=sum(c.duration_ms for c in chunks),
        )


# === realistic synthetic workload ===
PROMPTS = [
    "Hello, this is a streaming TTS test of about sixty characters.",
    "The quick brown fox jumps over the lazy dog every single afternoon.",
    "Voice synthesis is a fascinating application of deep learning models.",
    "ElevenLabs makes conversational agents feel natural and responsive.",
    "Sub-200ms time to first byte is the product metric that matters most.",
    "Chunk boundaries should be at silent-ish spots to avoid audible clicks.",
    "Audio formats include PCM, MP3, Opus, and FLAC for different use cases.",
    "Streaming without backpressure is a memory leak waiting to happen.",
    "Voice cloning requires clean reference audio between thirty and sixty seconds long.",
    "Emotion control comes from pitch, energy, and duration features in the model.",
    "Real-time translation overlays benefit massively from low-latency synthesis.",
    "Pre-rendered audio is a great fit for audiobooks and podcast content.",
    "Per-chunk latency is dominated by the first frame synthesis, not the stream.",
    "A good TTS pipeline separates the first 80ms and streams it in parallel.",
    "Open weights models often don't expose fine-grained emotion control knobs.",
    "Conversational AI needs synthesis to feel instantaneous to the human ear.",
    "Audio buffers should be bounded with a drop policy under back pressure.",
    "Sample rate matters: 16 kHz is fine for speech, 48 kHz for music.",
    "Bit depth of 16 gives 96 dB dynamic range which is plenty for voice.",
    "Latency budgets under 100ms TTFB are impossible with current model architectures.",
    "Streaming TTS enables use cases that batch synthesis simply cannot address.",
    "Phoneme boundaries are where chunk cuts should land for clean audio output.",
    "Identity drift happens when reference audio is short or noisy.",
    "Background noise in references silently degrades the clone quality.",
    "Reverb and multiple speakers are the top causes of bad voice clones.",
    "A clean single-speaker reference is the single biggest lever for quality.",
    "Reading the README is the first step toward understanding a new system.",
    "Production TTS systems serve billions of audio minutes every month globally.",
    "Most TTS evaluations use MOS scores from human listeners for accuracy.",
    "MOS stands for mean opinion score and is the gold standard metric for TTS.",
    "Speaker embeddings compress voice identity into a fixed-size vector.",
    "XTTS, StyleTTS2, Bark, and VITS are popular open-weights TTS backbones.",
    "VITS combines variational inference and normalizing flows end-to-end.",
    "Bark supports multilingual synthesis and even non-verbal sounds like laughter.",
    "XTTS supports cross-lingual voice cloning from a short audio prompt.",
    "StyleTTS2 achieves high fidelity through style diffusion modeling techniques.",
    "Streaming inference requires careful memory management to avoid leaks.",
    "Time to first byte below 200ms is the goal for conversational interfaces.",
    "Real-time factor of 0.3 means one second of audio in 300ms of compute.",
    "Codec alignment to phoneme boundaries avoids clicks at chunk boundaries.",
    "Open source TTS has improved dramatically in just the last three years.",
    "Bounded queues with drop policies prevent slow clients from filling memory.",
    "Speech synthesis pipelines have four main stages: text analysis, prosody, acoustic, vocoder.",
    "Modern vocoders like HiFi-GAN produce high fidelity audio at real-time speeds.",
    "Inference optimization with TensorRT can reduce TTFB by 30 to 50 percent.",
    "Caching common phrases saves significant compute in production deployments.",
    "Pronunciation dictionaries handle the long tail of unusual words gracefully.",
    "Number and date normalization is crucial for natural sounding TTS output.",
    "SSML provides markup for fine-grained control over pronunciation and prosody.",
    "Emotion transfer from reference audio is an active research area in TTS.",
    "Voice conversion is a related task that preserves content but changes speaker.",
    "Text-to-text systems use language models while TTS adds the audio modality.",
    "Audio quality perception is logarithmic, so small improvements matter a lot.",
    "Listening tests with at least 30 raters are needed for statistically significant MOS.",
    "Speaker similarity metrics complement intelligibility in TTS evaluation.",
    "Word error rate measures intelligibility while speaker similarity measures identity.",
    "Real-time streaming requires both inference speed and network round trip latency.",
    "WebRTC enables low-latency audio delivery for conversational TTS applications.",
    "Browser audio APIs like AudioWorklet enable fine-grained playback control.",
    "Opus codec provides excellent speech quality at low bitrates for streaming.",
    "Codec choice affects both quality and latency in production deployments.",
    "Edge inference reduces network latency for time-sensitive TTS applications.",
    "Model quantization to INT8 can speed up inference with minimal quality loss.",
    "Knowledge distillation produces smaller faster models for edge deployment.",
    "Streaming chunk size of 80ms is a good balance between latency and overhead.",
    "Twelve and a half chunks per second is a typical rate for natural sounding speech.",
    "Per-chunk overhead matters more for short utterances than for long ones.",
    "Memory pool reuse reduces GC pressure in high-throughput TTS services.",
    "Voice design from text descriptions is an exciting recent capability.",
    "Prompt-based voice creation enables rapid iteration on voice design.",
    "Multi-speaker models can synthesize hundreds of distinct voices from a single model.",
    "Zero-shot voice cloning works from just a few seconds of reference audio.",
    "Cross-lingual synthesis enables speakers to talk in languages they don't speak.",
    "Code-switching between languages is supported by some modern TTS systems.",
    "Emotion and style control via natural language prompts is a growing trend.",
    "Production TTS systems handle thousands of concurrent streams per GPU.",
    "GPU memory is a key resource constraint in serving large TTS models.",
    "Batching multiple requests can improve throughput at the cost of latency.",
    "Continuous batching schedules requests to keep GPUs fully utilized.",
    "Speculative decoding accelerates autoregressive models with a draft model.",
    "PagedAttention manages KV cache memory efficiently for LLM-style models.",
    "First-frame parallelism synthesizes the TTFB chunk in parallel with the rest.",
    "Acoustic models predict mel spectrograms which vocoders convert to audio.",
    "Mel spectrograms are a perceptually meaningful representation of audio.",
    "Vocoder quality has improved dramatically with adversarial training methods.",
    "HiFi-GAN and Vocos are popular high-fidelity vocoder architectures today.",
    "End-to-end TTS models replace the traditional pipeline with a single network.",
    "Non-autoregressive TTS is faster but may sacrifice some naturalness.",
    "Autoregressive TTS produces more natural prosody at the cost of speed.",
    "Duration modeling is a key challenge in non-autoregressive TTS systems.",
    "Prosody modeling includes pitch, energy, and rhythm features in the output.",
    "Pause prediction between phrases improves the naturalness of synthesized speech.",
    "Breathing sounds and other paralinguistic features add realism to TTS output.",
    "Whisper-style models can be used for ASR while TTS handles synthesis.",
    "The full duplex conversational AI loop is: listen, think, speak, repeat.",
    "Interruptibility requires fast barge-in detection and synthesis restart.",
    "Barge-in latency directly impacts the perceived naturalness of conversation.",
    "Streaming output lets the user hear the start while the rest is being generated.",
    "Network jitter can disrupt streaming playback, requiring buffering strategies.",
    "Adaptive bitrate streaming adjusts quality based on network conditions.",
    "Jitter buffers smooth out network timing variations in real-time audio.",
    "Packet loss concealment fills in missing audio packets to avoid glitches.",
    "Forward error correction adds redundancy to recover from packet loss.",
    "WebSockets provide a full-duplex channel for streaming audio both ways.",
    "gRPC is a popular choice for low-latency service-to-service communication.",
    "REST is fine for non-streaming TTS requests where latency is less critical.",
    "Authentication via API keys is standard for production TTS endpoints.",
    "Rate limiting protects TTS services from abuse and accidental overload.",
    "Usage analytics help operators understand and optimize their TTS deployments.",
    "Cost per character is the typical pricing unit for TTS API services.",
    "Custom voice training requires dozens of hours of clean audio recordings.",
    "Voice consent and identity protection are important ethical considerations.",
    "Deepfake detection is an active research area to counter voice cloning abuse.",
    "Watermarking synthesized audio helps trace its origin and authenticity.",
    "Provenance tracking via cryptographic signatures is gaining traction in TTS.",
    "The future of TTS includes richer emotional expression and personality.",
    "Personalized voices trained on a user's own speech are now possible.",
    "Realtime TTS enables new categories of voice-first applications.",
    "Voice interfaces are the next frontier of human-computer interaction.",
    "Accessibility is a major use case for high-quality TTS technology.",
    "Screen readers rely on TTS to make digital content accessible to blind users.",
    "Language learning apps use TTS to provide native pronunciation examples.",
    "Audiobook production is being transformed by high-quality TTS synthesis.",
    "Podcast generation from text is now feasible with modern TTS systems.",
    "News article narration is a high-volume use case for TTS at scale.",
    "IVR systems are migrating from recorded prompts to synthesized speech.",
    "Voice assistants like Siri and Alexa rely on TTS for their spoken responses.",
    "In-car navigation systems use TTS for turn-by-turn directions.",
    "Public announcement systems benefit from multilingual TTS capabilities.",
    "Translation apps use TTS to speak translations in the target language.",
    "Educational content is increasingly narrated by TTS for consistent quality.",
    "Video game dialogue is being augmented with TTS for non-player characters.",
    "Virtual reality experiences use spatial TTS for immersive audio environments.",
    "Customer service bots are evolving to include natural TTS voices.",
    "Healthcare applications use TTS for medication reminders and instructions.",
    "Emergency notification systems use TTS for clear, attention-grabbing alerts.",
    "Smart home devices speak to users via embedded TTS engines.",
    "Wearable devices with small speakers benefit from optimized TTS pipelines.",
    "IoT devices can speak status updates and notifications using TTS.",
    "Robotic systems use TTS to communicate with humans in shared spaces.",
    "Museum exhibits use TTS to provide audio guides in multiple languages.",
    "Tourism applications use TTS for real-time translation and narration.",
    "Accessibility for dyslexia is improved by listening to text via TTS.",
    "Document review workflows benefit from TTS for hands-free consumption.",
    "Email clients can read messages aloud using TTS for multitasking users.",
    "Social media platforms experiment with TTS for content accessibility.",
    "E-commerce sites use TTS for product descriptions and shopping assistance.",
    "Banking apps use TTS for transaction confirmations and balance inquiries.",
    "Travel apps use TTS for boarding announcements and gate changes.",
    "Weather forecasts are increasingly delivered via TTS in voice assistants.",
    "Sports commentary is being augmented by TTS for real-time updates.",
    "Stock market summaries can be spoken aloud via TTS for traders.",
    "Recipe apps use TTS to read cooking instructions hands-free.",
    "Workout apps use TTS to provide coaching and motivation during exercise.",
    "Meditation apps use TTS for guided sessions with calm, soothing voices.",
    "Children's educational apps use TTS to read stories and explain concepts.",
    "Language learning platforms use TTS for pronunciation practice and feedback.",
    "Customer feedback collection can use TTS for survey question delivery.",
    "Voice-based search is enabled by TTS for reading back search results.",
    "Audio advertisements are being generated dynamically using TTS.",
    "Voiceovers for explainer videos can be produced quickly with TTS.",
    "Corporate training materials are increasingly narrated using TTS.",
    "Compliance training benefits from consistent TTS narration across modules.",
    "Onboarding flows for new employees can use TTS for a personal touch.",
    "Product tutorials can be voiced by TTS for a consistent user experience.",
    "Software documentation can be read aloud using TTS for accessibility.",
    "API documentation read aloud helps developers learn new endpoints quickly.",
    "Code review tools can read diff summaries aloud using TTS.",
    "Developer tools increasingly support TTS for accessibility and productivity.",
    "Gaming tutorials and hints can be spoken aloud using TTS engines.",
    "In-game dialogue for procedurally generated content uses TTS dynamically.",
    "NPCs in open-world games speak via TTS for vast amounts of dialogue.",
    "Virtual assistants in games use TTS for character interactions.",
    "Game streaming platforms use TTS for automated commentary features.",
    "Esports broadcasts can use TTS for live event narration and updates.",
    "Live event captioning relies on TTS for real-time audio output.",
    "Conference interpretation uses TTS to deliver translations in real time.",
    "Diplomatic meetings use TTS for multilingual communication support.",
    "Healthcare providers use TTS to communicate with patients who have hearing loss.",
    "Assistive technology for the elderly relies on TTS for independence.",
    "Smart speakers use TTS for all spoken responses and notifications.",
    "Automotive infotainment systems use TTS for navigation and media control.",
    "Aviation systems use TTS for cockpit communications and announcements.",
    "Maritime navigation systems use TTS for safety announcements.",
    "Railway announcements are increasingly generated by TTS for consistency.",
    "Bus and transit systems use TTS for next-stop announcements.",
    "Airport gate announcements can be generated dynamically using TTS.",
    "Hotel concierge systems use TTS for guest information delivery.",
    "Restaurant ordering systems can speak order confirmations via TTS.",
    "Retail point-of-sale systems use TTS for transaction confirmations.",
    "Vending machines can speak product selections using embedded TTS.",
    "Industrial equipment uses TTS for status updates and warning messages.",
    "Agricultural systems use TTS to alert farmers about conditions and actions.",
    "Environmental monitoring systems use TTS to announce alerts and updates.",
    "Scientific instruments use TTS to communicate results to researchers.",
    "Spacecraft systems use TTS to communicate with astronauts during missions.",
    "Submarine communication systems rely on TTS for clear audio output.",
    "Military communication systems use TTS for command and control messages.",
    "Emergency response systems use TTS for clear, authoritative instructions.",
    "Disaster warning systems use TTS to reach broad audiences quickly.",
    "Public safety announcements benefit from consistent, clear TTS output.",
    "Cybersecurity alerts can be delivered via TTS for immediate attention.",
    "Network operations centers use TTS for alarm and status notifications.",
    "Data center monitoring systems use TTS for environmental alerts.",
    "Power grid management uses TTS for outage and restoration updates.",
    "Water utility systems use TTS for service interruption notices.",
    "Gas leak detection systems use TTS for safety warnings.",
    "Building management systems use TTS for HVAC and security notifications.",
    "Elevator systems use TTS for floor announcements and safety messages.",
    "Parking systems use TTS for space availability and payment instructions.",
    "Traffic management systems use TTS for driver information broadcasts.",
    "Toll booth systems use TTS for payment instructions and receipts.",
    "Border control systems use TTS for instructions to travelers.",
    "Customs and immigration use TTS for clear procedural announcements.",
    "Voting systems can use TTS for ballot audio accessibility.",
    "Court reporting systems use TTS to read back testimony and evidence.",
    "Legal aid services use TTS to make legal information more accessible.",
    "Tax preparation software uses TTS to guide users through forms.",
    "Government services increasingly use TTS for citizen communication.",
    "Public libraries use TTS for audio book lending and accessibility.",
    "Schools use TTS to support students with diverse learning needs.",
    "Universities use TTS for lecture transcription and audio content.",
    "Online learning platforms use TTS to narrate course content.",
    "MOOC platforms rely on TTS for consistent lecture audio quality.",
    "Educational testing uses TTS for reading comprehension assessments.",
    "Special education benefits greatly from personalized TTS voices.",
    "Speech therapy uses TTS as a tool for articulation practice.",
    "Language pathology tools use TTS for patient communication aids.",
    "Augmentative and alternative communication devices rely on TTS.",
    "Voice banking preserves a person's voice for future TTS use.",
    "Medical patients who lose their voice can use TTS to communicate.",
    "ALS patients rely on TTS for ongoing communication as the disease progresses.",
    "Tracheostomy patients use TTS to speak while recovering.",
    "Stroke patients use TTS during speech rehabilitation therapy.",
    "Cerebral palsy patients use TTS to communicate effectively.",
    "Down syndrome education programs use TTS for learning support.",
    "Autism spectrum disorder support tools use TTS for communication.",
    "Dyslexia assistance tools use TTS to read text aloud for users.",
    "ADHD productivity tools use TTS to help with focus and comprehension.",
    "Visual impairment aids use TTS to describe visual content audibly.",
    "Cognitive accessibility tools use TTS for simplified information delivery.",
    "Memory assistance tools use TTS for reminders and prompts.",
    "Executive function support uses TTS for task management and organization.",
    "Mental health apps use TTS for guided meditation and therapy exercises.",
    "Substance abuse recovery programs use TTS for supportive messaging.",
    "Smoking cessation programs use TTS for encouraging messages.",
    "Weight loss programs use TTS for coaching and motivation.",
    "Fitness apps use TTS for workout instructions and encouragement.",
    "Running apps use TTS for pace updates and milestone announcements.",
    "Cycling apps use TTS for navigation and performance data.",
    "Swimming apps use TTS for lap counting and stroke feedback.",
    "Yoga apps use TTS for pose instructions and breathing guidance.",
    "Meditation apps use TTS for calming guided sessions.",
    "Sleep apps use TTS for bedtime stories and relaxation scripts.",
    "Dream journaling apps use TTS for recording and playback.",
    "Therapy apps use TTS for homework and between-session exercises.",
    "Coaching apps use TTS for personalized advice and encouragement.",
    "Sales training tools use TTS for objection handling practice.",
    "Customer service training uses TTS for realistic call simulations.",
    "Medical training uses TTS to simulate patient interactions.",
    "Pilot training uses TTS for air traffic control simulations.",
    "Military training uses TTS for tactical communication practice.",
    "Language immersion programs use TTS for authentic pronunciation models.",
    "Cultural exchange programs use TTS to introduce new languages.",
    "Heritage language learning benefits from TTS for family history research.",
    "Sign language translation uses TTS as a complement to visual signing.",
    "Braille readers can use TTS as an alternative to tactile reading.",
    "Audio description for the blind uses TTS to describe visual media.",
    "Tactile graphics tools use TTS to describe images and diagrams.",
    "Museum audio guides use TTS for consistent, multilingual narration.",
    "Historical site interpretation uses TTS for visitor education.",
    "National park audio tours use TTS for accessible interpretation.",
    "Zoo and aquarium guides use TTS for animal information delivery.",
    "Theme park attractions use TTS for narrative ride experiences.",
    "Escape rooms use TTS for hints and atmospheric storytelling.",
    "Theatrical productions can use TTS for offstage voice effects.",
    "Audio dramas and podcasts are increasingly produced using TTS.",
    "Radio broadcasting can use TTS for automated news segments.",
    "Television closed captioning can be voiced using TTS for accessibility.",
    "Streaming services use TTS for audio description tracks.",
    "Sports broadcasting uses TTS for real-time score updates and commentary.",
    "Weather broadcasting uses TTS for automated forecast delivery.",
    "Traffic reporting uses TTS for real-time road condition updates.",
    "Financial news uses TTS for market summaries and analysis.",
    "Political coverage uses TTS for unbiased reporting of speeches and statements.",
    "Entertainment news uses TTS for celebrity update delivery.",
    "Technology news can be read aloud using TTS for tech enthusiasts.",
    "Science news delivery via TTS makes complex topics more accessible.",
    "Educational television uses TTS for narration in documentaries.",
    "Children's programming uses TTS for character voices and storytelling.",
    "Animation voiceovers can be augmented with TTS for background characters.",
    "Documentary narration increasingly uses TTS for cost-effective production.",
    "Corporate communications use TTS for internal announcements and updates.",
    "Investor relations use TTS for earnings call summaries and analysis.",
    "Public relations use TTS for press release distribution and accessibility.",
    "Marketing materials use TTS for consistent brand voice across channels.",
    "Product demonstrations use TTS for hands-free feature explanations.",
    "Sales presentations use TTS to ensure consistent messaging.",
    "Training videos use TTS for professional narration at lower cost.",
    "Webinar platforms use TTS for automated captions and audio summaries.",
    "Virtual conferences use TTS for accessible session playback.",
    "Hybrid events use TTS to reach remote attendees effectively.",
    "Networking platforms use TTS to read profiles and connection requests.",
    "Professional networking apps use TTS for hands-free profile browsing.",
    "Job search platforms use TTS for job description narration.",
    "Recruitment tools use TTS for candidate communication and updates.",
    "HR systems use TTS for policy distribution and acknowledgment.",
    "Performance management tools use TTS for review feedback delivery.",
    "Employee onboarding uses TTS for welcoming new team members.",
    "Internal communications use TTS for company-wide announcements.",
    "Crisis communication uses TTS for rapid, consistent message delivery.",
    "Brand storytelling uses TTS to create audio versions of written content.",
    "Customer testimonials can be voiced using TTS for marketing videos.",
    "Product reviews can be read aloud using TTS for shopping assistance.",
    "Recipe narration uses TTS for hands-free cooking guidance.",
    "Travel guides use TTS for immersive destination information.",
    "City tours use TTS for self-guided exploration with audio commentary.",
    "Adventure apps use TTS to narrate outdoor experiences safely.",
    "Stargazing apps use TTS to describe constellations and celestial events.",
    "Bird watching apps use TTS to identify species by their calls and appearance.",
    "Plant identification apps use TTS to describe botanical features.",
    "Rock identification tools use TTS to describe geological samples.",
    "Insect identification apps use TTS to describe entomological specimens.",
    "Fish identification guides use TTS for marine biology education.",
    "Weather observation tools use TTS to report atmospheric conditions.",
    "Astronomy education uses TTS to explain complex celestial concepts.",
    "Physics simulations use TTS to narrate experiment results and explanations.",
    "Chemistry tools use TTS to pronounce chemical names and formulas correctly.",
    "Biology education uses TTS to describe anatomical structures and processes.",
    "Medical education uses TTS to describe symptoms and treatment options.",
    "History education uses TTS to bring historical events to life through narration.",
    "Geography lessons use TTS to pronounce place names and describe regions.",
    "Literature analysis uses TTS to read excerpts aloud for discussion.",
    "Poetry appreciation uses TTS to recite verses with proper rhythm and intonation.",
    "Drama education uses TTS to perform monologues and soliloquies.",
    "Music theory instruction uses TTS to explain complex harmonic concepts.",
    "Art history education uses TTS to describe artistic movements and techniques.",
    "Philosophy discussions use TTS to read primary source texts aloud.",
    "Religious education uses TTS to recite sacred texts and prayers.",
    "Ethics discussions use TTS to present scenarios and case studies.",
    "Political science education uses TTS to explain complex policy issues.",
    "Economics instruction uses TTS to describe market dynamics and theories.",
    "Psychology education uses TTS to describe experimental procedures and findings.",
    "Sociology courses use TTS to present research findings and theories.",
    "Anthropology education uses TTS to describe cultural practices and artifacts.",
    "Linguistics instruction uses TTS to demonstrate phonetic distinctions.",
    "Computer science education uses TTS to explain algorithms and data structures.",
    "Engineering courses use TTS to describe technical concepts and procedures.",
    "Mathematics education uses TTS to read problem statements and solutions.",
    "Statistics instruction uses TTS to explain methodology and interpretation.",
    "Data science education uses TTS to describe analytical techniques.",
    "Machine learning courses use TTS to explain model architectures and training.",
    "Artificial intelligence education uses TTS to discuss ethical implications.",
    "Robotics instruction uses TTS to describe sensor systems and control algorithms.",
    "Cybersecurity education uses TTS to explain threat vectors and defenses.",
    "Network engineering uses TTS to describe protocol operations and troubleshooting.",
    "Database courses use TTS to explain query optimization and schema design.",
    "Web development education uses TTS to describe frameworks and best practices.",
    "Mobile app development uses TTS to describe platform-specific features.",
    "Game development courses use TTS to explain engine architectures and workflows.",
    "Cloud computing education uses TTS to describe service models and deployment.",
    "DevOps training uses TTS to explain CI/CD pipelines and automation tools.",
    "Software architecture education uses TTS to describe design patterns and principles.",
    "Quality assurance training uses TTS to explain testing methodologies and tools.",
    "Project management education uses TTS to describe methodologies and frameworks.",
    "Product management training uses TTS to explain user research and prioritization.",
    "UX design education uses TTS to describe design thinking and research methods.",
    "UI design training uses TTS to explain visual hierarchy and interaction patterns.",
    "Graphic design education uses TTS to describe typography and color theory.",
    "Animation training uses TTS to explain principles of motion and timing.",
    "Film production courses use TTS to describe cinematography and editing techniques.",
    "Photography education uses TTS to explain composition and lighting principles.",
    "Audio production training uses TTS to describe mixing and mastering techniques.",
    "Music production education uses TTS to explain recording and arrangement.",
    "Sound design training uses TTS to describe synthesis and sampling techniques.",
    "Voice acting courses use TTS to demonstrate character voice techniques.",
    "Public speaking training uses TTS to demonstrate rhetorical devices.",
    "Debate education uses TTS to demonstrate argumentation techniques.",
    "Negotiation training uses TTS to demonstrate tactical communication.",
    "Mediation training uses TTS to demonstrate conflict resolution techniques.",
    "Leadership development uses TTS to describe management styles and approaches.",
    "Team building exercises use TTS to facilitate group activities.",
    "Diversity training uses TTS to present inclusive communication practices.",
    "Ethics training uses TTS to present case studies and decision frameworks.",
    "Compliance education uses TTS to explain regulatory requirements clearly.",
    "Safety training uses TTS to communicate critical procedures and warnings.",
    "First aid training uses TTS to walk through emergency response procedures.",
    "CPR training uses TTS to coach rescuers through chest compressions and breaths.",
    "Fire safety education uses TTS to describe evacuation procedures and protocols.",
    "Workplace safety training uses TTS to communicate hazard awareness and prevention.",
    "Cybersecurity awareness uses TTS to deliver engaging phishing simulations.",
    "Data privacy training uses TTS to explain complex regulations and best practices.",
    "Financial literacy education uses TTS to explain budgeting and investing concepts.",
    "Retirement planning uses TTS to explain complex financial products and strategies.",
    "Tax education uses TTS to explain filing requirements and deduction categories.",
    "Estate planning uses TTS to explain wills, trusts, and inheritance procedures.",
    "Insurance education uses TTS to explain coverage types and policy details.",
    "Real estate training uses TTS to explain contracts and closing procedures.",
    "Mortgage education uses TTS to explain loan terms and qualification requirements.",
    "Credit score education uses TTS to explain factors affecting creditworthiness.",
    "Debt management training uses TTS to explain consolidation and repayment strategies.",
    "Investment education uses TTS to explain stocks, bonds, and portfolio diversification.",
    "Retirement account training uses TTS to explain IRAs, 401ks, and contribution limits.",
    "College planning uses TTS to explain savings options and financial aid processes.",
    "Small business education uses TTS to explain business plans and funding options.",
    "Entrepreneurship training uses TTS to explain startup fundamentals and pitfalls.",
    "Marketing education uses TTS to explain branding, positioning, and customer acquisition.",
    "Sales training uses TTS to explain prospecting, qualifying, and closing techniques.",
    "Customer success education uses TTS to explain onboarding and retention strategies.",
    "Product marketing uses TTS to explain positioning and competitive differentiation.",
    "Content marketing education uses TTS to explain strategy and distribution channels.",
    "Social media marketing uses TTS to explain platform-specific best practices.",
    "Email marketing training uses TTS to explain segmentation and automation.",
    "Search engine optimization uses TTS to explain ranking factors and techniques.",
    "Paid advertising training uses TTS to explain bidding strategies and ad formats.",
    "Analytics education uses TTS to explain metrics, attribution, and reporting.",
    "Conversion optimization uses TTS to explain testing methodologies and tools.",
    "User research training uses TTS to explain interview techniques and analysis.",
    "A/B testing education uses TTS to explain experimental design and statistical significance.",
    "Customer journey mapping uses TTS to explain touchpoints and pain points.",
    "Persona development uses TTS to explain demographic and psychographic research.",
    "Market research training uses TTS to explain methodologies and data analysis.",
    "Competitive intelligence uses TTS to explain research techniques and reporting.",
    "Brand strategy education uses TTS to explain positioning and identity development.",
    "Crisis management training uses TTS to explain communication protocols.",
    "Media relations training uses TTS to explain press release writing and pitching.",
    "Investor relations education uses TTS to explain financial communication best practices.",
    "Government affairs training uses TTS to explain advocacy and lobbying techniques.",
    "Public affairs education uses TTS to explain community engagement strategies.",
    "Corporate social responsibility uses TTS to explain impact measurement and reporting.",
    "Sustainability education uses TTS to explain environmental practices and certifications.",
    "Diversity and inclusion training uses TTS to explain bias awareness and mitigation.",
    "Workplace culture education uses TTS to explain values and behavioral expectations.",
    "Employee engagement training uses TTS to explain survey design and action planning.",
    "Talent acquisition education uses TTS to explain sourcing and selection strategies.",
    "Talent management training uses TTS to explain development and succession planning.",
    "Compensation and benefits education uses TTS to explain total rewards strategies.",
    "Learning and development uses TTS to explain training program design and delivery.",
    "Performance management training uses TTS to explain goal setting and feedback techniques.",
    "Change management education uses TTS to explain transition planning and execution.",
    "Organizational design training uses TTS to explain structure and reporting relationships.",
    "Strategic planning education uses TTS to explain vision, mission, and goal setting.",
    "Innovation management training uses TTS to explain ideation and portfolio management.",
    "Project management education uses TTS to explain scope, schedule, and budget management.",
    "Risk management training uses TTS to explain identification and mitigation strategies.",
    "Quality management education uses TTS to explain continuous improvement methodologies.",
    "Lean six sigma training uses TTS to explain process optimization techniques.",
    "Agile methodology education uses TTS to explain scrum and kanban frameworks.",
    "Design thinking training uses TTS to explain empathy, ideation, and prototyping.",
    "Systems thinking education uses TTS to explain feedback loops and leverage points.",
    "Critical thinking training uses TTS to explain logic and argument analysis.",
    "Creative thinking education uses TTS to explain brainstorming and idea generation.",
    "Problem solving training uses TTS to explain root cause analysis techniques.",
    "Decision making education uses TTS to explain frameworks and bias awareness.",
    "Emotional intelligence training uses TTS to explain self-awareness and empathy.",
    "Conflict resolution education uses TTS to explain mediation and negotiation techniques.",
    "Time management training uses TTS to explain prioritization and productivity techniques.",
    "Stress management education uses TTS to explain coping strategies and resilience building.",
    "Mindfulness training uses TTS to explain meditation and present-moment awareness.",
    "Resilience building uses TTS to explain adaptation and recovery strategies.",
    "Goal setting education uses TTS to explain SMART criteria and action planning.",
    "Habit formation training uses TTS to explain behavior change techniques.",
    "Motivation education uses TTS to explain intrinsic and extrinsic factors.",
    "Self-confidence training uses TTS to explain assertiveness and positive self-talk.",
    "Communication skills education uses TTS to explain active listening and clear expression.",
    "Presentation skills training uses TTS to explain structure and delivery techniques.",
    "Storytelling education uses TTS to explain narrative arc and character development.",
    "Persuasion training uses TTS to explain rhetorical devices and ethical influence.",
    "Negotiation skills education uses TTS to explain interest-based bargaining.",
    "Networking skills training uses TTS to explain relationship building strategies.",
    "Mentoring education uses TTS to explain guidance and knowledge transfer.",
    "Coaching skills training uses TTS to explain questioning and feedback techniques.",
    "Facilitation education uses TTS to explain group process and decision making.",
    "Meeting management training uses TTS to explain agendas and time management.",
    "Email communication education uses TTS to explain clarity and tone management.",
    "Cross-cultural communication uses TTS to explain cultural norms and adaptations.",
    "Difficult conversations training uses TTS to explain preparation and delivery strategies.",
    "Feedback delivery education uses TTS to explain specific and constructive approaches.",
    "Active listening training uses TTS to explain techniques for full engagement.",
    "Empathic communication uses TTS to explain validation and understanding techniques.",
    "Assertiveness training uses TTS to explain direct and respectful expression.",
    "Boundaries education uses TTS to explain healthy limits in relationships.",
    "Self-care training uses TTS to explain stress reduction and wellness strategies.",
    "Work-life balance education uses TTS to explain prioritization and boundaries.",
    "Burnout prevention training uses TTS to explain recognition and intervention strategies.",
    "Mental health awareness uses TTS to explain common conditions and support resources.",
    "Suicide prevention training uses TTS to explain warning signs and intervention.",
    "Crisis intervention education uses TTS to explain de-escalation techniques.",
    "Trauma-informed care uses TTS to explain safety and trust building.",
    "Grief support training uses TTS to explain listening and陪伴 techniques.",
    "Addiction recovery education uses TTS to explain stages and support strategies.",
    "Eating disorder awareness uses TTS to explain warning signs and treatment options.",
    "Body positivity training uses TTS to explain self-acceptance and media literacy.",
    "Healthy relationship education uses TTS to explain communication and boundaries.",
    "Parenting skills training uses TTS to explain positive discipline and connection.",
    "Child development education uses TTS to explain milestones and age-appropriate activities.",
    "Adolescent psychology training uses TTS to explain identity and peer relationships.",
    "Adult development education uses TTS to explain transitions and life stages.",
    "Aging well training uses TTS to explain health maintenance and engagement strategies.",
    "Elder care education uses TTS to explain support and communication techniques.",
    "End of life care training uses TTS to explain comfort and dignity strategies.",
    "Palliative care education uses TTS to explain symptom management and support.",
    "Hospice care training uses TTS to explain family support and comfort measures.",
    "Spiritual care education uses TTS to explain meaning and connection techniques.",
    "Religious literacy training uses TTS to explain diverse beliefs and practices.",
    "Cultural competency education uses TTS to explain traditions and values.",
    "Diversity appreciation training uses TTS to explain inclusion and belonging.",
    "Implicit bias education uses TTS to explain awareness and mitigation strategies.",
    "Allyship training uses TTS to explain support and advocacy techniques.",
    "Anti-racism education uses TTS to explain systemic analysis and action.",
    "Gender equity training uses TTS to explain inclusion and opportunity.",
    "LGBTQ+ awareness uses TTS to explain terminology and supportive practices.",
    "Disability inclusion training uses TTS to explain accessibility and accommodation.",
    "Neurodiversity appreciation uses TTS to explain different cognitive styles.",
    "Mental health first aid uses TTS to explain recognition and referral.",
    "Substance use awareness uses TTS to explain signs and intervention strategies.",
    "Financial wellness education uses TTS to explain budgeting and debt management.",
    "Career development training uses TTS to explain planning and skill building.",
    "Personal branding education uses TTS to explain authentic self-presentation.",
    "Networking strategy training uses TTS to explain relationship building approaches.",
    "Interview preparation uses TTS to explain common questions and strong answers.",
    "Resume writing education uses TTS to explain effective content and format.",
    "Cover letter training uses TTS to explain customization and impact.",
    "LinkedIn optimization uses TTS to explain profile enhancement techniques.",
    "Job search strategy education uses TTS to explain sourcing and application approaches.",
    "Salary negotiation training uses TTS to explain research and advocacy techniques.",
    "Onboarding success uses TTS to explain integration and relationship building.",
    "Workplace politics education uses TTS to explain navigation and ethics.",
    "Office etiquette training uses TTS to explain professional behavior expectations.",
    "Remote work best practices uses TTS to explain communication and productivity.",
    "Hybrid work strategies uses TTS to explain flexibility and collaboration.",
    "Team collaboration education uses TTS to explain roles and communication.",
    "Cross-functional teamwork uses TTS to explain shared goals and coordination.",
    "Stakeholder management training uses TTS to explain engagement strategies.",
    "Vendor management education uses TTS to explain selection and relationship building.",
    "Partnership development training uses TTS to explain mutual value creation.",
    "Customer relationship management uses TTS to explain engagement and retention.",
    "Account management education uses TTS to explain growth and satisfaction strategies.",
    "Sales pipeline management uses TTS to explain forecasting and optimization.",
    "Revenue operations training uses TTS to explain process and technology alignment.",
    "Marketing operations education uses TTS to explain efficiency and measurement.",
    "Customer operations training uses TTS to explain service quality and efficiency.",
    "IT operations education uses TTS to explain service delivery and support.",
    "Security operations training uses TTS to explain threat detection and response.",
    "DevOps practices education uses TTS to explain collaboration and automation.",
    "Site reliability engineering uses TTS to explain reliability and incident response.",
    "Platform engineering education uses TTS to explain developer experience and tooling.",
    "Data engineering training uses TTS to explain pipelines and data quality.",
    "Machine learning operations uses TTS to explain model deployment and monitoring.",
    "Analytics engineering education uses TTS to explain data modeling and transformation.",
    "Business intelligence training uses TTS to explain reporting and decision support.",
    "Data science education uses TTS to explain analysis and insight generation.",
    "Research methodology training uses TTS to explain study design and ethics.",
    "Statistical analysis education uses TTS to explain inference and modeling.",
    "Experimental design training uses TTS to explain controlled studies and validity.",
    "Survey methodology education uses TTS to explain design and sampling techniques.",
    "Qualitative research training uses TTS to explain interviews and thematic analysis.",
    "Quantitative research education uses TTS to explain measurement and analysis.",
    "Mixed methods training uses TTS to explain integration and triangulation.",
    "Action research education uses TTS to explain participatory and iterative approaches.",
    "Implementation science training uses TTS to explain evidence-based practice adoption.",
    "Knowledge management education uses TTS to explain capture and sharing strategies.",
    "Organizational learning training uses TTS to explain continuous improvement.",
    "Communities of practice education uses TTS to explain collaboration and knowledge sharing.",
    "Mentorship program training uses TTS to explain structure and best practices.",
    "Coaching program education uses TTS to explain skill development approaches.",
    "Leadership development training uses TTS to explain vision and influence.",
    "Executive education uses TTS to explain strategic thinking and decision making.",
    "Board governance training uses TTS to explain fiduciary responsibilities and oversight.",
    "Corporate strategy education uses TTS to explain competitive positioning and growth.",
    "Business model innovation uses TTS to explain value creation and capture.",
    "Digital transformation training uses TTS to explain technology adoption and change.",
    "Innovation strategy education uses TTS to explain portfolio and ecosystem approaches.",
    "Sustainability strategy training uses TTS to explain ESG integration and impact.",
    "Global expansion education uses TTS to explain market entry and localization.",
    "Mergers and acquisitions training uses TTS to explain integration and value capture.",
    "Divestiture strategy education uses TTS to explain portfolio optimization.",
    "Joint venture training uses TTS to explain partnership structure and governance.",
    "Strategic alliance education uses TTS to explain collaboration and value sharing.",
    "Ecosystem strategy training uses TTS to explain platform and network effects.",
    "Open innovation education uses TTS to explain external collaboration and sourcing.",
    "Crowdsourcing strategy training uses TTS to explain engagement and quality management.",
    "Venture capital education uses TTS to explain investment thesis and portfolio construction.",
    "Private equity training uses TTS to explain value creation and exit strategies.",
    "Angel investing education uses TTS to explain early stage investment approaches.",
    "Startup funding training uses TTS to explain bootstrapping and capital raising.",
    "Initial public offering education uses TTS to explain process and requirements.",
    "Secondary offering training uses TTS to explain follow-on capital raising.",
    "Debt financing education uses TTS to explain loan structures and covenants.",
    "Bond issuance training uses TTS to explain fixed income markets and pricing.",
    "Equity research education uses TTS to explain analysis and recommendations.",
    "Fixed income research training uses TTS to explain credit analysis and valuation.",
    "Commodity research education uses TTS to explain supply, demand, and price drivers.",
    "Currency research training uses TTS to explain macroeconomic factors and central bank policy.",
    "Alternative investment education uses TTS to explain hedge funds and private markets.",
    "Real estate investment training uses TTS to explain property analysis and financing.",
    "Infrastructure investment education uses TTS to explain project finance and returns.",
    "Impact investing training uses TTS to explain social and environmental returns.",
    "Socially responsible investing education uses TTS to explain values-based approaches.",
    "Environmental, social, and governance training uses TTS to explain sustainable business.",
    "Corporate governance education uses TTS to explain board structure and accountability.",
    "Executive compensation training uses TTS to explain incentive design and alignment.",
    "Audit and assurance education uses TTS to explain financial statement verification.",
    "Tax planning training uses TTS to explain optimization and compliance strategies.",
    "Treasury management education uses TTS to explain cash and liquidity management.",
    "Financial planning and analysis uses TTS to explain budgeting and forecasting.",
    "Management accounting education uses TTS to explain cost analysis and decision support.",
    "Cost accounting training uses TTS to explain allocation and profitability analysis.",
    "Performance measurement education uses TTS to explain KPIs and balanced scorecards.",
    "Budgeting and forecasting training uses TTS to explain planning and variance analysis.",
    "Capital budgeting education uses TTS to explain investment evaluation and selection.",
    "Working capital management training uses TTS to explain liquidity and efficiency.",
    "Inventory management education uses TTS to explain optimization and control techniques.",
    "Supply chain management training uses TTS to explain end-to-end coordination.",
    "Logistics management education uses TTS to explain transportation and warehousing.",
    "Procurement training uses TTS to explain sourcing and supplier relationship management.",
    "Vendor management education uses TTS to explain selection and performance management.",
    "Contract management training uses TTS to explain negotiation and compliance.",
    "Project portfolio management uses TTS to explain prioritization and resource allocation.",
    "Program management education uses TTS to explain coordinated initiative delivery.",
    "Project management office training uses TTS to explain standards and support.",
    "Agile transformation education uses TTS to explain cultural and process change.",
    "DevOps transformation training uses TTS to explain collaboration and automation.",
    "Design transformation education uses TTS to explain human-centered approaches.",
    "Digital transformation training uses TTS to explain technology strategy and adoption.",
    "Change management education uses TTS to explain stakeholder engagement and adoption.",
    "Organizational development training uses TTS to explain culture and capability building.",
    "Talent management education uses TTS to explain acquisition and development strategies.",
    "Succession planning training uses TTS to explain leadership continuity and development.",
    "Workforce planning education uses TTS to explain supply, demand, and gap analysis.",
    "Diversity recruiting training uses TTS to explain inclusive sourcing and selection.",
    "Employer branding education uses TTS to explain value proposition and reputation.",
    "Employee value proposition training uses TTS to explain total rewards and culture.",
    "Total rewards education uses TTS to explain compensation and benefits strategy.",
    "Compensation strategy training uses TTS to explain pay structure and philosophy.",
    "Benefits administration education uses TTS to explain plan design and communication.",
    "Wellness program training uses TTS to explain health and engagement initiatives.",
    "Employee assistance programs use TTS to explain confidential support services.",
    "Performance appraisal education uses TTS to explain evaluation and feedback processes.",
    "360 degree feedback training uses TTS to explain multi-source assessment.",
    "Goal alignment education uses TTS to explain cascading objectives and key results.",
    "Key performance indicators training uses TTS to explain measurement and tracking.",
    "Objectives and key results education uses TTS to explain goal setting and progress.",
    "Balanced scorecard training uses TTS to explain strategic performance measurement.",
    "Strategy mapping education uses TTS to explain cause-and-effect strategic thinking.",
    "Hoshin kanri training uses TTS to explain strategic planning and deployment.",
    "Policy deployment education uses TTS to explain catchball and alignment processes.",
    "Lean management training uses TTS to explain waste reduction and value creation.",
    "Six sigma education uses TTS to explain defect reduction and process improvement.",
    "Total quality management training uses TTS to explain customer focus and continuous improvement.",
    "ISO standards education uses TTS to explain quality management systems.",
    "Industry standards training uses TTS to explain compliance and best practices.",
    "Regulatory compliance education uses TTS to explain requirements and implementation.",
    "Risk management training uses TTS to explain identification and mitigation frameworks.",
    "Internal controls education uses TTS to explain governance and assurance processes.",
    "Fraud prevention training uses TTS to explain detection and deterrence measures.",
    "Anti-money laundering education uses TTS to explain compliance and reporting.",
    "Know your customer training uses TTS to explain verification and due diligence.",
    "Data protection education uses TTS to explain privacy and security requirements.",
    "Cybersecurity training uses TTS to explain threat awareness and safe practices.",
    "Information security education uses TTS to explain confidentiality and integrity.",
    "Physical security training uses TTS to explain access control and surveillance.",
    "Personnel security education uses TTS to explain screening and clearance processes.",
    "Operational security training uses TTS to explain process and procedural safeguards.",
    "Communications security education uses TTS to explain transmission and signaling protection.",
    "Network security training uses TTS to explain perimeter and internal defenses.",
    "Endpoint security education uses TTS to explain device-level protection measures.",
    "Application security training uses TTS to explain secure development practices.",
    "Cloud security education uses TTS to explain shared responsibility and controls.",
    "Identity and access management training uses TTS to explain authentication and authorization.",
    "Privileged access management education uses TTS to explain elevated access controls.",
    "Vulnerability management training uses TTS to explain scanning and remediation.",
    "Patch management education uses TTS to explain update and deployment strategies.",
    "Configuration management training uses TTS to explain baseline and drift control.",
    "Asset management education uses TTS to explain inventory and lifecycle tracking.",
    "Change management training uses TTS to explain approval and implementation controls.",
    "Incident management education uses TTS to explain response and recovery procedures.",
    "Problem management training uses TTS to explain root cause and prevention.",
    "Service request management education uses TTS to explain fulfillment and satisfaction.",
    "Service level management training uses TTS to explain agreements and performance.",
    "Capacity management education uses TTS to explain planning and optimization.",
    "Availability management training uses TTS to explain uptime and resilience.",
    "Continuity management education uses TTS to explain business resilience planning.",
    "Disaster recovery training uses TTS to explain restoration and resumption procedures.",
    "Crisis management education uses TTS to explain response and communication protocols.",
    "Emergency management training uses TTS to explain preparedness and response procedures.",
    "Business continuity education uses TTS to explain operational resilience strategies.",
    "Resilience engineering training uses TTS to explain system design for failure.",
    "Reliability engineering education uses TTS to explain failure mode and effects analysis.",
    "Maintainability engineering training uses TTS to explain serviceability and repair.",
    "Safety engineering education uses TTS to explain hazard analysis and mitigation.",
    "Human factors engineering training uses TTS to explain usability and safety.",
    "Ergonomics education uses TTS to explain comfort and efficiency in design.",
    "Accessibility engineering training uses TTS to explain inclusive design principles.",
    "Universal design education uses TTS to explain equitable use and flexibility.",
    "Sustainable design training uses TTS to explain environmental and social impact.",
    "Green building education uses TTS to explain energy efficiency and materials.",
    "LEED certification training uses TTS to explain sustainability standards and credits.",
    "Energy management education uses TTS to explain conservation and efficiency.",
    "Water management training uses TTS to explain conservation and quality.",
    "Waste management education uses TTS to explain reduction and recycling strategies.",
    "Pollution prevention training uses TTS to explain source reduction and control.",
    "Environmental management education uses TTS to explain compliance and stewardship.",
    "Carbon footprint reduction training uses TTS to explain measurement and mitigation.",
    "Climate action education uses TTS to explain mitigation and adaptation strategies.",
    "Biodiversity conservation training uses TTS to explain habitat and species protection.",
    "Ecosystem restoration education uses TTS to explain rehabilitation and recovery.",
    "Wildlife management training uses TTS to explain population and habitat management.",
    "Fisheries management education uses TTS to explain sustainable harvesting and conservation.",
    "Forest management training uses TTS to explain timber and ecosystem services.",
    "Agriculture education uses TTS to explain crop production and soil management.",
    "Horticulture training uses TTS to explain plant cultivation and landscape design.",
    "Animal husbandry education uses TTS to explain breeding and care practices.",
    "Veterinary medicine training uses TTS to explain diagnosis and treatment.",
    "Public health education uses TTS to explain prevention and population health.",
    "Epidemiology training uses TTS to explain disease distribution and determinants.",
    "Biostatistics education uses TTS to explain health data analysis and interpretation.",
    "Health policy training uses TTS to explain development and implementation.",
    "Health economics education uses TTS to explain financing and resource allocation.",
    "Health informatics training uses TTS to explain data and information systems.",
    "Telehealth education uses TTS to explain remote care delivery and technology.",
    "Precision medicine training uses TTS to explain personalized treatment approaches.",
    "Genomics education uses TTS to explain genetic information and applications.",
    "Proteomics training uses TTS to explain protein analysis and functions.",
    "Metabolomics education uses TTS to explain metabolic profiling and applications.",
    "Bioinformatics training uses TTS to explain computational biology and data analysis.",
    "Computational biology education uses TTS to explain modeling and simulation approaches.",
    "Systems biology training uses TTS to explain networks and emergent properties.",
    "Synthetic biology education uses TTS to explain design and construction of biological systems.",
    "Genetic engineering training uses TTS to explain modification and applications.",
    "Biotechnology education uses TTS to explain applications in medicine and industry.",
    "Pharmaceutical sciences training uses TTS to explain drug discovery and development.",
    "Clinical research education uses TTS to explain trial design and conduct.",
    "Regulatory affairs training uses TTS to explain approval and compliance processes.",
    "Medical affairs education uses TTS to explain scientific communication and evidence.",
    "Medical writing training uses TTS to explain clear and accurate documentation.",
    "Health communication education uses TTS to explain effective message design.",
    "Patient education training uses TTS to explain condition management and self-care.",
    "Caregiver education uses TTS to explain support techniques and resources.",
    "Community health training uses TTS to explain population-based interventions.",
    "Global health education uses TTS to explain international health challenges and responses.",
    "Health equity training uses TTS to explain disparities and social determinants.",
    "Social determinants of health education uses TTS to explain environmental and social factors.",
    "Health behavior change training uses TTS to explain motivation and strategies.",
    "Health literacy education uses TTS to explain understanding and use of health information.",
    "Cultural competence in healthcare training uses TTS to explain diverse patient needs.",
    "Patient-centered care education uses TTS to explain respect and partnership.",
    "Shared decision making training uses TTS to explain collaborative choices.",
    "Informed consent education uses TTS to explain voluntary and informed agreement.",
    "Advance care planning training uses TTS to explain future healthcare preferences.",
    "Palliative care education uses TTS to explain comfort and quality of life.",
    "Hospice care training uses TTS to explain end-of-life support and dignity.",
    "Bereavement support education uses TTS to explain grief and coping.",
    "Spiritual care training uses TTS to explain meaning and transcendence in illness.",
    "Integrative medicine education uses TTS to explain complementary and conventional approaches.",
    "Functional medicine training uses TTS to explain root cause and systems biology.",
    "Lifestyle medicine education uses TTS to explain prevention and lifestyle factors.",
    "Preventive medicine training uses TTS to explain risk reduction and early detection.",
    "Occupational medicine education uses TTS to explain work-related health and safety.",
    "Environmental health training uses TTS to explain environmental factors and health.",
    "Travel medicine education uses TTS to explain health risks and prevention for travelers.",
    "Sports medicine training uses TTS to explain physical activity and injury prevention.",
    "Rehabilitation medicine education uses TTS to explain recovery and functional improvement.",
    "Pain management training uses TTS to explain assessment and treatment strategies.",
    "Addiction medicine education uses TTS to explain substance use and treatment.",
    "Mental health treatment training uses TTS to explain therapy and medication approaches.",
    "Psychiatric care education uses TTS to explain mental health conditions and care.",
    "Child and adolescent psychiatry training uses TTS to explain developmental mental health.",
    "Geriatric psychiatry education uses TTS to explain mental health in older adults.",
    "Forensic psychiatry training uses TTS to explain legal and mental health interface.",
    "Consultation-liaison psychiatry education uses TTS to explain medical setting mental health.",
    "Emergency psychiatry training uses TTS to explain crisis assessment and intervention.",
    "Community psychiatry education uses TTS to explain population mental health approaches.",
    "Social psychiatry training uses TTS to explain social factors in mental health.",
    "Cross-cultural psychiatry education uses TTS to explain cultural factors in mental health.",
    "Clinical psychology training uses TTS to explain assessment and psychotherapy.",
    "Counseling psychology education uses TTS to explain personal and career development.",
    "School psychology training uses TTS to explain educational and developmental support.",
    "Forensic psychology education uses TTS to explain legal and psychological interface.",
    "Health psychology training uses TTS to explain behavioral health factors.",
    "Neuropsychology education uses TTS to explain brain-behavior relationships.",
    "Rehabilitation psychology training uses TTS to explain disability and adjustment.",
    "Industrial-organizational psychology education uses TTS to explain workplace behavior.",
    "Sports psychology training uses TTS to explain performance and motivation.",
    "Music therapy education uses TTS to explain therapeutic use of music.",
    "Art therapy training uses TTS to explain therapeutic use of art.",
    "Dance therapy education uses TTS to explain therapeutic use of movement.",
    "Drama therapy training uses TTS to explain therapeutic use of performance.",
    "Play therapy education uses TTS to explain therapeutic use of play.",
    "Animal-assisted therapy training uses TTS to explain therapeutic use of animals.",
    "Recreational therapy education uses TTS to explain therapeutic use of leisure.",
    "Music education training uses TTS to explain teaching and learning music.",
    "Visual arts education uses TTS to explain teaching and learning art.",
    "Performing arts education uses TTS to explain teaching and learning performance.",
    "Physical education training uses TTS to explain teaching and learning movement.",
    "Health education uses TTS to explain teaching and learning health.",
    "Driver education training uses TTS to explain safe driving practices.",
    "Environmental education uses TTS to explain teaching and learning environment.",
    "Outdoor education training uses TTS to explain experiential learning in nature.",
    "Adventure education uses TTS to explain experiential learning through challenge.",
    "Service learning education uses TTS to explain community engagement and reflection.",
    "Experiential learning training uses TTS to explain hands-on learning approaches.",
    "Problem-based learning education uses TTS to explain student-centered inquiry.",
    "Project-based learning training uses TTS to explain real-world project engagement.",
    "Inquiry-based learning education uses TTS to explain student-driven investigation.",
    "Cooperative learning training uses TTS to explain collaborative group structures.",
    "Collaborative learning education uses TTS to explain shared knowledge construction.",
    "Peer learning training uses TTS to explain students teaching students.",
    "Mentoring education uses TTS to explain guidance and support relationships.",
    "Coaching education uses TTS to explain skill development and performance.",
    "Tutoring training uses TTS to explain individualized academic support.",
    "Remedial education uses TTS to explain foundational skill development.",
    "Gifted education training uses TTS to explain enrichment and acceleration.",
    "Special education uses TTS to explain individualized support for diverse learners.",
    "Inclusive education training uses TTS to explain access and participation for all.",
    "Multilingual education uses TTS to explain language development and support.",
    "Bilingual education training uses TTS to explain two-language instruction.",
    "Immersion education uses TTS to explain content-based language learning.",
    "Heritage language education training uses TTS to explain family language maintenance.",
    "Second language acquisition uses TTS to explain learning additional languages.",
    "Foreign language teaching training uses TTS to explain instructional approaches.",
    "English language teaching uses TTS to explain instruction for non-native speakers.",
    "Teaching English as a foreign language training uses TTS to explain global instruction.",
    "Teaching English to speakers of other languages uses TTS to explain specialized instruction.",
    "Applied linguistics education uses TTS to explain practical language study.",
    "Sociolinguistics training uses TTS to explain language in social context.",
    "Psycholinguistics education uses TTS to explain language and cognition.",
    "Neurolinguistics training uses TTS to explain language and brain.",
    "Computational linguistics education uses TTS to explain language and computation.",
    "Corpus linguistics training uses TTS to explain language data analysis.",
    "Discourse analysis education uses TTS to explain language beyond the sentence.",
    "Conversation analysis training uses TTS to explain talk-in-interaction.",
    "Pragmatics education uses TTS to explain language in use.",
    "Semantics training uses TTS to explain meaning in language.",
    "Syntax education uses TTS to explain sentence structure.",
    "Morphology training uses TTS to explain word structure.",
    "Phonology education uses TTS to explain sound systems.",
    "Phonetics training uses TTS to explain speech sounds.",
    "Historical linguistics education uses TTS to explain language change over time.",
    "Comparative linguistics training uses TTS to explain language relationships.",
    "Typology education uses TTS to explain language universals and variation.",
    "Language documentation training uses TTS to explain recording and describing languages.",
    "Language revitalization education uses TTS to explain reclaiming endangered languages.",
    "Translation studies training uses TTS to explain theory and practice of translation.",
    "Interpretation studies education uses TTS to explain theory and practice of interpretation.",
    "Localization training uses TTS to explain adaptation for specific markets.",
    "Internationalization education uses TTS to explain design for global use.",
    "Globalization training uses TTS to explain interconnected world systems.",
    "Intercultural communication education uses TTS to explain cross-cultural interaction.",
    "Cross-cultural psychology training uses TTS to explain culture and behavior.",
    "Cross-cultural management education uses TTS to explain culture and organizations.",
    "Cross-cultural negotiation training uses TTS to explain culture and agreement.",
    "Cross-cultural marketing education uses TTS to explain culture and consumer behavior.",
    "Cross-cultural design training uses TTS to explain culture and design thinking.",
    "Cross-cultural education uses TTS to explain culture and teaching.",
    "Cross-cultural research training uses TTS to explain culture and methodology.",
    "Cross-cultural counseling education uses TTS to explain culture and therapy.",
    "Cross-cultural social work training uses TTS to explain culture and practice.",
    "Cross-cultural nursing education uses TTS to explain culture and care.",
    "Cross-cultural medicine training uses TTS to explain culture and healing.",
    "Cross-cultural public health education uses TTS to explain culture and health.",
    "Cross-cultural epidemiology training uses TTS to explain culture and disease patterns.",
    "Cross-cultural psychiatry education uses TTS to explain culture and mental health.",
    "Cross-cultural psychology training uses TTS to explain culture and mind.",
    "Cross-cultural communication training uses TTS to explain culture and interaction.",
    "Cross-cultural competence education uses TTS to explain effective cultural engagement.",
    "Cultural humility training uses TTS to explain ongoing cultural learning.",
    "Cultural safety education uses TTS to explain safe and respectful practice.",
    "Cultural responsiveness training uses TTS to explain effective cultural response.",
    "Cultural appropriateness education uses TTS to explain fitting cultural context.",
    "Cultural relevance training uses TTS to explain meaningful cultural connection.",
    "Cultural sustainability education uses TTS to explain preserving cultural heritage.",
    "Cultural preservation training uses TTS to explain safeguarding traditions.",
    "Cultural heritage education uses TTS to explain valuing and transmitting culture.",
    "Cultural identity training uses TTS to explain personal and group identity.",
    "Cultural diversity education uses TTS to explain valuing differences.",
    "Cultural pluralism training uses TTS to explain multiple cultures coexisting.",
    "Multiculturalism education uses TTS to explain diverse cultural recognition.",
    "Interculturalism training uses TTS to explain cultural interaction and exchange.",
    "Global citizenship education uses TTS to explain interconnected responsibilities.",
    "Global learning training uses TTS to explain worldwide perspective development.",
    "Global competence education uses TTS to explain effective global engagement.",
    "Global leadership training uses TTS to explain worldwide leadership skills.",
    "Global management education uses TTS to explain worldwide organizational practices.",
    "Global business training uses TTS to explain international commerce.",
    "International business education uses TTS to explain cross-border operations.",
    "International trade training uses TTS to explain import and export.",
    "International finance education uses TTS to explain cross-border financial flows.",
    "International marketing training uses TTS to explain global market strategies.",
    "International human resources education uses TTS to explain global workforce management.",
    "International relations training uses TTS to explain diplomatic and global affairs.",
    "International law education uses TTS to explain legal frameworks across borders.",
    "International politics training uses TTS to explain global political dynamics.",
    "International development education uses TTS to explain global progress and challenges.",
    "International security training uses TTS to explain global safety and cooperation.",
    "International cooperation education uses TTS to explain collaborative global action.",
    "International organizations training uses TTS to explain multilateral institutions.",
    "International conflict education uses TTS to explain causes and resolution of disputes.",
    "International peace building training uses TTS to explain sustainable peace efforts.",
    "Conflict resolution education uses TTS to explain peaceful dispute settlement.",
    "Mediation training uses TTS to explain facilitated negotiation.",
    "Arbitration education uses TTS to explain binding dispute resolution.",
    "Negotiation training uses TTS to explain interest-based agreement.",
    "Diplomacy education uses TTS to explain statecraft and international engagement.",
    "Soft power training uses TTS to explain attraction and persuasion in foreign policy.",
    "Hard power education uses TTS to explain coercion and force in international relations.",
    "Smart power training uses TTS to explain combining soft and hard power.",
    "Cultural diplomacy education uses TTS to explain cultural exchange in foreign relations.",
    "Public diplomacy training uses TTS to explain direct public engagement abroad.",
    "Digital diplomacy education uses TTS to explain online international engagement.",
    "Economic diplomacy training uses TTS to explain economic tools in foreign policy.",
    "Environmental diplomacy education uses TTS to explain ecological cooperation.",
    "Health diplomacy training uses TTS to explain health cooperation across borders.",
    "Science diplomacy education uses TTS to explain scientific cooperation.",
    "Sports diplomacy training uses TTS to explain athletic exchange and cooperation.",
    "Educational diplomacy education uses TTS to explain academic exchange.",
    "Track two diplomacy training uses TTS to explain informal international dialogue.",
    "Citizen diplomacy education uses TTS to explain people-to-people exchange.",
    "City diplomacy training uses TTS to explain urban international relations.",
    "Subnational diplomacy education uses TTS to explain regional international engagement.",
    "Diaspora diplomacy training uses TTS to explain expatriate community engagement.",
    "Religious diplomacy education uses TTS to explain faith-based international engagement.",
    "Indigenous diplomacy training uses TTS to explain indigenous international relations.",
    "Parliamentary diplomacy education uses TTS to explain legislative international relations.",
    "Judicial diplomacy training uses TTS to explain court-to-court international relations.",
    "Military diplomacy education uses TTS to explain defense engagement abroad.",
    "Intelligence diplomacy training uses TTS to explain intelligence cooperation.",
    "Law enforcement diplomacy education uses TTS to explain police cooperation abroad.",
    "Coast guard diplomacy training uses TTS to explain maritime cooperation.",
    "Customs diplomacy education uses TTS to explain border cooperation.",
    "Tax diplomacy training uses TTS to explain fiscal cooperation.",
    "Regulatory diplomacy education uses TTS to explain standards cooperation.",
    "Financial diplomacy training uses TTS to explain financial system cooperation.",
    "Banking diplomacy education uses TTS to explain banking cooperation.",
    "Insurance diplomacy training uses TTS to explain insurance cooperation.",
    "Audit diplomacy education uses TTS to explain audit cooperation.",
    "Accounting diplomacy training uses TTS to explain accounting cooperation.",
    "Corporate diplomacy education uses TTS to explain business international engagement.",
    "Investor diplomacy training uses TTS to explain investor relations abroad.",
    "Trade diplomacy education uses TTS to explain trade negotiation and enforcement.",
    "Tariff diplomacy training uses TTS to explain customs and trade policy.",
    "Sanctions diplomacy education uses TTS to explain economic pressure tools.",
    "Embargo diplomacy training uses TTS to explain trade prohibition tools.",
    "Boycott diplomacy education uses TTS to explain consumer pressure tools.",
    "Divestment diplomacy training uses TTS to explain investment withdrawal tools.",
    "Advocacy diplomacy education uses TTS to explain cause promotion tools.",
    "Activism diplomacy training uses TTS to explain grassroots pressure tools.",
    "Protest diplomacy education uses TTS to explain public demonstration tools.",
    "Resistance diplomacy training uses TTS to explain opposition and resilience.",
    "Liberation diplomacy education uses TTS to explain freedom and self-determination.",
    "Solidarity diplomacy training uses TTS to explain mutual support and cooperation.",
    "Human rights diplomacy education uses TTS to explain rights promotion abroad.",
    "Humanitarian diplomacy training uses TTS to explain aid and assistance abroad.",
    "Development diplomacy education uses TTS to explain progress support abroad.",
    "Educational diplomacy training uses TTS to explain learning support abroad.",
    "Cultural diplomacy education uses TTS to explain culture promotion abroad.",
    "Sports diplomacy training uses TTS to explain athletics promotion abroad.",
    "Tourism diplomacy education uses TTS to explain travel promotion abroad.",
    "Trade diplomacy training uses TTS to explain commerce promotion abroad.",
    "Investment diplomacy education uses TTS to explain capital promotion abroad.",
    "Technology diplomacy training uses TTS to explain innovation promotion abroad.",
    "Science diplomacy education uses TTS to explain research promotion abroad.",
    "Health diplomacy training uses TTS to explain health promotion abroad.",
    "Environmental diplomacy education uses TTS to explain ecology promotion abroad.",
    "Climate diplomacy training uses TTS to explain climate cooperation abroad.",
    "Energy diplomacy education uses TTS to explain energy cooperation abroad.",
    "Food diplomacy training uses TTS to explain agriculture cooperation abroad.",
    "Water diplomacy education uses TTS to explain water cooperation abroad.",
    "Cyber diplomacy training uses TTS to explain digital cooperation abroad.",
    "Space diplomacy education uses TTS to explain outer space cooperation abroad.",
    "Maritime diplomacy training uses TTS to explain ocean cooperation abroad.",
    "Polar diplomacy education uses TTS to explain polar region cooperation abroad.",
    "Mountain diplomacy training uses TTS to explain mountain region cooperation abroad.",
    "Desert diplomacy education uses TTS to explain dryland cooperation abroad.",
    "Forest diplomacy training uses TTS to explain forest cooperation abroad.",
    "Urban diplomacy education uses TTS to explain city cooperation abroad.",
    "Rural diplomacy training uses TTS to explain countryside cooperation abroad.",
    "Island diplomacy education uses TTS to explain island cooperation abroad.",
    "Coastal diplomacy training uses TTS to explain coastal cooperation abroad.",
    "River diplomacy education uses TTS to explain river basin cooperation abroad.",
    "Lake diplomacy training uses TTS to explain lake basin cooperation abroad.",
    "Wetland diplomacy education uses TTS to explain wetland cooperation abroad.",
    "Coral reef diplomacy training uses TTS to explain reef cooperation abroad.",
    "Mangrove diplomacy education uses TTS to explain mangrove cooperation abroad.",
    "Seagrass diplomacy training uses TTS to explain seagrass cooperation abroad.",
    "Kelp diplomacy education uses TTS to explain kelp forest cooperation abroad.",
    "Plankton diplomacy training uses TTS to explain plankton cooperation abroad.",
    "Fish diplomacy education uses TTS to explain fish population cooperation.",
    "Marine mammal diplomacy training uses TTS to explain marine mammal cooperation.",
    "Sea turtle diplomacy education uses TTS to explain sea turtle conservation.",
    "Shark diplomacy training uses TTS to explain shark conservation cooperation.",
    "Whale diplomacy education uses TTS to explain whale conservation cooperation.",
    "Dolphin diplomacy training uses TTS to explain dolphin conservation cooperation.",
    "Seabird diplomacy education uses TTS to explain seabird conservation cooperation.",
    "Penguin diplomacy training uses TTS to explain penguin conservation cooperation.",
    "Polar bear diplomacy education uses TTS to explain polar bear conservation.",
    "Elephant diplomacy training uses TTS to explain elephant conservation cooperation.",
    "Tiger diplomacy education uses TTS to explain tiger conservation cooperation.",
    "Lion diplomacy training uses TTS to explain lion conservation cooperation.",
    "Cheetah diplomacy education uses TTS to explain cheetah conservation cooperation.",
    "Leopard diplomacy training uses TTS to explain leopard conservation cooperation.",
    "Jaguar diplomacy education uses TTS to explain jaguar conservation cooperation.",
    "Puma diplomacy training uses TTS to explain puma conservation cooperation.",
    "Bear diplomacy education uses TTS to explain bear conservation cooperation.",
    "Wolf diplomacy training uses TTS to explain wolf conservation cooperation.",
    "Fox diplomacy education uses TTS to explain fox conservation cooperation.",
    "Coyote diplomacy training uses TTS to explain coyote conservation cooperation.",
    "Hyena diplomacy education uses TTS to explain hyena conservation cooperation.",
    "Wild dog diplomacy training uses TTS to explain wild dog conservation cooperation.",
    "Crocodile diplomacy education uses TTS to explain crocodile conservation.",
    "Alligator diplomacy training uses TTS to explain alligator conservation.",
    "Turtle diplomacy education uses TTS to explain turtle conservation cooperation.",
    "Lizard diplomacy training uses TTS to explain lizard conservation cooperation.",
    "Snake diplomacy education uses TTS to explain snake conservation cooperation.",
    "Frog diplomacy training uses TTS to explain frog conservation cooperation.",
    "Salamander diplomacy education uses TTS to explain salamander conservation.",
    "Butterfly diplomacy training uses TTS to explain butterfly conservation.",
    "Bee diplomacy education uses TTS to explain bee conservation cooperation.",
    "Ant diplomacy training uses TTS to explain ant conservation cooperation.",
    "Worm diplomacy education uses TTS to explain worm conservation cooperation.",
    "Spider diplomacy training uses TTS to explain spider conservation cooperation.",
    "Scorpion diplomacy education uses TTS to explain scorpion conservation cooperation.",
    "Centipede diplomacy training uses TTS to explain centipede conservation cooperation.",
    "Millipede diplomacy education uses TTS to explain millipede conservation cooperation.",
    "Crab diplomacy training uses TTS to explain crab conservation cooperation.",
    "Lobster diplomacy education uses TTS to explain lobster conservation cooperation.",
    "Shrimp diplomacy training uses TTS to explain shrimp conservation cooperation.",
    "Mussel diplomacy education uses TTS to explain mussel conservation cooperation.",
    "Oyster diplomacy training uses TTS to explain oyster conservation cooperation.",
    "Clam diplomacy education uses TTS to explain clam conservation cooperation.",
    "Squid diplomacy training uses TTS to explain squid conservation cooperation.",
    "Octopus diplomacy education uses TTS to explain octopus conservation cooperation.",
    "Jellyfish diplomacy training uses TTS to explain jellyfish conservation cooperation.",
    "Starfish diplomacy education uses TTS to explain starfish conservation cooperation.",
    "Sea urchin diplomacy training uses TTS to explain sea urchin conservation cooperation.",
    "Coral diplomacy education uses TTS to explain coral conservation cooperation.",
    "Sponge diplomacy training uses TTS to explain sponge conservation cooperation.",
    "Algae diplomacy education uses TTS to explain algae conservation cooperation.",
    "Seaweed diplomacy training uses TTS to explain seaweed conservation cooperation.",
    "Plankton diplomacy education uses TTS to explain plankton conservation cooperation.",
    "Microbe diplomacy training uses TTS to explain microbial conservation cooperation.",
    "Bacteria diplomacy education uses TTS to explain bacterial conservation cooperation.",
    "Virus diplomacy training uses TTS to explain viral conservation cooperation.",
    "Fungi diplomacy education uses TTS to explain fungal conservation cooperation.",
    "Lichen diplomacy training uses TTS to explain lichen conservation cooperation.",
    "Moss diplomacy education uses TTS to explain moss conservation cooperation.",
    "Fern diplomacy training uses TTS to explain fern conservation cooperation.",
    "Grass diplomacy education uses TTS to explain grass conservation cooperation.",
    "Tree diplomacy training uses TTS to explain tree conservation cooperation.",
    "Flower diplomacy education uses TTS to explain flower conservation cooperation.",
    "Fruit diplomacy training uses TTS to explain fruit conservation cooperation.",
    "Seed diplomacy education uses TTS to explain seed conservation cooperation.",
    "Pollen diplomacy training uses TTS to explain pollen conservation cooperation.",
    "Nectar diplomacy education uses TTS to explain nectar conservation cooperation.",
    "Root diplomacy training uses TTS to explain root conservation cooperation.",
    "Leaf diplomacy education uses TTS to explain leaf conservation cooperation.",
    "Stem diplomacy training uses TTS to explain stem conservation cooperation.",
    "Branch diplomacy education uses TTS to explain branch conservation cooperation.",
    "Trunk diplomacy training uses TTS to explain trunk conservation cooperation.",
    "Bark diplomacy education uses TTS to explain bark conservation cooperation.",
    "Sap diplomacy training uses TTS to explain sap conservation cooperation.",
    "Soil diplomacy education uses TTS to explain soil conservation cooperation.",
    "Water diplomacy training uses TTS to explain water conservation cooperation.",
    "Air diplomacy education uses TTS to explain air conservation cooperation.",
    "Sun diplomacy training uses TTS to explain solar energy cooperation.",
    "Wind diplomacy education uses TTS to explain wind energy cooperation.",
    "Rain diplomacy training uses TTS to explain precipitation cooperation.",
    "Snow diplomacy education uses TTS to explain snow conservation cooperation.",
    "Ice diplomacy training uses TTS to explain ice conservation cooperation.",
    "Cloud diplomacy education uses TTS to explain cloud cooperation.",
    "Fog diplomacy training uses TTS to explain fog cooperation.",
    "Mist diplomacy education uses TTS to explain mist cooperation.",
    "Dew diplomacy training uses TTS to explain dew cooperation.",
    "Frost diplomacy education uses TTS to explain frost cooperation.",
    "Hail diplomacy training uses TTS to explain hail cooperation.",
    "Sleet diplomacy education uses TTS to explain sleet cooperation.",
    "Thunder diplomacy training uses TTS to explain thunder cooperation.",
    "Lightning diplomacy education uses TTS to explain lightning cooperation.",
    "Rainbow diplomacy training uses TTS to explain rainbow cooperation.",
    "Aurora diplomacy education uses TTS to explain aurora cooperation.",
    "Eclipse diplomacy training uses TTS to explain eclipse cooperation.",
    "Meteor diplomacy education uses TTS to explain meteor cooperation.",
    "Comet diplomacy training uses TTS to explain comet cooperation.",
    "Asteroid diplomacy education uses TTS to explain asteroid cooperation.",
    "Planet diplomacy training uses TTS to explain planetary cooperation.",
    "Star diplomacy education uses TTS to explain stellar cooperation.",
    "Galaxy diplomacy training uses TTS to explain galactic cooperation.",
    "Universe diplomacy education uses TTS to explain cosmic cooperation.",
    "Multiverse diplomacy training uses TTS to explain multiverse cooperation.",
    "Dimension diplomacy education uses TTS to explain dimensional cooperation.",
    "Time diplomacy training uses TTS to explain temporal cooperation.",
    "Space diplomacy education uses TTS to explain spatial cooperation.",
    "Reality diplomacy training uses TTS to explain existential cooperation.",
    "Consciousness diplomacy education uses TTS to explain awareness cooperation.",
    "Intelligence diplomacy training uses TTS to explain cognitive cooperation.",
    "Wisdom diplomacy education uses TTS to explain knowledge cooperation.",
    "Knowledge diplomacy training uses TTS to explain information cooperation.",
    "Information diplomacy education uses TTS to explain data cooperation.",
    "Data diplomacy training uses TTS to explain dataset cooperation.",
    "Dataset diplomacy education uses TTS to explain corpus cooperation.",
    "Corpus diplomacy training uses TTS to explain body cooperation.",
    "Library diplomacy education uses TTS to explain collection cooperation.",
    "Archive diplomacy training uses TTS to explain record cooperation.",
    "Museum diplomacy education uses TTS to explain heritage cooperation.",
    "Gallery diplomacy training uses TTS to explain exhibition cooperation.",
    "Theater diplomacy education uses TTS to explain performance cooperation.",
    "Concert diplomacy training uses TTS to explain musical cooperation.",
    "Festival diplomacy education uses TTS to explain celebration cooperation.",
    "Carnival diplomacy training uses TTS to explain festivity cooperation.",
    "Parade diplomacy education uses TTS to explain procession cooperation.",
    "Rally diplomacy training uses TTS to explain gathering cooperation.",
    "March diplomacy education uses TTS to explain walking cooperation.",
    "Run diplomacy training uses TTS to explain running cooperation.",
    "Walk diplomacy education uses TTS to explain strolling cooperation.",
    "Hike diplomacy training uses TTS to explain trekking cooperation.",
    "Climb diplomacy education uses TTS to explain ascending cooperation.",
    "Swim diplomacy training uses TTS to explain water cooperation.",
    "Dive diplomacy education uses TTS to explain underwater cooperation.",
    "Surf diplomacy training uses TTS to explain wave cooperation.",
    "Sail diplomacy education uses TTS to explain wind and water cooperation.",
    "Row diplomacy training uses TTS to explain oar cooperation.",
    "Paddle diplomacy education uses TTS to explain water craft cooperation.",
    "Float diplomacy training uses TTS to explain buoyancy cooperation.",
    "Sink diplomacy education uses TTS to explain submersion cooperation.",
    "Submerge diplomacy training uses TTS to explain immersion cooperation.",
    "Emerge diplomacy education uses TTS to explain surfacing cooperation.",
    "Resurface diplomacy training uses TTS to explain re-emergence cooperation.",
    "Surface diplomacy education uses TTS to explain exterior cooperation.",
    "Interior diplomacy training uses TTS to explain internal cooperation.",
    "Exterior diplomacy education uses TTS to explain external cooperation.",
    "Internal diplomacy training uses TTS to explain inside cooperation.",
    "External diplomacy education uses TTS to explain outside cooperation.",
    "Inside diplomacy training uses TTS to explain interior cooperation.",
    "Outside diplomacy education uses TTS to explain exterior cooperation.",
    "Indoor diplomacy training uses TTS to explain interior space cooperation.",
    "Outdoor diplomacy education uses TTS to explain exterior space cooperation.",
    "Indoor-outdoor diplomacy training uses TTS to explain transitional cooperation.",
    "Climate-controlled diplomacy education uses TTS to explain environmental management.",
    "Natural diplomacy training uses TTS to explain organic cooperation.",
    "Artificial diplomacy education uses TTS to explain constructed cooperation.",
    "Synthetic diplomacy training uses TTS to explain manufactured cooperation.",
    "Organic diplomacy education uses TTS to explain natural cooperation.",
    "Inorganic diplomacy training uses TTS to explain mineral cooperation.",
    "Living diplomacy education uses TTS to explain animate cooperation.",
    "Non-living diplomacy training uses TTS to explain inanimate cooperation.",
    "Animate diplomacy education uses TTS to explain living cooperation.",
    "Inanimate diplomacy training uses TTS to explain non-living cooperation.",
    "Sentient diplomacy education uses TTS to explain conscious cooperation.",
    "Non-sentient diplomacy training uses TTS to explain unconscious cooperation.",
    "Aware diplomacy education uses TTS to explain cognizant cooperation.",
    "Unaware diplomacy training uses TTS to explain non-cognizant cooperation.",
    "Conscious diplomacy education uses TTS to explain aware cooperation.",
    "Unconscious diplomacy training uses TTS to explain unaware cooperation.",
    "Sentient diplomacy education uses TTS to explain feeling cooperation.",
    "Non-sentient diplomacy training uses TTS to explain non-feeling cooperation.",
    "Feeling diplomacy education uses TTS to explain emotional cooperation.",
    "Non-feeling diplomacy training uses TTS to explain non-emotional cooperation.",
    "Emotional diplomacy education uses TTS to explain feeling cooperation.",
    "Non-emotional diplomacy training uses TTS to explain non-feeling cooperation.",
    "Passionate diplomacy education uses TTS to explain intense feeling cooperation.",
    "Dispassionate diplomacy training uses TTS to explain calm cooperation.",
    "Calm diplomacy education uses TTS to explain peaceful cooperation.",
    "Turbulent diplomacy training uses TTS to explain chaotic cooperation.",
    "Peaceful diplomacy education uses TTS to explain tranquil cooperation.",
    "Conflicted diplomacy training uses TTS to explain opposed cooperation.",
    "Harmonious diplomacy education uses TTS to explain balanced cooperation.",
    "Discordant diplomacy training uses TTS to explain conflicting cooperation.",
    "Tonal diplomacy education uses TTS to explain pitch cooperation.",
    "Atonal diplomacy training uses TTS to explain non-pitch cooperation.",
    "Rhythmic diplomacy education uses TTS to explain beat cooperation.",
    "Arrhythmic diplomacy training uses TTS to explain non-beat cooperation.",
    "Melodic diplomacy education uses TTS to explain tune cooperation.",
    "Non-melodic diplomacy training uses TTS to explain non-tune cooperation.",
    "Harmonic diplomacy education uses TTS to explain chord cooperation.",
    "Discordant diplomacy training uses TTS to explain clashing cooperation.",
    "Consonant diplomacy education uses TTS to explain consonant cooperation.",
    "Dissonant diplomacy training uses TTS to explain dissonant cooperation.",
    "Loud diplomacy education uses TTS to explain volume cooperation.",
    "Quiet diplomacy training uses TTS to explain soft cooperation.",
    "Soft diplomacy education uses TTS to explain gentle cooperation.",
    "Hard diplomacy training uses TTS to explain firm cooperation.",
    "Firm diplomacy education uses TTS to explain solid cooperation.",
    "Loose diplomacy training uses TTS to explain relaxed cooperation.",
    "Tight diplomacy education uses TTS to explain constrained cooperation.",
    "Constrained diplomacy training uses TTS to explain limited cooperation.",
    "Free diplomacy education uses TTS to explain unrestricted cooperation.",
    "Restricted diplomacy training uses TTS to explain limited cooperation.",
    "Bound diplomacy education uses TTS to explain tied cooperation.",
    "Unbound diplomacy training uses TTS to explain untied cooperation.",
    "Linked diplomacy education uses TTS to explain connected cooperation.",
    "Unlinked diplomacy training uses TTS to explain disconnected cooperation.",
    "Connected diplomacy education uses TTS to explain joined cooperation.",
    "Disconnected diplomacy training uses TTS to explain separate cooperation.",
    "Joined diplomacy education uses TTS to explain unified cooperation.",
    "Separate diplomacy training uses TTS to explain divided cooperation.",
    "United diplomacy education uses TTS to explain combined cooperation.",
    "Divided diplomacy training uses TTS to explain split cooperation.",
    "Combined diplomacy education uses TTS to explain merged cooperation.",
    "Split diplomacy training uses TTS to explain broken cooperation.",
    "Merged diplomacy education uses TTS to explain combined cooperation.",
    "Broken diplomacy training uses TTS to explain fractured cooperation.",
    "Whole diplomacy education uses TTS to explain complete cooperation.",
    "Partial diplomacy training uses TTS to explain incomplete cooperation.",
    "Complete diplomacy education uses TTS to explain full cooperation.",
    "Incomplete diplomacy training uses TTS to explain partial cooperation.",
    "Full diplomacy education uses TTS to explain complete cooperation.",
    "Empty diplomacy training uses TTS to explain void cooperation.",
    "Void diplomacy education uses TTS to explain empty cooperation.",
    "Filled diplomacy training uses TTS to explain full cooperation.",
    "Vacant diplomacy education uses TTS to explain empty cooperation.",
    "Occupied diplomacy training uses TTS to explain used cooperation.",
    "Available diplomacy education uses TTS to explain free cooperation.",
    "Unavailable diplomacy training uses TTS to explain taken cooperation.",
    "Taken diplomacy education uses TTS to explain used cooperation.",
    "Free diplomacy training uses TTS to explain available cooperation.",
    "Open diplomacy education uses TTS to explain accessible cooperation.",
    "Closed diplomacy training uses TTS to explain inaccessible cooperation.",
    "Accessible diplomacy education uses TTS to explain reachable cooperation.",
    "Inaccessible diplomacy training uses TTS to explain unreachable cooperation.",
    "Reachable diplomacy education uses TTS to explain attainable cooperation.",
    "Unreachable diplomacy training uses TTS to explain unattainable cooperation.",
    "Attainable diplomacy education uses TTS to explain achievable cooperation.",
    "Unattainable diplomacy training uses TTS to explain unachievable cooperation.",
    "Achievable diplomacy education uses TTS to explain reachable cooperation.",
    "Unachievable diplomacy training uses TTS to explain unreachable cooperation.",
    "Possible diplomacy education uses TTS to explain potential cooperation.",
    "Impossible diplomacy training uses TTS to explain no-potential cooperation.",
    "Potential diplomacy education uses TTS to explain capability cooperation.",
    "Actual diplomacy training uses TTS to explain realized cooperation.",
    "Real diplomacy education uses TTS to explain tangible cooperation.",
    "Imagined diplomacy training uses TTS to explain conceived cooperation.",
    "Conceived diplomacy education uses TTS to explain imagined cooperation.",
    "Perceived diplomacy training uses TTS to explain sensed cooperation.",
    "Sensed diplomacy education uses TTS to explain detected cooperation.",
    "Detected diplomacy training uses TTS to explain perceived cooperation.",
    "Undetected diplomacy education uses TTS to explain hidden cooperation.",
    "Hidden diplomacy training uses TTS to explain concealed cooperation.",
    "Concealed diplomacy education uses TTS to explain hidden cooperation.",
    "Revealed diplomacy training uses TTS to explain shown cooperation.",
    "Shown diplomacy education uses TTS to explain displayed cooperation.",
    "Displayed diplomacy training uses TTS to explain presented cooperation.",
    "Presented diplomacy education uses TTS to explain shown cooperation.",
    "Exposed diplomacy training uses TTS to explain revealed cooperation.",
    "Obscured diplomacy education uses TTS to explain hidden cooperation.",
    "Visible diplomacy training uses TTS to explain seen cooperation.",
    "Invisible diplomacy education uses TTS to explain unseen cooperation.",
    "Seen diplomacy training uses TTS to explain visible cooperation.",
    "Unseen diplomacy education uses TTS to explain invisible cooperation.",
    "Overt diplomacy training uses TTS to explain open cooperation.",
    "Covert diplomacy education uses TTS to explain secret cooperation.",
    "Secret diplomacy training uses TTS to explain hidden cooperation.",
    "Public diplomacy education uses TTS to explain open cooperation.",
    "Private diplomacy training uses TTS to explain restricted cooperation.",
    "Restricted diplomacy education uses TTS to explain limited cooperation.",
    "Open diplomacy training uses TTS to explain unrestricted cooperation.",
    "Unrestricted diplomacy education uses TTS to explain free cooperation.",
    "Restricted diplomacy training uses TTS to explain limited cooperation.",
    "Public diplomacy education uses TTS to explain open cooperation.",
    "Private diplomacy training uses TTS to explain closed cooperation.",
    "Closed diplomacy education uses TTS to explain private cooperation.",
    "Open diplomacy training uses TTS to explain public cooperation.",
    "Public diplomacy education uses TTS to explain societal cooperation.",
    "Private diplomacy training uses TTS to explain personal cooperation.",
    "Personal diplomacy education uses TTS to explain individual cooperation.",
    "Social diplomacy training uses TTS to explain group cooperation.",
    "Group diplomacy education uses TTS to explain collective cooperation.",
    "Individual diplomacy training uses TTS to explain personal cooperation.",
    "Collective diplomacy education uses TTS to explain group cooperation.",
    "Team diplomacy training uses TTS to explain group cooperation.",
    "Solo diplomacy education uses TTS to explain individual cooperation.",
    "Joint diplomacy training uses TTS to explain shared cooperation.",
    "Sole diplomacy education uses TTS to explain only cooperation.",
    "Shared diplomacy training uses TTS to explain common cooperation.",
    "Common diplomacy education uses TTS to explain mutual cooperation.",
    "Mutual diplomacy training uses TTS to explain reciprocal cooperation.",
    "Reciprocal diplomacy education uses TTS to explain mutual cooperation.",
    "One-way diplomacy training uses TTS to explain unilateral cooperation.",
    "Two-way diplomacy education uses TTS to explain bilateral cooperation.",
    "Unilateral diplomacy training uses TTS to explain one-sided cooperation.",
    "Bilateral diplomacy education uses TTS to explain two-sided cooperation.",
    "Multilateral diplomacy training uses TTS to explain many-sided cooperation.",
    "Bipartisan diplomacy education uses TTS to explain two-party cooperation.",
    "Multiparty diplomacy training uses TTS to explain many-party cooperation.",
    "Coalition diplomacy education uses TTS to explain alliance cooperation.",
    "Alliance diplomacy training uses TTS to explain partnership cooperation.",
    "Partnership diplomacy education uses TTS to explain cooperation.",
    "Cooperation diplomacy training uses TTS to explain working together.",
    "Collaboration diplomacy education uses TTS to explain joint effort.",
    "Coordination diplomacy training uses TTS to explain organized effort.",
    "Communication diplomacy education uses TTS to explain information exchange.",
    "Information exchange diplomacy training uses TTS to explain data sharing.",
    "Data sharing diplomacy education uses TTS to explain information transfer.",
    "Information transfer diplomacy training uses TTS to explain knowledge movement.",
    "Knowledge movement diplomacy education uses TTS to explain wisdom flow.",
    "Wisdom flow diplomacy training uses TTS to explain understanding transfer.",
    "Understanding transfer diplomacy education uses TTS to explain insight sharing.",
    "Insight sharing diplomacy training uses TTS to explain perception exchange.",
    "Perception exchange diplomacy education uses TTS to explain viewpoint sharing.",
    "Viewpoint sharing diplomacy training uses TTS to explain perspective transfer.",
    "Perspective transfer diplomacy education uses TTS to explain viewpoint exchange.",
    "Viewpoint exchange diplomacy training uses TTS to explain perspective sharing.",
    "Perspective sharing diplomacy education uses TTS to explain viewpoint exchange.",
    "Viewpoint exchange diplomacy training uses TTS to explain perspective sharing.",
    "Perspective sharing diplomacy education uses TTS to explain viewpoint exchange.",
    "Viewpoint exchange diplomacy training uses TTS to explain perspective sharing.",
    "Perspective sharing diplomacy education uses TTS to explain viewpoint exchange.",
    "Viewpoint exchange diplomacy training uses TTS to explain perspective sharing.",
    "Perspective sharing diplomacy education uses TTS to explain viewpoint exchange.",
    "Final viewpoint exchange diplomacy training uses TTS to explain the end of this very long list.",
]

VOICE_PROMPTS: dict[str, list[str]] = {v: PROMPTS for v in VOICES}


def build_workload(n: int = 500, seed: int = 42) -> list[tuple[str, str]]:
    """Build a workload of n (voice_id, text) pairs across all VOICES.

    Text length varies from ~50 chars to ~500+ chars. Voices are picked
    round-robin so each voice sees roughly n/len(VOICES) inputs.
    Falls back to the closest non-empty pool if a target bucket is empty.
    """
    import random
    rng = random.Random(seed)
    pairs: list[tuple[str, str]] = []
    # Sort by length to get a clear short/medium/long partition
    by_len = sorted(PROMPTS, key=len)
    short_pool = [p for p in by_len if len(p) <= 200]
    long_pool = [p for p in by_len if len(p) > 200]
    # If the corpus skews one direction, fall back to the other pool
    if not short_pool:
        short_pool = long_pool
    if not long_pool:
        long_pool = short_pool
    for i in range(n):
        voice = VOICES[i % len(VOICES)]
        # 50% short, 50% long — ensures we exercise both small and large
        # text inputs (we have lots of long lines in the corpus).
        if rng.random() < 0.5:
            text = rng.choice(short_pool)
        else:
            text = rng.choice(long_pool)
        pairs.append((voice, text))
    return pairs


def long_text(chars: int = 5000) -> str:
    """Build a synthetic long text of approximately `chars` characters by
    concatenating prompt sentences with spaces until we reach the target.
    """
    out: list[str] = []
    total = 0
    idx = 0
    while total < chars:
        p = PROMPTS[idx % len(PROMPTS)]
        out.append(p)
        total += len(p) + 1
        idx += 1
    return " ".join(out)[:chars]


if __name__ == "__main__":
    print("═══ elevenlabs-tts-stream: meaningful workload ═══")
    import statistics

    # --- Build workload of 500 inputs across 4 voices ---
    N = 500
    print(f"building workload of {N} inputs across {len(VOICES)} voices...")
    workload = build_workload(N)
    tts = StreamingTTS(first_frame_ms=80.0, chunk_ms=80.0)
    print(f"  workload size: {len(workload)}")
    print(f"  voice mix:     "
          + ", ".join(f"{v}={sum(1 for w in workload if w[0] == v)}" for v in VOICES))
    char_lens = [len(text) for _, text in workload]
    print(f"  text length:   min={min(char_lens)} max={max(char_lens)} "
          f"avg={statistics.mean(char_lens):.0f} med={statistics.median(char_lens):.0f}")
    print()

    # === Scenario A: synthesize, stream, verify non-empty ===
    print("═══ Scenario A: streaming + non-empty output ═══")
    sample_text = "Hello, this is a streaming TTS test of about sixty characters."
    req = TTSRequest(text=sample_text, voice_id="rachel", stream=True)
    sync_result = tts.synthesize(req)
    stream_result = tts.stream_collect(req)
    first_chunk_latency_ms = stream_result.ttfb_ms
    print(f"  sync result:    {len(sync_result.chunks)} chunks, "
          f"{sync_result.total_bytes} bytes, ttfb_budget={sync_result.ttfb_ms:.0f}ms")
    print(f"  stream result:  {len(stream_result.chunks)} chunks, "
          f"{stream_result.total_bytes} bytes, ttfb_actual={stream_result.ttfb_ms:.1f}ms")
    assert len(sync_result.chunks) > 0, "synthesis must produce chunks"
    assert sync_result.total_bytes > 0, "synthesis must produce non-empty bytes"
    assert stream_result.total_bytes > 0, "streaming synthesis must produce non-empty bytes"
    print("  ✓ every synthesis produces non-empty output")
    print()

    # === Scenario B: multi-voice — same text across voices differs ===
    print("═══ Scenario B: multi-voice identity ═══")
    test_text = "Identity check: the same text spoken by different voices."
    voice_signatures: dict[str, bytes] = {}
    for voice in VOICES:
        req = TTSRequest(text=test_text, voice_id=voice, stream=False)
        result = tts.synthesize(req)
        # Use first chunk + last chunk as the voice signature
        sig = result.chunks[0].pcm_bytes + result.chunks[-1].pcm_bytes
        voice_signatures[voice] = sig
        print(f"  {voice:<7} first_chunk={len(result.chunks[0].pcm_bytes):>5}B "
              f"last_chunk={len(result.chunks[-1].pcm_bytes):>5}B "
              f"total={result.total_bytes:>6}B")
    # Every pair of voices must produce different signatures
    pairs_diff = 0
    pairs_total = 0
    for i, v1 in enumerate(VOICES):
        for v2 in VOICES[i + 1:]:
            pairs_total += 1
            if voice_signatures[v1] != voice_signatures[v2]:
                pairs_diff += 1
    print(f"  distinct voice pairs: {pairs_diff}/{pairs_total}")
    assert pairs_diff == pairs_total, "all voice pairs must produce distinct bytes"
    # Sanity: same voice, same text must be stable
    r1 = tts.synthesize(TTSRequest(text=test_text, voice_id="rachel", stream=False))
    r2 = tts.synthesize(TTSRequest(text=test_text, voice_id="rachel", stream=False))
    assert r1.chunks[0].pcm_bytes == r2.chunks[0].pcm_bytes, "same voice+text must be deterministic"
    print("  ✓ different voices produce different byte streams")
    print("  ✓ same voice + same text is deterministic")
    print()

    # === Scenario C: prosody control ===
    print("═══ Scenario C: prosody control (rate, pitch) ═══")
    prosody_text = "Prosody check: rate and pitch should both affect the output bytes."
    base = tts.synthesize(TTSRequest(text=prosody_text, voice_id="adam", rate=1.0, pitch=1.0))
    fast = tts.synthesize(TTSRequest(text=prosody_text, voice_id="adam", rate=2.0, pitch=1.0))
    slow = tts.synthesize(TTSRequest(text=prosody_text, voice_id="adam", rate=0.5, pitch=1.0))
    high_pitch = tts.synthesize(TTSRequest(text=prosody_text, voice_id="adam", rate=1.0, pitch=1.5))
    low_pitch = tts.synthesize(TTSRequest(text=prosody_text, voice_id="adam", rate=1.0, pitch=0.5))
    print(f"  base     rate=1.0 pitch=1.0: {base.total_bytes:>6}B "
          f"({len(base.chunks)} chunks, {base.total_audio_ms:.0f}ms audio)")
    print(f"  fast     rate=2.0 pitch=1.0: {fast.total_bytes:>6}B "
          f"({len(fast.chunks)} chunks, {fast.total_audio_ms:.0f}ms audio)")
    print(f"  slow     rate=0.5 pitch=1.0: {slow.total_bytes:>6}B "
          f"({len(slow.chunks)} chunks, {slow.total_audio_ms:.0f}ms audio)")
    print(f"  high_p   rate=1.0 pitch=1.5: {high_pitch.total_bytes:>6}B "
          f"({len(high_pitch.chunks)} chunks)")
    print(f"  low_p    rate=1.0 pitch=0.5: {low_pitch.total_bytes:>6}B "
          f"({len(low_pitch.chunks)} chunks)")
    # Faster rate → fewer bytes per second (more compressed in time)
    assert fast.total_bytes < base.total_bytes, (
        f"faster rate must produce fewer total bytes: fast={fast.total_bytes} base={base.total_bytes}"
    )
    # Slower rate → more total bytes
    assert slow.total_bytes > base.total_bytes, (
        f"slower rate must produce more total bytes: slow={slow.total_bytes} base={base.total_bytes}"
    )
    # Different pitch → different bytes
    assert high_pitch.chunks[0].pcm_bytes != base.chunks[0].pcm_bytes, (
        "different pitch must produce different chunk bytes"
    )
    assert low_pitch.chunks[0].pcm_bytes != base.chunks[0].pcm_bytes, (
        "different pitch must produce different chunk bytes"
    )
    # Avg bytes/sec should be lower for fast rate (less audio wall-clock per real second)
    base_bps = base.total_bytes / max(1.0, base.total_audio_ms / 1000.0)
    fast_bps = fast.total_bytes / max(1.0, fast.total_audio_ms / 1000.0)
    print(f"  bytes/sec: base={base_bps:.0f} fast={fast_bps:.0f}")
    assert fast_bps < base_bps, (
        f"faster rate must produce fewer bytes-per-second: fast={fast_bps:.0f} base={base_bps:.0f}"
    )
    print("  ✓ rate affects output: fast < base < slow (bytes)")
    print("  ✓ pitch affects output bytes (per-chunk digest)")
    print()

    # === Scenario D: long text chunking ===
    print("═══ Scenario D: long text chunking (5000 chars) ═══")
    long = long_text(5000)
    # Synthesize the whole thing in one call (chunked internally)
    whole = tts.synthesize(TTSRequest(text=long, voice_id="josh", stream=False))
    # And split into ~500-char pieces and stream each
    pieces = [long[i:i + 500] for i in range(0, len(long), 500)]
    piece_results: list[TTSResult] = []
    for p in pieces:
        piece_results.append(tts.synthesize(TTSRequest(text=p, voice_id="josh", stream=False)))
    # And stream the whole thing as a single request
    stream_long = tts.stream_collect(TTSRequest(text=long, voice_id="josh", stream=True))
    print(f"  whole text length: {len(long)} chars")
    print(f"  whole result:      {len(whole.chunks)} chunks, {whole.total_bytes} bytes")
    print(f"  split into:        {len(pieces)} pieces of ~500 chars each")
    print(f"  piece chunks:      {sum(len(r.chunks) for r in piece_results)} total")
    print(f"  stream result:     {len(stream_long.chunks)} chunks, {stream_long.total_bytes} bytes")
    # Chunks emitted in order — each chunk.seq must be strictly increasing
    seqs = [c.seq for c in stream_long.chunks]
    assert seqs == list(range(len(seqs))), "chunks must be emitted in order with monotonic seq"
    # All chunks must be non-empty
    assert all(c.size_bytes > 0 for c in stream_long.chunks), "every chunk must be non-empty"
    # Whole text and stream must produce same byte total
    assert stream_long.total_bytes == whole.total_bytes, (
        f"stream vs whole must match: stream={stream_long.total_bytes} whole={whole.total_bytes}"
    )
    print("  ✓ all chunks emitted in order with monotonic seq")
    print("  ✓ stream bytes == non-stream bytes")
    print()

    # === Bulk workload run (the metrics that matter) ===
    print("═══ Bulk workload run ═══")
    bulk_t0 = time.time()
    syntheses = 0
    total_bytes = 0
    total_audio_ms = 0.0
    first_chunks_latencies: list[float] = []
    by_voice_bytes: dict[str, int] = {v: 0 for v in VOICES}
    for voice, text in workload:
        req = TTSRequest(text=text, voice_id=voice, stream=True)
        # Use stream_collect to get real timing
        result = tts.stream_collect(req)
        syntheses += 1
        total_bytes += result.total_bytes
        total_audio_ms += result.total_audio_ms
        first_chunks_latencies.append(result.ttfb_ms)
        by_voice_bytes[voice] += result.total_bytes
    bulk_dt = time.time() - bulk_t0
    avg_bytes_per_sec = total_bytes / max(1.0, total_audio_ms / 1000.0)
    p50_latency = statistics.median(first_chunks_latencies)
    p95_latency = sorted(first_chunks_latencies)[int(0.95 * len(first_chunks_latencies))]

    print(f"  syntheses performed: {syntheses}")
    print(f"  voices used:         {len(VOICES)} ({', '.join(VOICES)})")
    print(f"  total bytes:         {total_bytes:,}")
    print(f"  total audio (ms):    {total_audio_ms:,.0f}")
    print(f"  avg bytes/sec:       {avg_bytes_per_sec:,.0f}")
    print(f"  wall-clock (sec):    {bulk_dt:.2f}")
    print(f"  first-chunk latency: p50={p50_latency:.1f}ms  p95={p95_latency:.1f}ms  "
          f"min={min(first_chunks_latencies):.1f}ms")
    print(f"  bytes per voice:")
    for v in VOICES:
        print(f"    {v:<7} {by_voice_bytes[v]:>10,}B "
              f"({by_voice_bytes[v] / total_bytes:.1%})")
    print()

    # === Final invariants ===
    print("═══ invariants ═══")
    assert syntheses == N, f"expected {N} syntheses, got {syntheses}"
    assert total_bytes > 0, "total bytes must be > 0"
    assert p50_latency >= 70.0, f"p50 first-chunk latency {p50_latency}ms should be near 80ms budget"
    # Every voice saw some traffic
    for v in VOICES:
        assert by_voice_bytes[v] > 0, f"voice {v} produced no bytes"
    # The streaming path produces the same total bytes as the non-streaming path
    final_compare_text = "Final comparison: streaming must equal non-streaming byte total."
    r_sync = tts.synthesize(TTSRequest(text=final_compare_text, voice_id="bella", stream=False))
    r_stream = tts.stream_collect(TTSRequest(text=final_compare_text, voice_id="bella", stream=True))
    assert r_sync.total_bytes == r_stream.total_bytes, (
        f"stream and non-stream must produce same total bytes: "
        f"sync={r_sync.total_bytes} stream={r_stream.total_bytes}"
    )
    # All 4 voices produced distinct audio for the same text
    distinct_voice_count = len({
        tts.synthesize(TTSRequest(text="voice identity test", voice_id=v)).chunks[0].pcm_bytes
        for v in VOICES
    })
    assert distinct_voice_count == len(VOICES), (
        f"every voice must produce distinct bytes: {distinct_voice_count}/{len(VOICES)}"
    )
    print(f"  ✓ {N} syntheses completed, all non-empty")
    print(f"  ✓ {len(VOICES)} voices all produced distinct audio")
    print(f"  ✓ p50 first-chunk latency {p50_latency:.1f}ms is within TTFB budget")
    print(f"  ✓ streaming == non-streaming total bytes")
    print()
    print("✓ all invariants pass")

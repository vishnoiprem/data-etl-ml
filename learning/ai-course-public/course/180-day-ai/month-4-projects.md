# Month 4: AI + Files & Media — 30 Days of Hands-On Projects
### Theme: "AI for images, audio, video, PDFs at scale"

**Data system:** S3-compatible object storage + media processing
**Tools:** Python 3.10+, boto3 (S3/R2/B2), ffmpeg, openai-whisper, DALL-E, GPT-4V, Tesseract
**Setup time:** 30 min
**Time per project:** 30-90 min
**Total time:** ~28 hours over 30 days

---

## Setup (do this once, before Day 91)

```bash
mkdir ai-daily && cd ai-daily
python -m venv venv && source venv/bin/activate
pip install openai boto3 ffmpeg-python Pillow pytesseract python-dotenv streamlit

# For Whisper
pip install openai-whisper
brew install ffmpeg

# For local Stable Diffusion (Day 99)
pip install diffusers transformers torch accelerate

# AWS or Cloudflare R2
echo "AWS_ACCESS_KEY_ID=..." > .env
echo "AWS_SECRET_ACCESS_KEY=..." >> .env
echo "AWS_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com" >> .env
echo "AWS_BUCKET=my-bucket" >> .env
```

---

## Day 91: S3 File Upload with Presigned URLs (45 min)

```python
# day91_presigned_upload.py
import boto3
import os
from botocore.config import Config

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ.get("AWS_ENDPOINT_URL"),
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    config=Config(signature_version="s3v4"),
)
BUCKET = os.environ["AWS_BUCKET"]

def presigned_put(key: str, content_type: str, expires: int = 3600) -> str:
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )

def presigned_get(key: str, expires: int = 3600) -> str:
    return s3.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET, "Key": key}, ExpiresIn=expires
    )

# Demo
key = "uploads/photo.jpg"
print(f"Upload URL: {presigned_put(key, 'image/jpeg')[:80]}...")
print(f"Download URL: {presigned_get(key)[:80]}...")
```

**Stretch:** Multipart presigned URLs, max-size enforcement, content-type whitelist.
**Architect note:** Presigned URLs let clients upload directly to S3 without proxying through your server — critical for large files. Always set `ContentType` to match client uploads.

---

## Day 92: Multipart Upload for Large Files (60 min)

```python
# day92_multipart.py
import boto3
import os
from pathlib import Path

s3 = boto3.client("s3", endpoint_url=os.environ.get("AWS_ENDPOINT_URL"))
BUCKET = os.environ["AWS_BUCKET"]
PART_SIZE = 10 * 1024 * 1024  # 10 MB

def multipart_upload(local_path: str, key: str) -> str:
    file_size = Path(local_path).stat().st_size
    if file_size < PART_SIZE * 2:
        # Skip multipart for small files
        s3.upload_file(local_path, BUCKET, key)
        return f"s3://{BUCKET}/{key}"

    mpu = s3.create_multipart_upload(Bucket=BUCKET, Key=key)
    parts = []
    try:
        with open(local_path, "rb") as f:
            part_number = 1
            while True:
                data = f.read(PART_SIZE)
                if not data:
                    break
                resp = s3.upload_part(
                    Bucket=BUCKET, Key=key, PartNumber=part_number,
                    UploadId=mpu["UploadId"], Body=data,
                )
                parts.append({"PartNumber": part_number, "ETag": resp["ETag"]})
                print(f"  uploaded part {part_number} ({len(data)/1e6:.1f} MB)")
                part_number += 1
        s3.complete_multipart_upload(
            Bucket=BUCKET, Key=key, UploadId=mpu["UploadId"],
            MultipartUpload={"Parts": parts},
        )
    except Exception as e:
        s3.abort_multipart_upload(Bucket=BUCKET, Key=key, UploadId=mpu["UploadId"])
        raise
    return f"s3://{BUCKET}/{key}"

# Demo
# print(multipart_upload("big_video.mp4", "videos/big_video.mp4"))
```

**Stretch:** Parallel part uploads (5-10× faster), resumable uploads, progress callbacks.
**Architect note:** Multipart is required for files >5 GB and recommended >100 MB. S3 limits parts to 10,000 — that's 100 GB max with 10 MB parts.

---

## Day 93: Image Processing Pipeline (45 min)

```python
# day93_image_pipeline.py
from PIL import Image, ImageOps
import boto3
import os
import io
from pathlib import Path

s3 = boto3.client("s3", endpoint_url=os.environ.get("AWS_ENDPOINT_URL"))
BUCKET = os.environ["AWS_BUCKET"]

def process_image(blob: bytes) -> dict:
    img = Image.open(io.BytesIO(blob))
    original_size = len(blob)

    # Generate variants
    variants = {}
    for name, size, quality in [("thumb", (300, 300), 75),
                                 ("medium", (1024, 1024), 80),
                                 ("large", (2048, 2048), 85)]:
        v = img.copy()
        v.thumbnail(size, Image.LANCZOS)
        # Auto-orient
        v = ImageOps.exif_transpose(v)
        # Convert to RGB for JPEG
        if v.mode in ("RGBA", "P"):
            v = v.convert("RGB")
        buf = io.BytesIO()
        v.save(buf, format="JPEG", quality=quality, optimize=True)
        variants[name] = buf.getvalue()

    return {
        "original": original_size,
        "thumb": len(variants["thumb"]),
        "medium": len(variants["medium"]),
        "large": len(variants["large"]),
        "blobs": variants,
    }

def process_and_upload(key: str) -> dict:
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    result = process_image(obj["Body"].read())
    base = Path(key).stem
    for variant_name, blob in result["blobs"].items():
        s3.put_object(Bucket=BUCKET, Key=f"variants/{base}/{variant_name}.jpg", Body=blob)
    return {k: v for k, v in result.items() if k != "blobs"}

# process_and_upload("uploads/raw/photo.jpg")
```

**Stretch:** WebP/AVIF output (50% smaller than JPEG), face detection cropping, watermarking.
**Architect note:** Process images once, serve forever. CDN-cache the variants — don't re-process on every request.

---

## Day 94: Virus Scanning with ClamAV (45 min)

```bash
# Setup
docker run -d -p 3310:3310 --name clamav -v clamav_data:/var/lib/clamav clamav/clamav:latest
# Wait 5-10 min for first-time virus DB download
```

```python
# day94_virus_scan.py
import clamd
import os
import boto3

s3 = boto3.client("s3", endpoint_url=os.environ.get("AWS_ENDPOINT_URL"))
BUCKET = os.environ["AWS_BUCKET"]

def scan_bytes(blob: bytes) -> dict:
    cd = clamd.ClamdNetworkSocket(host="localhost", port=3310, timeout=120)
    result = cd.instream(blob)
    stream = list(result["stream"].values())[0]
    return {
        "clean": stream[0] == "OK",
        "status": stream[0],
        "signature": stream[1] if stream[0] != "OK" else None,
    }

def safe_upload(key: str, body: bytes, content_type: str) -> dict:
    scan = scan_bytes(body)
    if not scan["clean"]:
        return {"uploaded": False, "reason": f"virus: {scan['signature']}"}
    s3.put_object(Bucket=BUCKET, Key=key, Body=body, ContentType=content_type)
    return {"uploaded": True, "scan": scan}

# Demo
# print(safe_upload("uploads/test.pdf", open("test.pdf", "rb").read(), "application/pdf"))
```

**Stretch:** Quarantine bucket, async scanning worker, EICAR test file, scan in worker (don't block upload).
**Architect note:** Never trust user uploads. Scan in an async worker (SQS + Lambda), not synchronously in the upload path.

---

## Day 95: CDN Integration (45 min)

```python
# day95_cdn.py
import boto3
import os

s3 = boto3.client("s3", endpoint_url=os.environ.get("AWS_ENDPOINT_URL"))
BUCKET = os.environ["AWS_BUCKET"]
CDN_DOMAIN = os.environ.get("CDN_DOMAIN", "cdn.example.com")  # CloudFront or R2 public domain

def cdn_url(key: str) -> str:
    return f"https://{CDN_DOMAIN}/{key}"

def setup_cache_policy(prefix: str = "variants/*", ttl: int = 31536000):
    """Configure S3 lifecycle for variant cache (1 year immutable)."""
    s3.put_bucket_lifecycle_configuration(
        Bucket=BUCKET,
        LifecycleConfiguration={
            "Rules": [{
                "ID": "cache-variants",
                "Status": "Enabled",
                "Filter": {"Prefix": prefix},
                "Expiration": {"Days": 365},
                "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}],
            }],
        },
    )

def purge_cache(paths: list[str]):
    """Call CDN API to invalidate. CloudFront: CreateInvalidation. R2: not needed (purge on demand)."""
    cf = boto3.client("cloudfront")
    cf.create_invalidation(
        DistributionId=os.environ["CLOUDFRONT_ID"],
        InvalidationBatch={
            "Paths": {"Quantity": len(paths), "Items": paths},
            "CallerReference": str(os.urandom(8).hex()),
        },
    )
```

**Stretch:** Multi-CDN failover, signed URLs for private content, regional edge caching.
**Architect note:** The CDN cache TTL is your worst-case staleness. For user uploads, set `Cache-Control: max-age=0, must-revalidate` so the next request hits S3.

---

## Day 96: File Metadata + Tagging (45 min)

```python
# day96_metadata.py
import boto3
import os
import json
from datetime import datetime

s3 = boto3.client("s3", endpoint_url=os.environ.get("AWS_ENDPOINT_URL"))
BUCKET = os.environ["AWS_BUCKET"]

def tag_object(key: str, tags: dict[str, str]):
    s3.put_object_tagging(
        Bucket=BUCKET, Key=key,
        Tagging={"TagSet": [{"Key": k, "Value": v} for k, v in tags.items()]},
    )

def list_by_tag(tag_key: str, tag_value: str) -> list[str]:
    resp = s3.get_object_tagging(Bucket=BUCKET, Key=key) if False else None
    # Use S3 Inventory or ListObjectsV2 + GetObjectTagging (slow at scale)
    # Better: maintain a metadata table in Postgres
    paginator = s3.get_paginator("list_objects_v2")
    matches = []
    for page in paginator.paginate(Bucket=BUCKET):
        for obj in page.get("Contents", []):
            tags = s3.get_object_tagging(Bucket=BUCKET, Key=obj["Key"])["TagSet"]
            tag_map = {t["Key"]: t["Value"] for t in tags}
            if tag_map.get(tag_key) == tag_value:
                matches.append(obj["Key"])
    return matches

def set_custom_metadata(key: str, metadata: dict):
    s3.copy_object(
        Bucket=BUCKET, Key=key,
        CopySource={"Bucket": BUCKET, "Key": key},
        Metadata=metadata, MetadataDirective="REPLACE",
    )

# Demo
# tag_object("uploads/photo.jpg", {"user_id": "u_123", "type": "avatar", "uploaded_at": str(int(datetime.now().timestamp()))})
```

**Stretch:** S3 Inventory + Athena for tag queries, lifecycle hooks to Postgres.
**Architect note:** S3 tags are limited to 10 per object. For complex metadata, use a separate metadata store (Postgres) and S3 for the bytes only.

---

## Day 97: WEEKEND — File Upload Service (3 hours)

Build a production file upload service:
- FastAPI + presigned URLs (Day 91)
- Image processing pipeline (Day 93) on upload
- Virus scan (Day 94) async
- Metadata in Postgres
- CDN delivery
- Auth (JWT)
- Rate limit (per user)
- Webhook on processing complete
- Deploy to Fly.io

**Architect note:** The hardest part of a file service is the *async coordination*: upload completes → virus scan → process → notify. Use a state machine (Step Functions or a simple DB-backed queue).

---

## Day 98: DALL-E 3 Image Generation (30 min)

```python
# day98_dalle.py
from openai import OpenAI
import httpx
import os

client = OpenAI()

def generate(prompt: str, size: str = "1024x1024", quality: str = "standard", n: int = 1) -> list[str]:
    resp = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,  # 1024x1024, 1792x1024, 1024x1792
        quality=quality,  # "standard" or "hd"
        n=n,
    )
    return [d.url for d in resp.data]

def download_and_save(url: str, path: str):
    r = httpx.get(url, timeout=30)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    return path

# Demo
urls = generate("A futuristic Tokyo street at night, neon lights, rain, cinematic")
for u in urls:
    print(u)
    download_and_save(u, "tokyo.png")
```

**Stretch:** Prompt refinement with GPT-4V before generation, style presets, batch generation for A/B tests.
**Architect note:** DALL-E 3 doesn't support seed control — for reproducible images, use a different model (SDXL, Flux). For brand consistency, fine-tune a model on your assets.

---

## Day 99: Stable Diffusion (Local) (60 min)

```python
# day99_sd_local.py
import torch
from diffusers import StableDiffusionXLPipeline

# First run: downloads ~7 GB
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16",
    use_safetensors=True,
).to("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")

def generate(prompt: str, negative: str = "", steps: int = 30, seed: int = None) -> "PIL.Image":
    generator = torch.Generator(device=pipe.device).manual_seed(seed) if seed else None
    return pipe(
        prompt=prompt,
        negative_prompt=negative or "blurry, low quality, distorted",
        num_inference_steps=steps,
        generator=generator,
    ).images[0]

# Demo
img = generate("a corgi wearing a tiny space suit, digital art", seed=42)
img.save("cogi.png")
```

**Stretch:** LoRA fine-tuning on your own images, ControlNet for pose/depth control, inpainting.
**Architect note:** SDXL needs ~10 GB VRAM. For M-series Macs, use `torch.float16` and `mps` backend. Cloud alternative: Replicate ($0.005/image).

---

## Day 100: GPT-4V Image Understanding (45 min)

```python
# day100_gpt4v.py
from openai import OpenAI
import base64
import httpx

client = OpenAI()

def image_to_b64(url: str) -> str:
    return base64.b64encode(httpx.get(url).content).decode()

def analyze(image_path: str, question: str = "What's in this image?") -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ],
        }],
        max_tokens=500,
    )
    return resp.choices[0].message.content

print(analyze("photo.jpg", "How many people are in this image and what are they doing?"))
```

**Stretch:** Multi-image comparison, OCR from images, structured output (JSON).
**Architect note:** GPT-4V is great but expensive ($0.01/image at low res). For high-volume, pre-filter with a small vision model or use CLIP embeddings.

---

## Day 101: Image Similarity Search with CLIP (60 min)

```python
# day101_clip.py
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def embed_image(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        emb = model.get_image_features(**inputs)
    return emb[0].numpy() / np.linalg.norm(emb[0].numpy())  # L2 normalize

def embed_text(text: str) -> np.ndarray:
    inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        emb = model.get_text_features(**inputs)
    return emb[0].numpy() / np.linalg.norm(emb[0].numpy())

def search(query: str, image_db: list[tuple[str, np.ndarray]], k: int = 5) -> list[tuple[str, float]]:
    qvec = embed_text(query)
    scores = [(path, float(np.dot(qvec, ivec))) for path, ivec in image_db]
    return sorted(scores, key=lambda x: -x[1])[:k]

# Build a small index
import os
db = []
for fname in os.listdir("images")[:20]:
    if fname.endswith((".jpg", ".png")):
        db.append((fname, embed_image(f"images/{fname}")))

for path, score in search("a sunset over the ocean", db):
    print(f"{score:.3f}  {path}")
```

**Stretch:** Pre-compute embeddings for the whole library, FAISS index for fast search, multi-modal queries (image+text).
**Architect note:** CLIP is the *lingua franca* of image embeddings. Same vector space for text and image means text-to-image and image-to-image search both work.

---

## Day 102: Image Captioning (45 min)

```python
# day102_caption.py
from openai import OpenAI
import base64
from PIL import Image
import io

client = OpenAI()

def caption(image_path: str, style: str = "descriptive", max_length: int = 200) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": f"Write a {style} caption for this image. Max {max_length} chars. No preamble."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ],
        }],
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()

# Demo
print(caption("photo.jpg", style="instagram-caption"))
print(caption("photo.jpg", style="alt-text-for-accessibility"))
```

**Stretch:** Per-style fine-tuned models, multi-language captions, SEO-keyword captions.
**Architect note:** "Alt text for accessibility" is a great forcing function for caption quality — it makes the model describe *what's actually in the image* rather than make up stories.

---

## Day 103: Object Detection with YOLO (60 min)

```bash
pip install ultralytics
```

```python
# day103_yolo.py
from ultralytics import YOLO
import json

# First run: downloads yolov8n.pt (~6 MB)
model = YOLO("yolov8n.pt")

def detect(image_path: str) -> list[dict]:
    results = model(image_path, verbose=False)
    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                "class": model.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": [float(x) for x in box.xyxy[0]],  # [x1, y1, x2, y2]
            })
    return detections

# Demo
print(json.dumps(detect("street.jpg"), indent=2))

# Save annotated image
results = model("street.jpg")
results[0].save(filename="annotated.jpg")
```

**Stretch:** Custom-trained YOLO on your domain (e.g., product defects), tracking across video frames.
**Architect note:** YOLOv8n is fast (50ms/image on GPU). For 100+ FPS on a single GPU, use TensorRT export. For >10 classes, fine-tune.

---

## Day 104: WEEKEND — Visual Search App (3 hours)

Build a visual search app:
- Upload an image (Streamlit)
- Embed with CLIP
- Search your indexed library
- Display top-K similar images
- Add text-to-image search too
- Deploy to Streamlit Cloud

**Architect note:** Visual search works best for products, art, fashion, and design. The hardest problem is *indexing* — pre-compute embeddings for the whole library ahead of time.

---

## Day 105: Whisper Transcription (30 min)

```bash
pip install openai-whisper
brew install ffmpeg
```

```python
# day105_whisper.py
import whisper
import os

# Models: tiny, base, small, medium, large
model = whisper.load_model("base")

def transcribe(audio_path: str, language: str = None) -> dict:
    return model.transcribe(
        audio_path,
        language=language,  # None = auto-detect
        task="transcribe",  # or "translate" (to English)
        verbose=False,
    )

# Demo
result = transcribe("interview.mp3")
print(f"Detected language: {result['language']}")
print(f"Text: {result['text'][:300]}")
for seg in result["segments"][:5]:
    print(f"  [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")
```

**Stretch:** Word-level timestamps, translation to English, batch transcribe a folder.
**Architect note:** `base` is fast but ~7% WER. `large-v3` is best but 10× slower. For production, use `whisper-large-v3-turbo` or OpenAI's API ($0.006/minute).

---

## Day 106: Speaker Diarization (45 min)

```bash
pip install pyannote.audio
# Get a HuggingFace token and accept the model terms
```

```python
# day106_diarization.py
from pyannote.audio import Pipeline
import os

# Auth
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=os.environ["HF_TOKEN"],
)

def diarize(audio_path: str) -> list[dict]:
    diarization = pipeline(audio_path)
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "speaker": speaker,
            "start": turn.start,
            "end": turn.end,
        })
    return segments

# Demo
import whisper
whisper_model = whisper.load_model("base")

def transcribe_with_speakers(audio_path: str) -> list[dict]:
    asr = whisper_model.transcribe(audio_path, verbose=False)
    diar = diarize(audio_path)
    # Align segments to speakers
    output = []
    for seg in asr["segments"]:
        mid = (seg["start"] + seg["end"]) / 2
        speaker = "UNKNOWN"
        for d in diar:
            if d["start"] <= mid <= d["end"]:
                speaker = d["speaker"]
                break
        output.append({**seg, "speaker": speaker})
    return output
```

**Stretch:** Speaker enrollment (known speakers), emotion detection per segment, multi-language.
**Architect note:** pyannote needs GPU for real-time. For CPU, batch process 5-10× realtime. Speaker labels are anonymous by default — link them to names via enrollment.

---

## Day 107: Real-Time Transcription (60 min)

```python
# day107_realtime.py
import pyaudio
import numpy as np
import whisper
import queue
import threading

model = whisper.load_model("base")
CHUNK_SECONDS = 3
RATE = 16000
CHUNK = RATE * CHUNK_SECONDS
audio_q = queue.Queue()

def audio_callback(in_data, frame_count, time_info, status):
    audio_q.put(np.frombuffer(in_data, np.int16).astype(np.float32) / 32768.0)
    return (None, pyaudio.paContinue)

def transcriber():
    while True:
        audio = audio_q.get()
        if len(audio) < RATE:  # skip short
            continue
        # Pad or trim to 30s
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        _, probs = model.detect_language(mel)
        options = whisper.DecodingOptions(language=max(probs, key=probs.get), fp16=False)
        result = whisper.decode(model, mel, options)
        print(f"[{max(probs, key=probs.get)}] {result.text}")

def main():
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                     frames_per_buffer=CHUNK, stream_callback=audio_callback)
    threading.Thread(target=transcriber, daemon=True).start()
    print("Listening... (Ctrl-C to stop)")
    stream.start_stream()
    while stream.is_active():
        pass

# main()
```

**Stretch:** VAD (voice activity detection) to skip silence, rolling buffer for context, hotword detection.
**Architect note:** Real-time Whisper is hard on CPU. Use `whisper-streaming` for production, or stream to OpenAI's API with WebSocket.

---

## Day 108: Audio Embeddings (45 min)

```python
# day108_audio_embed.py
from transformers import ClapModel, ClapProcessor
import torch
import numpy as np
import librosa

model = ClapModel.from_pretrained("laion/larger_clap_music_and_speech")
processor = ClapProcessor.from_pretrained("laion/larger_clap_music_and_speech")

def embed_audio(path: str) -> np.ndarray:
    audio, sr = librosa.load(path, sr=48000)
    inputs = processor(audios=[audio], sampling_rate=48000, return_tensors="pt")
    with torch.no_grad():
        emb = model.get_audio_features(**inputs)
    return emb[0].numpy() / np.linalg.norm(emb[0].numpy())

def embed_query(text: str) -> np.ndarray:
    inputs = processor(text=[text], return_tensors="pt", padding=True)
    with torch.no_grad():
        emb = model.get_text_features(**inputs)
    return emb[0].numpy() / np.linalg.norm(emb[0].numpy())

# Demo
audio_db = [("song1.mp3", embed_audio("song1.mp3")),
            ("podcast1.mp3", embed_audio("podcast1.mp3"))]
qvec = embed_query("upbeat electronic music")
scores = sorted([(p, float(np.dot(qvec, v))) for p, v in audio_db], key=lambda x: -x[1])
print(scores[0])
```

**Stretch:** Index 10K+ audio files with FAISS, music recommendation engine, sound-effect library search.
**Architect note:** CLAP (Contrastive Language-Audio Pretraining) is to audio what CLIP is to images — same vector space for text and audio. Magical for search.

---

## Day 109: Text-to-Speech (30 min)

```python
# day109_tts.py
from openai import OpenAI
import os

client = OpenAI()

def tts(text: str, voice: str = "alloy", output: str = "speech.mp3") -> str:
    """OpenAI TTS. Voices: alloy, echo, fable, onyx, nova, shimmer."""
    resp = client.audio.speech.create(
        model="tts-1",  # or "tts-1-hd"
        voice=voice,
        input=text,
    )
    resp.stream_to_file(output)
    return output

# Demo
tts("The quick brown fox jumps over the lazy dog. Welcome to the AI Daily course.", voice="nova")
```

**Stretch:** Streaming TTS (chunk by sentence), SSML for prosody, voice cloning with consent (Day 110).
**Architect note:** `tts-1` is fast, `tts-1-hd` is higher quality. For sub-200ms response in voice agents, stream the response in 100ms chunks.

---

## Day 110: Voice Cloning (with consent) (60 min)

```python
# day110_voice_clone.py
import os
from openai import OpenAI
import httpx

# Note: requires explicit consent and a verified use case.
# OpenAI's voice cloning is part of their Realtime API.

client = OpenAI()

def clone_voice(reference_audio_path: str, name: str) -> str:
    """Upload a reference clip. Returns a voice_id."""
    # OpenAI's TTS doesn't expose voice cloning via the public API.
    # This example uses ElevenLabs (paid) for legitimate use cases.
    api_key = os.environ["ELEVENLABS_API_KEY"]
    with open(reference_audio_path, "rb") as f:
        r = httpx.post(
            "https://api.elevenlabs.io/v1/voices/add",
            headers={"xi-api-key": api_key},
            data={"name": name},
            files={"files": ("sample.mp3", f, "audio/mpeg")},
        )
    r.raise_for_status()
    return r.json()["voice_id"]

def speak(voice_id: str, text: str, output: str = "out.mp3"):
    r = httpx.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
        json={"text": text, "model_id": "eleven_multilingual_v2"},
    )
    r.raise_for_status()
    with open(output, "wb") as f:
        f.write(r.content)

# IMPORTANT: only clone voices you have explicit written consent for.
# vid = clone_voice("my_consented_voice.mp3", "Personal Assistant")
# speak(vid, "Hello, this is my AI assistant.")
```

**Stretch:** Coqui XTTS (open-source), So-VITS-SVC, consent verification flow.
**Architect note:** Voice cloning is a dual-use technology. Production systems MUST verify consent (audio consent, written permission) and add watermarking to detect synthetic speech.

---

## Day 111: WEEKEND — Podcast Search Engine (3 hours)

Build a podcast search engine:
- RSS feed parser
- Download episodes
- Transcribe with Whisper
- Embed with CLAP
- Hybrid search (BM25 + CLAP)
- Web UI with audio snippets
- Deploy to Streamlit Cloud

**Architect note:** "Podcast search" is a great use case because transcripts are *valuable* (text is searchable) but *not natively searchable* (no auto-transcripts for many shows).

---

## Day 112: Video Frame Extraction (45 min)

```python
# day112_video_frames.py
import ffmpeg
import os
from pathlib import Path

def extract_frames(video_path: str, output_dir: str, fps: int = 1) -> int:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    stream = ffmpeg.input(video_path)
    stream = ffmpeg.output(stream, f"{output_dir}/frame_%05d.jpg", vf=f"fps={fps}")
    ffmpeg.run(stream, overwrite_output=True, quiet=True)
    return len(list(Path(output_dir).glob("*.jpg")))

def extract_at_timestamps(video_path: str, timestamps: list[float], output_dir: str):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for i, t in enumerate(timestamps):
        stream = ffmpeg.input(video_path, ss=t)
        stream = ffmpeg.output(stream, f"{output_dir}/frame_{i:03d}.jpg", vframes=1)
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

# Demo
# count = extract_frames("video.mp4", "frames/", fps=1)  # 1 frame per second
# print(f"Extracted {count} frames")
```

**Stretch:** Scene-based extraction (only key frames), batch processing, video metadata extraction.
**Architect note:** 1 FPS is a good default for scene detection. For dense tasks (e.g., sports analysis), use 10-30 FPS. Compress to 720p before extraction to save disk.

---

## Day 113: Video Scene Detection (45 min)

```bash
pip install scenedetect
```

```python
# day113_scene_detect.py
from scenedetect import open_video, SceneManager, ContentDetector
from scenedetect.stats_manager import StatsManager
import os

def detect_scenes(video_path: str, threshold: float = 27.0) -> list[tuple[float, float]]:
    video = open_video(video_path)
    stats = StatsManager()
    sm = SceneManager(stats)
    sm.add_detector(ContentDetector(threshold=threshold))
    sm.detect_scenes(video)
    return [(s.get_seconds(), e.get_seconds()) for s, e in sm.get_scene_list()]

# Demo
# scenes = detect_scenes("video.mp4", threshold=20)
# for start, end in scenes[:10]:
#     print(f"  {start:.1f}s - {end:.1f}s ({end-start:.1f}s)")
```

**Stretch:** Per-scene thumbnail, key-frame extraction, scene classification (action/dialogue/landscape).
**Architect note:** Threshold ~27 is a good default. Lower = more sensitive (more scenes). For "talking head" videos, raise to 35-40 to avoid splitting on micro-expressions.

---

## Day 114: Video Summarization (60 min)

```python
# day114_video_summary.py
import os
from openai import OpenAI
from pathlib import Path
from day113_scene_detect import detect_scenes
from day112_video_frames import extract_frames

client = OpenAI()

def summarize_video(video_path: str) -> str:
    # Step 1: detect scenes
    scenes = detect_scenes(video_path)
    print(f"Found {len(scenes)} scenes")

    # Step 2: extract a key frame from each scene (midpoint)
    frame_dir = "frames"
    Path(frame_dir).mkdir(exist_ok=True)
    frame_paths = []
    for i, (start, end) in enumerate(scenes):
        mid = (start + end) / 2
        # Use ffmpeg to extract
        import ffmpeg
        out = f"{frame_dir}/scene_{i:03d}.jpg"
        ffmpeg.input(video_path, ss=mid).output(out, vframes=1).run(quiet=True, overwrite_output=True)
        frame_paths.append(out)

    # Step 3: describe each frame
    descriptions = []
    for path in frame_paths:
        with open(path, "rb") as f:
            import base64
            b64 = base64.b64encode(f.read()).decode()
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this video frame in 1 sentence. Focus on what's happening."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }],
            max_tokens=100,
        )
        descriptions.append(resp.choices[0].message.content)

    # Step 4: synthesize summary
    summary = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Write a 3-paragraph summary of this video based on these scene descriptions:\n\n" +
                       "\n".join(f"Scene {i}: {d}" for i, d in enumerate(descriptions)),
        }],
    )
    return summary.choices[0].message.content

# print(summarize_video("video.mp4"))
```

**Stretch:** Audio transcript + frame descriptions combined, chapter markers, highlight reel.
**Architect note:** Combining audio transcript with frame descriptions gives 2-3× better summaries than either alone. Always do both.

---

## Day 115: PDF Table Extraction (45 min)

```python
# day115_pdf_table.py
import pdfplumber
import pandas as pd

def extract_tables(pdf_path: str) -> list[pd.DataFrame]:
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            for j, table in enumerate(page.extract_tables()):
                if table:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    df.attrs["page"] = i + 1
                    df.attrs["table_index"] = j
                    tables.append(df)
    return tables

# Demo
# for t in extract_tables("report.pdf"):
#     print(f"\n=== Page {t.attrs['page']}, Table {t.attrs['table_index']} ===")
#     print(t.head())
```

**Stretch:** Per-table LLM cleanup, multi-page table merging, CSV export.
**Architect note:** `pdfplumber` is great for clean, well-structured tables. For scanned PDFs, you need OCR + structure recognition (e.g., `olmocr`).

---

## Day 116: PDF Figure/Chart Extraction (60 min)

```python
# day116_pdf_figure.py
import fitz  # PyMuPDF
import os
from pathlib import Path

def extract_images(pdf_path: str, output_dir: str = "images", min_size: int = 100) -> list[dict]:
    doc = fitz.open(pdf_path)
    Path(output_dir).mkdir(exist_ok=True)
    images = []
    for page_num, page in enumerate(doc):
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            try:
                base = doc.extract_image(xref)
                if base["width"] < min_size or base["height"] < min_size:
                    continue
                ext = base["ext"]
                path = f"{output_dir}/p{page_num+1}_i{img_index}.{ext}"
                with open(path, "wb") as f:
                    f.write(base["image"])
                images.append({
                    "path": path, "page": page_num + 1,
                    "width": base["width"], "height": base["height"],
                })
            except Exception:
                continue
    return images

def extract_charts_as_images(pdf_path: str, output_dir: str = "charts") -> list[str]:
    """Render each page that contains a chart and save as image."""
    doc = fitz.open(pdf_path)
    Path(output_dir).mkdir(exist_ok=True)
    paths = []
    for page_num, page in enumerate(doc):
        # Heuristic: pages with figure objects
        if page.get_drawings():
            pix = page.get_pixmap(dpi=150)
            path = f"{output_dir}/p{page_num+1}.png"
            pix.save(path)
            paths.append(path)
    return paths

# extract_images("report.pdf")
# extract_charts_as_images("report.pdf")
```

**Stretch:** GPT-4V to caption each chart, structured data extraction from charts.
**Architect note:** Charts are hard — there are no easy OCR for "the bar at 30% on Tuesday." Use GPT-4V on rendered images.

---

## Day 117: Form Parsing (PDF → JSON) (60 min)

```python
# day117_form_parse.py
import fitz
import json
import re
from openai import OpenAI

client = OpenAI()

def extract_form_fields(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    fields = []
    for page in doc:
        for widget in page.widgets() or []:
            fields.append({
                "page": page.number + 1,
                "type": widget.field_type_string,
                "name": widget.field_name,
                "value": widget.field_value,
                "rect": list(widget.rect),
            })
    return fields

def parse_form_with_llm(pdf_path: str, schema_hint: str = "") -> dict:
    """For non-fillable PDFs: render + LLM extract."""
    doc = fitz.open(pdf_path)
    results = []
    for page_num, page in enumerate(doc):
        pix = page.get_pixmap(dpi=200)
        import base64
        b64 = base64.b64encode(pix.tobytes("png")).decode()
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Extract all form fields and values as JSON: {schema_hint}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }],
            response_format={"type": "json_object"},
        )
        results.append(json.loads(resp.choices[0].message.content))
    return {"pages": results}
```

**Stretch:** Auto-fill forms, multi-page form assembly, validation against schema.
**Architect note:** Native form fields (Day 117) are 100× cheaper than LLM extraction. Always check `page.widgets()` first.

---

## Day 118: WEEKEND — Document Automation Tool (3 hours)

Build an invoice processing tool:
- Upload PDF invoices
- Extract fields (vendor, amount, date, line items) using GPT-4V
- Validate against expected schema
- Push to accounting system (e.g., QuickBooks API or just CSV)
- Audit log + approval queue
- Deploy to Fly.io

**Architect note:** Invoice processing is the #1 ROI AI use case for SMBs. A 95% accuracy is worth $50K/year for a mid-sized company.

---

## Day 119: Polish + Cost Analysis (60 min)

Take the audio/video pipeline:
- Cost per minute of audio (Whisper API vs local)
- Cost per frame (GPT-4V)
- Cost per chunk (embedding)
- Throughput (frames/sec on your hardware)
- Latency (time to first result)
- Document the cost in a `COSTS.md` file

**Architect note:** A pipeline without cost analysis is a prototype. Production teams track cost per document/request religiously.

---

## Day 120: MONTH PROJECT — Media Processing Pipeline (6 hours)

**Goal:** End-to-end media processing pipeline.

**Spec:**
- Upload endpoint (audio/video/PDF)
- Whisper transcription (audio)
- GPT-4V frame analysis (video)
- PDF text + table extraction
- LLM-generated summary
- Index in Elasticsearch
- Webhook notification on completion
- Web UI for browsing results
- Cost tracking per file
- Deploy to Fly.io + R2

**Architect note:** This is the "unstructured data platform" pattern. Every company has 10s of TBs of this stuff. Whoever processes it first wins.

---

## Month 4 Summary

**Built:** 30 projects · 1 file service · 1 image generation suite · 1 audio pipeline · 1 video pipeline
**Time:** ~32 hours over 30 days
**Cost:** ~$25 (image gen is expensive)

**Key skills learned:**
- S3/R2/CloudFront (uploads, multipart, CDN)
- Image AI (DALL-E, CLIP, GPT-4V, YOLO)
- Audio AI (Whisper, CLAP, TTS, voice cloning)
- Video AI (frame extraction, scene detection, summarization)
- PDF AI (table extraction, form parsing, chart extraction)
- Cost analysis for media pipelines

**Next:** Month 5 — AI + Real-Time Streams. 30 projects on Kafka, Redis Streams, RabbitMQ, and event-driven AI.

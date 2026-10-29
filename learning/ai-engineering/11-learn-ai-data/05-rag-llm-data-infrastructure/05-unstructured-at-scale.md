# Lesson 5 — Unstructured at Scale

> **Type:** Article · Module 5 · RAG & LLM Data Infrastructure
> Processing PDFs, images, audio, and HTML at billion-doc scale.

---

## The 80% problem

Most enterprise data is **unstructured**: PDFs, images, audio, slide decks, scanned forms. Most RAG pipelines handle text. **Bridging that gap is the difference between "works on the demo" and "works on the company."**

```
   ENTERPRISE DATA MIX (2026)
   ─────────────────────────
   PDFs / scans        ████████████████  ~50%
   Office docs (Word, PPT, Excel)   ███████     ~25%
   Images (PNG, JPG)              ███          ~10%
   Audio / video                  ██            ~7%
   HTML / web                     █              ~5%
   Plain text / structured         █              ~3%
```

If your RAG only handles the last 3%, you serve 3% of the company's questions.

---

## The architecture: a multimodal ingest pipeline

```
   source bytes
        │
        ▼
   ┌─────────────┐
   │  Type       │  PDF / image / audio / video / HTML
   │  Detect     │
   └──────┬──────┘
          │
   ┌───────┴────────────────────────────────┐
   │                                        │
   ▼                                        ▼
┌─────────────┐                     ┌──────────────┐
│ ParsePDF    │                     │ Vision-LLM   │
│ (text +OCR) │                     │ (image → text)│
└──────┬──────┘                     └──────┬───────┘
       │                                  │
       └──────────────┬───────────────────┘
                      ▼
              ┌──────────────┐
              │  Chunk       │
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │  Embed       │
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │  Vector DB   │
              └──────────────┘
```

The new piece is the **type router** + per-type parsers. The rest is unchanged.

---

## PDF parsing

### The naive approach (text only)
```python
import pypdf
reader = pypdf.PdfReader("doc.pdf")
text = "\n".join(page.extract_text() for page in reader.pages)
```

**Fails on:** scanned PDFs, complex layouts, tables, charts, multi-column text.

### The structured-parsing approach

```python
import pdfplumber

with pdfplumber.open("doc.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        tables = page.extract_tables()
        for table in tables:
            text += "\n" + markdown_table(table)
```

Preserves tables. Still fails on scanned PDFs.

### The OCR approach
```python
import pytesseract
from PIL import Image

# Convert each page to image, OCR
images = pdf_to_images("doc.pdf")
text = "\n".join(pytesseract.image_to_string(img) for img in images)
```

Works on scans. Slow. Loses structure.

### The vendor approach (best in 2026)
- **AWS Textract** — excellent OCR + table extraction + form understanding
- **Google Document AI** — same with better handwriting
- **Azure Document Intelligence** (formerly Form Recognizer)
- **Unstructured.io** — open-source + managed, multi-format
- **LandingAI** — visual document understanding

```python
# Textract example
response = textract.analyze_document(
    Document={"S3Object": {"Bucket": "docs", "Name": "key"}},
    FeatureTypes=["TABLES", "FORMS", "LAYOUT"],
)
text = extract_text_from_blocks(response["Blocks"])
tables = extract_tables_from_blocks(response["Blocks"])
```

Cost: ~$1.50 per 1000 pages. Quality: production-grade.

---

## Image parsing (vision LLMs)

For images in isolation or as part of documents:

```python
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": [
            {"type": "text", "text": "Describe this image in detail, "
                                     "including any text, charts, or data shown."},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]},
    ],
)
description = response.choices[0].message.content
```

Then embed the **description**, not the raw image. Optionally also embed the image with a CLIP-style model for visual similarity search.

**Alternatives:**
- **CLIP** for cross-modal embedding (text ↔ image)
- **Cohere `embed-v3`** supports text, image, audio
- **Google Vertex AI** vision embeddings

---

## Audio / video

### Transcription first
```python
import openai
transcript = openai.audio.transcriptions.create(
    model="whisper-1",
    file=open("call.mp3", "rb"),
    response_format="verbose_json",  # includes timestamps
)

# transcript has segments with start, end, text
for segment in transcript.segments:
    chunk = {
        "text": segment.text,
        "start_time": segment.start,
        "end_time": segment.end,
        "speaker": segment.get("speaker", "unknown"),  # with diarization
    }
    # embed + upsert
```

**Whisper**, **AssemblyAI**, **Deepgram** — all production-grade. Add **speaker diarization** for multi-person audio.

### Time-stamped chunks
For long audio, chunk by time (e.g. 30-second windows) and keep timestamps as metadata. Lets the LLM cite "at 4:32 in the call, ..."

### Video
For video, transcribe the audio track, extract keyframes, OCR the frames, treat as a multimodal document.

---

## HTML parsing

```python
import trafilatura

text = trafilatura.extract(html_content)
# clean text, no boilerplate, preserves semantic structure
```

Trafilatura > BeautifulSoup for content extraction. Strips ads, nav, footers automatically.

For structured data (JSON-LD, microdata):
```python
from extruct import extract
metadata = extract(html_content)
# includes Schema.org, OpenGraph, microdata, RDFa
```

---

## The "extraction pipeline" pattern

```
   source bytes
        │
        ▼
   ┌────────────────┐
   │ type_router.py │  sniff mime, dispatch
   └────────┬───────┘
            │
   ┌────────┼─────────────────┬───────────────┐
   ▼        ▼                 ▼               ▼
 PDF      image              audio           html
 (Textract) (vision-LLM)    (Whisper)       (trafilatura)
   │        │                 │               │
   ▼        ▼                 ▼               ▼
   structure-aware parsed content with metadata
            │
            ▼
   ┌────────────────┐
   │ chunker        │  structure-aware
   └────────┬───────┘
            │
            ▼
   ┌────────────────┐
   │ embedder       │
   └────────┬───────┘
            │
            ▼
   vector DB
```

Each parser is a **swappable adapter**. The router dispatches by file type. The chunker/embedder are shared.

---

## The "scale" considerations

### OCR cost
- 1M pages × $1.50/1000 = $1500 just for OCR
- Cache aggressively — re-OCR only on document change
- Use async batch APIs for non-urgent pipelines

### Vision LLM cost
- GPT-4o vision: ~$0.00255 per image (1024×1024)
- 1M images = $2550
- Sample / summarise before embedding if cost matters

### Storage
- Originals in S3 (cheap, slow)
- Parsed text in Parquet (fast, queryable)
- Embeddings in vector DB (fast, sparse)
- Three-tier: original → parsed → embedded

### Throughput
- Textract: 1000 pages / minute / region
- Whisper: ~1× realtime (60 min of audio = 60 min of compute)
- Plan for parallel workers; use async APIs.

---

## The "multimodal embedding" story

Some use cases want **search across modalities**: "find the slide that looks like this image and talks about X."

```
   TEXT  ─────► embed ─────► vector
   IMAGE ─────► embed ─────► vector  (CLIP, Cohere, Voyage multimodal)
   AUDIO ─────► transcribe + embed
   VIDEO ─────► frames + transcribe + embed

   All in the SAME vector space → cross-modal search
```

In 2026, **CLIP** (text ↔ image) is mature. Audio↔text via Whisper is the standard. Video↔text is early.

---

## The "what AI can do" for unstructured

AI handles:
- Vision-based parsing (no human-tuned rules)
- Transcription with timestamps
- Multilingual content (Whisper handles 99 languages)
- Diagram / chart interpretation (GPT-4o)

AI doesn't handle:
- Perfect table extraction (still ~95%, not 100%)
- Handwriting recognition at high accuracy
- Scanned image quality issues (degradation upstream)
- Industry-specific forms (still needs fine-tuning)

---

## What Comes Next

> Lesson 6 — **LLM Frameworks** — when to use LangChain, LlamaIndex, Haystack, or roll your own. The 2026 state of orchestration.

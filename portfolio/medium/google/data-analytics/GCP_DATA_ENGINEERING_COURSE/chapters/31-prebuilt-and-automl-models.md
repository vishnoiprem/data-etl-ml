# 8.2 — Prebuilt & AutoML Models

> **Section 8 · ML on GCP & Capstone · Lecture 8.2 · 8:00**

## 🎯 What you will learn

- The fastest path to production value: **a pre-trained API**, not a trained model
- The **pre-trained API family** and what each one actually does
  - **Vision API** — label detection, OCR, face detection, document analysis, image moderation
  - **Natural Language API** — entity analysis, sentiment, syntax, content classification, translation
  - **Speech-to-Text** — the streaming vs batch distinction, and why streaming latency is a design constraint
  - **Translation API (Advanced)** — and why it is a different product from the NLP translation feature
  - **Video Intelligence** — the streaming variant that most people miss
- The **AutoML family**: AutoML Vision, AutoML Natural Language, AutoML Tables, and the **Edge** variants
- For each: **what it does**, **when to reach for it**, **the cost model**, and **the honest limits**
- Why **the cost model of a pre-trained API is per-unit, not per-training** — and why that changes the break-even calculation entirely
- The decision framework: pre-trained API → AutoML → custom training → BigQuery ML
- Where these APIs sit in a **data pipeline**, and the architectural pattern for using them at scale

---

## 🧠 Concept

### The fastest path to value

Before any discussion of model architecture, a strategic point:

> **A pre-trained API gives you 80% of the value of a custom model for 1% of the engineering cost and 0% of the training cost.**

Google's pre-trained models (Vision, Natural Language, Speech-to-Text, Translation) are trained on enormous corpora by teams you cannot replicate. For many problems — extracting text from an invoice, classifying sentiment, transcribing a support call — they will beat anything you can train on your own data, because you do not have the data.

**But "80%" is doing real work in that sentence.** The right framing is that a pre-trained API solves a *general* problem. It works when your problem is general. It fails when your problem is specific.

This gives you a clean decision rule:

```text
Is the concept GENERAL (text, images, speech, language, translation)?
    └─ yes → pre-trained API. Done. Ship it.
    └─ no  → is it a variant of a general concept with YOUR labels?
              └─ yes → AutoML. You supply labels; Google supplies the training.
              └─ no  → custom training (Chapter 8.3) or BigQuery ML (Chapter 8.4).
```

Note the ordering. The most common mistake in ML projects on GCP is jumping straight to Vertex AI custom training when a pre-trained API would have done. The second most common is jumping to AutoML when a pre-trained API would have done.

### The pre-trained API family

| API | Input | Output | Typical use |
|---|---|---|---|
| **Vision API** | Image bytes / GCS URI | Labels, text, faces, document fields | OCR, catalogue tagging, receipt parsing |
| **Natural Language API** | Text | Entities, sentiment, syntax, categories | Feedback triage, ticket routing, PII detection |
| **Speech-to-Text** | Audio | Transcript + timestamps | Call centre transcripts, voice notes |
| **Translation API** | Text | Text in another language | Localisation, multilingual search |
| **Video Intelligence** | Video | Labels, shots, transcript | Media indexing, moderation |
| **Document AI** | PDF/image | Structured fields, tables | Claims, invoices, forms |

All of these share a common architecture, which matters because it determines how you integrate them:

```text
your pipeline ──▶ [ API call ] ──▶ JSON response ──▶ parse ──▶ your table
                   │
                   └── per-unit billed, synchronous or async
```

Three integration facts to internalise:

1. **They are stateless HTTP/gRPC APIs.** No model management, no endpoint to deploy. You call them.
2. **They bill per unit** — per image, per 1000 characters, per minute of audio. Not per training run. This is the fundamental cost difference from Vertex AI.
3. **They have quotas** (requests per minute per project, and per-project daily). You will hit them before you hit your budget. Design for it.

### Vision API

The Vision API exposes several distinct capabilities under one product. They are billed differently and have different accuracy profiles.

**Label detection.** Given an image, returns a set of labels with confidence scores ("dog" 0.98, "grass" 0.91). This is a general object/scene classifier trained on a huge corpus.

- *Reach for it when:* you need generic tagging of photos for search or catalogue organisation; you want a baseline to compare a custom classifier against.
- *Limits:* the label taxonomy is generic. It will not know your product SKU, your packaging, your "industrial valve" versus "plumbing fitting". It has no idea what a "churned account" looks like. It also has no notion of your business hierarchy — you get a flat list with no grouping.

**Text detection (OCR).** Returns text with bounding boxes, and can be asked to return word-level confidences.

- *Reach for it when:* extracting text from scans, receipts, invoices, screenshots.
- *Limits:* OCR on photographs (skewed, low-contrast, curved) is much weaker than on clean scanned documents. For anything document-shaped with structure — tables, key-value pairs, forms — **Document AI** is the right product, not Vision OCR. Vision OCR gives you a bag of text and coordinates; Document AI gives you fields.

**Face detection and recognition.** Face detection returns bounding polygons and landmarks (eyes, nose, mouth). Face recognition matches against an enrolled face collection. Face *detection* (finding faces) is broadly permitted and used for things like framing photos or counting people. **Face recognition** (identifying *who* someone is) has strict regulatory and contractual constraints — it requires an Access Control List (ACL) to be configured, and in many jurisdictions (EU AI Act, Illinois BIPA, various Brazilian LGPD provisions) it triggers legal obligations. Google also restricts it in certain regions.

**Document analysis.** Vision API has a "document text detection" mode that is better than plain OCR for dense documents — it models the document layout and returns full-text and page-level results.

**Image moderation.** Uses the same SafeSearch models: `Likelihood` fields for adult, violence, racy. Returns per-category likelihoods, not a boolean.

**Cost model.** Vision bills **per image** (and per feature — historically, annotating with multiple features could be billed per feature; the current model bills per image with a free tier of 1000 units/month per feature). The economics are simple and favourable:

```text
1,000 images/month  → free
10,000 images/month → ~$1.50 (at $1.50/1000)
1,000,000 images     → ~$150
```

Compare with training a custom image classifier: hundreds of dollars of training compute plus hours of labelling at a scale that makes 10,000 images/month look trivial. **Pre-trained wins decisively on images until your concept is genuinely custom.** The moment you need to distinguish "our SKU-A bottle" from "our SKU-B bottle", AutoML Vision with your own labels becomes competitive.

### Natural Language API

The NLP API has several features, and it is worth understanding which one you actually need because they are billed differently and answer different questions.

**Entity analysis.** Extracts mentions of entities — people, organisations, locations, events, products, dates, quantities — with salience scores and type information. Optionally returns sentiment *per entity* and the underlying text mention.

- *Reach for it when:* you want to extract structured slots from free text: which product, which date, which place.
- *Limits:* it recognises *common* entities. Your internal product codes, your customer tier names, your warehouse IDs are not entities to it. This is the single most common disappointment with the NLP API — you want "SKU-4471-B" extracted and it returns nothing, because that string is not a known entity type. **You need a custom model or AutoML Natural Language for that.**

**Sentiment analysis.** Returns a score from -1.0 (negative) to +1.0 (positive) and a magnitude (how strongly the sentiment is expressed).

- *Reach for it when:* triage inbound feedback, prioritise support tickets, monitor review sentiment.
- *Limits, and this is important:* the sentiment model is trained on *reviews and general text*. On domain text — clinical notes, legal contracts, terse support logs, multilingual technical jargon — accuracy degrades noticeably. Also, **magnitude is the more useful field**: a message with a score of -0.1 and magnitude 5.0 ("this is absolutely unacceptable") is more actionable than -0.6 and magnitude 0.2. Teams routinely look only at the score and miss the strong signal.

**Syntax analysis.** Returns a dependency parse: each token, its part of speech, and the dependency tree. The tree is genuinely useful for extracting relationships ("the invoice *for* Acme *is* due") that bag-of-words approaches miss.

**Content classification.** Two flavours:
- **Pre-trained categories** — a fixed taxonomy of ~1,500 categories (IAB taxonomy, etc.) in several languages. Broad and generic.
- **Custom categories** — you train your own classification model on your own labelled examples and host it. This is the "custom model" feature of the NL API, and it is the closest thing to AutoML here. Note that it is *deprecated* — Google recommends moving custom classification to Vertex AI AutoML Natural Language. Prefer the modern path.

**Limits.** The general limit across all of these: **the model is a black box you did not build, you cannot fine-tune it, you cannot see inside it, and you cannot teach it your domain.** If your stakeholders need an explanation of why a document was classified a particular way, a pre-trained API gives you a confidence score and nothing else. Vertex AI gives you feature importances and explanations.

### Speech-to-Text: the streaming vs batch distinction

This is the most operationally interesting pre-trained API, because the streaming/batch split is not a convenience — it changes the architecture.

**Batch recognition.** You submit an audio file (up to ~60 minutes for synchronous, longer for asynchronous) and receive a transcript.

- *Reach for it when:* the audio is already sitting in a bucket and you can wait minutes for the answer.
- *Limits:* the API is **asynchronous** for files over 1 minute — you submit, get an operation name, and poll. This is a state machine, and you must handle the polling.

**Streaming recognition.** You open a bidirectional gRPC stream, send audio chunks as they arrive, and receive partial results continuously.

- *Reach for it when:* the audio is happening *now* — a live call, a real-time subtitling, a voice command.
- *Why streaming latency matters:* the streaming API returns interim results — partial hypotheses that are revised as more audio arrives. The **final result** stabilises after an end-of-speech detection. The latency you care about is the **lag between the speaker finishing and the final transcript appearing**, and it is typically 200-800 ms depending on configuration.

**The `single_utterance` / `latest_partial` configuration** is what most people need to know:

```text
single_utterance = true   → the server finalises a result at each
                            end-of-speech / pause. Lower latency,
                            but you get one result per utterance and
                            lose the continuity of a dictation.

single_utterance = false  → the server keeps refining a single
                            hypothesis across the whole stream.
                            Better for long dictation; higher latency.
```

**Model choice:** `latest_short` (fastest, best for < 30 s commands), `latest_long` (best for longer speech), `telephony` (for 8 kHz phone audio — mandatory for telephony, and a common mistake is sending 8 kHz audio to `latest_short` and getting garbage).

**The architectural pattern.** Streaming and batch are not alternatives — they are two stages of the same pipeline:

```text
┌─────────────┐   streaming    ┌──────────────┐   GCS     ┌────────────┐
│ live call   │ ─────────────▶ │ STT (stream) │ ─────────▶ │ archive    │
└─────────────┘                │ interim+final│            │ .wav      │
                               └──────────────┘            └─────┬──────┘
                                                                │ async batch
                                                                ▼
                                                          ┌────────────┐
                                                          │ STT (batch)│
                                                          │ better model│
                                                          └────────────┘
```

The streaming result is for the live experience. The batch re-transcription is for the record, using a better model and no time pressure. This is the standard pattern and it is worth implementing deliberately.

**Limits.** Speaker diarisation (who spoke when) is available but adds latency and cost. Domain-specific vocabularies can be supplied as a `phrase_set` — cheap and effective for your product names. For anything requiring accuracy near the state of the art on domain audio, the pre-trained model is not enough; you need **Speech-to-Text V2 with a custom adaptation** (which does require a base model plus adaptation data and is a Vertex AI custom-model workflow, not a simple API call).

### Translation API

There are two different translation products and the distinction trips people up:

1. **Translation API (Basic)** — free, uses a fixed neural MT model, supports ~50 languages. Cannot be customised. Good enough for casual use.
2. **Translation API (Advanced)** — a general-purpose NMT service with:
   - **Glossary terms** — you supply a term/term-pair CSV and the model is instructed to use your terminology consistently. This is the killer feature for brands and legal entities.
   - **Batch translation** — asynchronous, for large volumes, with output to Cloud Storage.
   - **Model adaptation** — train a translation model on your own translated corpus. This is a Vertex AI custom job with a real training cost.

**Reach for it** when you need consistency across a large volume of user-facing text, and glossary terms matter more than raw fluency.

**Limits.** MT output is fluent and slightly wrong. It will not preserve a legally binding meaning without human review, and it will happily mistranslate idiom, sarcasm, and domain jargon. Glossary terms fix terminology, not register or meaning. Do not use MT for legal or medical content without review.

### Video Intelligence

Often forgotten, and genuinely useful. It has three modes:

- **Explicit mode** — per-frame analysis: labels, shot detection, text detection, object tracking.
- **Streaming mode** — process a live video stream, emitting events as they occur.
- **Annotations mode** — store results in a Bigtable-backed annotation store for later query, with filters on labels.

The **streaming mode** is the interesting one for a data engineer: it turns a live video feed into a stream of structured events, which is a natural fit for Pub/Sub → Dataflow → BigQuery. Use cases: shelf monitoring in retail, traffic analysis, safety-event detection. It bills per minute of video, which is expensive — you must decide, on the edge, whether to send footage at all, because you pay for every minute processed regardless of whether anything interesting happened.

### The AutoML family

AutoML is the middle rung: you supply **labelled examples** and Google supplies the training. No model code, no hyperparameter tuning, no ML framework.

| Product | Task | Data you need | Time to train |
|---|---|---|---|
| **AutoML Vision** | Image classification, object detection | Images + labels | ~1–3 hours |
| **AutoML Natural Language** | Text classification, entity extraction | Text + labels | ~1–3 hours |
| **AutoML Tables** | Tabular classification & regression | A table + a label column | Minutes to ~1 hour |
| **AutoML Edge** | On-device vision (Android/iOS/embedded) | Images + labels | Longer; includes model optimisation |

#### AutoML Vision

**Image classification.** Label images, get a model that classifies them.

- *Reach for it when:* you need to distinguish your own categories — "damaged packaging" vs "intact", "our product line A" vs "line B" vs "competitor". This is the case Vision API's generic labels cannot serve.
- *The workflow:* upload images to GCS → create a Dataset → import the images → annotate (in the console UI, by hand, or by importing pre-existing labels) → train → evaluate → deploy to an endpoint or a batch prediction job.
- *Label volumes:* a few hundred images per class is a working baseline; a few thousand gives materially better results. For a binary problem with visually distinct classes, 200 images per class can be genuinely useful.
- *Limits:* annotation is manual and is the bottleneck. **Budget human labelling time, not compute time** — a 10,000-image dataset at 20 seconds per image is 55 hours of human work. This is the real constraint on AutoML, and it is a data-engineering planning problem, not an ML one.

**Object detection.** Draw bounding boxes. Useful for counting or locating objects in an image. The annotation effort per image is much higher than classification (you must draw the boxes), so the dataset cost is much higher per image.

#### AutoML Natural Language

**Text classification.** Assign documents to your own categories — support ticket routing, document filing, intent detection.

**Entity extraction.** Identify specific substrings in text and label them — this is the way to extract your own SKUs, product codes, or internal identifiers from free text, the thing the general-purpose NLP API cannot do.

**The workflow differs from Vision in one important way:** the labels are *inline* with the text. You supply a CSV or JSONL with `(text, label)` pairs. No annotation UI, no per-item drawing. **This makes AutoML NL dramatically cheaper to run than AutoML Vision** for the same model quality, and it is a reason to prefer a text formulation of a problem over an image one when the information content allows it.

- *Reach for it when:* you need to classify or extract *your* concepts from text.
- *Limits:* the labels must be consistent. With 20 examples per class, label noise dominates. Two labelers who disagree about whether a ticket is "billing" or "technical" will produce a model that has learned the disagreement.

#### AutoML Tables

Tabular prediction: classification or regression over structured columns.

**Why this one is different from the other two:** AutoML Tables does **not require a separate annotation phase**. Your training data is a BigQuery table with a label column, and the label is already there because it comes from your warehouse.

**The training-time data preparation AutoML Tables does for you:**
- **Type inference** — STRING, INT64, FLOAT64, BOOL, TIMESTAMP, DATETIME, DATE. It infers from the schema, not from a sample.
- **Categorical encoding** — it handles high-cardinality categoricals intelligently, including target encoding computed with proper cross-validation folding to avoid leakage. This is exactly the thing that is easy to get wrong by hand.
- **Missing value imputation** — nulls are handled natively.
- **Feature selection** — drops low-value features.
- **The AutoML algorithm** — for small datasets (<= 1000 rows) it uses a tuned ensemble; for larger ones it uses a gradient-boosted-tree ensemble with automatic preprocessing. It searches a hyperparameter space and picks the best by cross-validation.

**Reach for it when:** your data is already a table with a label column, and you want a strong baseline in under an hour without writing a line of scikit-learn.

**The critical limitation, and it is a big one:** AutoML Tables **does not support time-based splits well enough for many temporal problems**, and it will happily train on data where the label is computed from future information if you do not pre-filter it. The truncation and as-of rules from Chapter 8.1 must be applied *before* you hand the table over. The tool will not protect you from leakage; it will actually *hide* it, because a leaky table produces a beautiful cross-validation score.

**Also: AutoML Tables has a row limit and a size limit.** For very large training sets, sample or pre-aggregate. And note that AutoML Tables is a Vertex AI product — you pay for the training compute and for the endpoint.

#### AutoML Edge

Train an AutoML Vision model and then **optimise it for on-device inference** — quantisation, distillation, compilation for the target hardware (Android, iOS, Coral, Jetson). The output is a `.tflite` or `.edgetpu` model you ship inside your app.

**Reach for it** when inference must happen on-device: no network round trip, works offline, no per-request cost.

**Why it matters commercially:** a cloud API call per image, on a phone, is a permanent per-unit cost and a permanent network dependency. AutoML Edge converts that into a one-time engineering cost and zero marginal cost.

### The cost model: per-unit vs per-training

This is the most important economic difference, and it should drive the choice more than accuracy does.

```text
                  Pre-trained API              AutoML / Custom (Vertex AI)
─────────────────────────────────────────────────────────────────────────────
Cost shape        per unit of inference        per training run (compute)
                  (image, char, minute)        + per endpoint-hour
Training cost     ZERO                        $3.67 per node-hour and up
Engineering       hours                       days to weeks
Labelling         ZERO (or pre-existing)      the real cost
Custom concept    NO                          YES
Explainability    confidence only             feature importances, SHAP
```

**The break-even calculation.** Suppose a custom vision model costs $200 to train (a one-time GPU training job), and you serve 1,000,000 images a year at $1.50/1000 = $1,500/year in API calls. The custom model is cheaper on compute — but only if its accuracy is comparable, and you paid for labelling, engineering, and an on-call rotation.

The real comparison:

```text
Pre-trained API:  $1,500/year inference, $0 setup, 0 labels, ship in a week
Custom model:     $200 training + $X labels + $Y engineering + endpoint cost
```

**Pre-trained wins until the label cost is genuinely large.** The crossover is usually driven by label cost, not by inference cost, because inference is priced at a few dollars per thousand units.

**Where the economics invert:** at very high volume with a cheap per-unit price, a custom model amortises. A vision model at $1.50/1000 images versus your own model running on a Cloud Run endpoint at $0.000024 per CPU-second — at 100 million images/year, the arithmetic starts to matter. But that is a scale most teams never reach, and by then you have the engineering team to make it work.

**The most underrated cost: labelling.** AutoML Vision on 20,000 images at 20 seconds each is 111 human-hours. At a fully-loaded $60/hour, that is $6,667 of human effort against a $200 training bill. **The training compute is noise; the labels are the budget.** This is the number to put in the business case.

### The decision framework

```text
                     ┌─ Generic concept? (text/image/speech/language)
                     │
        YES ─────────┼──────────────────────────────────────► Pre-trained API
                     │                                       (Vision, NLP, STT, Translation)
                     │
        NO          ▼
                     ┌─ Is the data already a labelled table?
                     │
        YES ─────────┼──────────────────────────────────────► AutoML Tables
                     │                                       or BigQuery ML (8.4)
                     │
        NO          ▼
                     ┌─ Images?  ──────────────────────► AutoML Vision
                     │ Text?    ──────────────────────► AutoML Natural Language
                     │ Need a custom architecture,
                     │ custom loss, custom preprocessing,
                     │ or full control?
                     │   YES ──────────────────────────► Vertex AI custom (8.3)
                     │
                     │ Need sub-100ms online serving at scale
                     │ with your own features?
                     │   YES ──────────► Vertex AI + Feature Store + Endpoint
```

Note the branch that matters most: **if the training data is already a table in BigQuery, the answer is AutoML Tables or BigQuery ML, and the choice between those two is decided in Chapter 8.4** — BigQuery ML is cheaper and simpler for most tabular problems; Vertex AI AutoML Tables is better when you need deeper feature engineering, custom preprocessing, or a deployed endpoint.

### Where these APIs sit in a pipeline

The architectural pattern for using pre-trained APIs at scale:

```text
                    ┌──────────────────────────┐
   GCS bucket ─────▶│ extract / orchestrate    │
   (documents,      │ (Cloud Function, Batch) │
    images, audio)  └───────────┬──────────────┘
                                │
                    ┌───────────▼──────────────┐
                    │  call the API            │
                    │  (batched / parallel)    │
                    └───────────┬──────────────┘
                                │
                    ┌───────────▼──────────────┐
                    │  parse the JSON response │
                    │  (Glue/Dataproc, or a   │
                    │   Dataflow transform)   │
                    └───────────┬──────────────┘
                                │
                    ┌───────────▼──────────────┐
                    │  write to BigQuery      │
                    │  (partitioned, clustered)│
                    └───────────┬──────────────┘
                                │
                    ┌───────────▼──────────────┘
                    ▼
              your warehouse, your models
```

**The engineering realities:**

- **Call the API from a batch job, not from a request handler.** For documents arriving in a bucket, a Cloud Function triggered by `OBJECT_FINALIZE` works but gets rate-limited quickly; a Cloud Run Job or Cloud Batch job that processes in batches of 100-1000 is far more efficient.
- **Handle quota errors with exponential backoff and a dead-letter queue.** Quota errors (`429 RESOURCE_EXHAUSTED`) are normal, not exceptional. The API is a dependency with a rate limit; treat it like one.
- **Persist the raw API response.** Store the JSON in GCS or a BigQuery column. When you change the model version, when a support ticket asks why a document was rejected, when you want to re-run with a different feature — you need the raw response. Re-running the API costs money and may not be reproducible if the model is updated.
- **Cost-control the call.** Vision lets you request only the features you need. Asking for face detection on every receipt you only need OCR for is a direct, avoidable cost.

### The honest limits of everything in this chapter

Let me put these in one place, because they apply across the board:

1. **A pre-trained model is a black box you did not build.** You cannot inspect its weights, cannot retrain it, cannot adapt it (except in the few cases with adaptation features), and you do not control its training data. When it produces a wrong answer, you cannot debug why — you can only file a support case.

2. **A pre-trained model cannot learn *your* business concept.** "Damaged packaging" is not in the general label taxonomy. "Our premium SKU" is not an entity. "Support ticket category 7" is not a sentiment. The moment your concept is specific, you need labels and training.

3. **Confidence scores are not explanations.** A 0.98 label confidence tells you the model is sure; it does not tell you *why*. For regulated or high-stakes decisions, "the model is confident" is not an audit trail.

4. **Pre-trained models are updated without your consent.** Google may retrain and roll out model versions. Your outputs can shift between weeks with no code change. **This is a real operational hazard** — pin behaviour by logging raw responses, and regression-test on a golden set whenever you notice a shift.

5. **There is no training cost, so there is no training accountability.** Nobody on your team knows what the model was trained on, because nobody chose the training data. For anything that needs to be explained or defended, that is disqualifying.

6. **AutoML hides the failure modes you need to know.** AutoML Tables' cross-validated accuracy on a leaky table will be spectacular and meaningless. AutoML Vision's label-consistency problem will show up as mediocre accuracy that you will be tempted to fix by adding more labels — when the actual problem is that your two labellers disagree.

7. **AutoML is a black box too, just a smaller one.** You get feature importances and an evaluation page; you do not get to modify the objective function, the loss, the preprocessing, or the architecture. When you need that, you need custom training.

---

## 🛠️ Hands-On

### Exercise 1 — Vision API: call it and read the response

The client code, and the response shape you must handle.

```python
import sys
sys.path.insert(0, "project/core")

from google.cloud import vision
from google.api_core import exceptions as gcp_exceptions

def annotate_image(image_bytes, feature_types=None):
    """Call the Vision API and return the parsed annotations.

    feature_types defaults to label detection plus text detection, which
    covers the two things most pipelines actually need.
    """
    client = vision.ImageAnnotatorClient()

    image = vision.Image(content=image_bytes)
    feature = None
    if feature_types is None:
        feature = {
            "type_": vision.Feature.Type.LABEL_DETECTION,
            "max_results": 20,
        }
        text_feature = {
            "type_": vision.Feature.Type.TEXT_DETECTION,
            "max_results": 50,
        }
        response = client.batch_annotate_images(
            request={
                "images": [image],
                "features": [feature, text_feature],
            }
        )
    else:
        response = client.batch_annotate_images(
            request={
                "images": [image],
                "features": [{"type_": t} for t in feature_types],
            }
        )

    return response.responses[0]


def parse_labels(annotation_response, min_confidence=0.70):
    """Flatten the Vision response into warehouse-shaped rows.

    Only labels above the confidence floor are kept. Below roughly 0.6
    the generic label set is mostly noise, and noise in a warehouse
    column is worse than no column.
    """
    rows = []
    for label in annotation_response.label_annotations:
        if label.description is None:
            continue
        if label.score < min_confidence:
            continue
        rows.append({
            "kind": "label",
            "name": label.description.lower(),
            "confidence": round(float(label.score), 4),
            "text": None,
        })
    for text in annotation_response.text_annotations:
        if text.description:
            rows.append({
                "kind": "ocr_text",
                "name": None,
                "confidence": None,
                "text": text.description.strip(),
            })
    return rows


def call_with_backoff(fn, max_attempts=5, base_delay=1.0):
    """Retry on quota and transient errors.

    429 RESOURCE_EXHAUSTED is an expected condition, not an exception.
    A pipeline that does not retry it will drop documents on the floor
    whenever the quota is hit.
    """
    import time
    import random

    delay = base_delay
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except gcp_exceptions.ResourceExhausted:
            if attempt == max_attempts:
                raise
            # Full jitter: avoids a thundering herd when many workers
            # hit the quota at the same moment.
            sleep_for = random.uniform(0, delay)
            time.sleep(sleep_for)
            delay = min(delay * 2, 60.0)
        except gcp_exceptions.ServiceUnavailable:
            if attempt == max_attempts:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 60.0)
    return None
```

Note the **`min_confidence` filter**. The generic Vision label set returns up to 20 labels per image, most of them below 0.5. Persisting them all produces a wide, sparse, noisy table that costs money to query and answers no question.

### Exercise 2 — Natural Language API: entity and sentiment parsing

```python
def parse_entity_sentiment(response):
    """Flatten the Natural Language API response into rows.

    Two important details:
      1. sentiment_analysis is per-entity, not per-document. A review
         mentioning two products can have opposite sentiment on each.
      2. magnitude carries the intensity. A mild -0.2 with magnitude 8
         is a strong complaint; a -0.9 with magnitude 0.5 is a passing
         grumble. Sorting on score alone loses the signal.
    """
    document_sentiment = response.document_sentiment
    rows = [{
        "kind": "document_sentiment",
        "mention": None,
        "type_": None,
        "salience": None,
        "sentiment_score": round(document_sentiment.score, 4),
        "sentiment_magnitude": round(document_sentiment.magnitude, 4),
    }]

    for entity in response.entities:
        rows.append({
            "kind": "entity",
            "mention": entity.name,
            "type_": entity.type_,
            "salience": round(entity.salience, 4),
            "sentiment_score": round(entity.sentiment.score, 4)
            if entity.sentiment else None,
            "sentiment_magnitude": round(entity.sentiment.magnitude, 4)
            if entity.sentiment else None,
        })
    return rows


def triage_priority(rows, score_floor=0.3, magnitude_floor=3.0):
    """A concrete triage rule that uses magnitude, not just score."""
    sentiments = [r for r in rows if r["kind"] == "document_sentiment"]
    if not sentiments:
        return "LOW"
    s = sentiments[0]
    strong = abs(s["sentiment_score"]) >= score_floor and s["sentiment_magnitude"] >= magnitude_floor
    if not strong:
        return "LOW"
    if s["sentiment_score"] < 0:
        return "HIGH_NEGATIVE"
    return "POSITIVE"
```

### Exercise 3 — Cost model for a pre-trained API versus a custom model

Using the course `cost_model` module, with real numbers.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate, VERTEX_AI_TRAINING_PER_NODE_HOUR

# Vision API list price: $1.50 per 1000 images.
VISION_PER_1000_IMAGES = 1.50

# Natural Language API: $1.00 per 1000 units (1000 characters each).
NL_PER_1000_UNITS = 1.00

def vision_cost(n_images, per_1000=VISION_PER_1000_IMAGES):
    return (n_images / 1000.0) * per_1000

def nl_cost(n_characters):
    units = n_characters / 1000.0
    return units * NL_PER_1000_UNITS

# A realistic document pipeline: 50,000 images a month.
MONTHLY_IMAGES = 50_000
api_cost = vision_cost(MONTHLY_IMAGES)
print(f"Vision API, {MONTHLY_IMAGES:,} images/month: ${api_cost:,.2f}/month")
print(f"                                  ${api_cost * 12:,.2f}/year")

# A custom model: one training run plus a serving endpoint.
training = estimate("vertex-ai", training_node_hours=4, monthly=False)
print(f"\nCustom training (4 node-hours): ${training.total:,.2f}")
print(f"  (list rate ${VERTEX_AI_TRAINING_PER_NODE_HOUR}/node-hour)")

# The endpoint: a small machine always on.
endpoint = estimate("vertex-ai", training_node_hours=1, monthly=True)
print(f"\nVertex AI endpoint, 1 node for a month: ${endpoint.total:,.2f}")

# The number that actually decides it: human labelling.
IMAGES = 20_000
SECONDS_PER_LABEL = 20
LOADED_HOURLY_RATE = 60.0
label_hours = IMAGES * SECONDS_PER_LABEL / 3600.0
label_cost = label_hours * LOADED_HOURLY_RATE
print(f"\nLabelling {IMAGES:,} images at {SECONDS_PER_LABEL}s each:")
print(f"  {label_hours:.1f} human-hours  =  ${label_cost:,.2f}")
print(f"\nTraining compute was ${training.total:,.2f}.")
print(f"Label cost is {label_cost / training.total:.1f}x the training compute.")
```

The last two lines are the point of the whole exercise. **On vision, the label budget dwarfs the training budget.** Any business case that quotes only the training cost is quoting the wrong number.

### Exercise 4 — AutoML Tables: prepare the training table correctly

The preparation step that decides whether AutoML produces a useful model.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    build_bigquery_rows,
    aggregate_events,
    render_summary_csv,
)

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines[1:])
rows = build_bigquery_rows(accepted)

# --- Step 1: the label. It must already be in the table. ---
# AutoML Tables does not do annotation. If the label is not a column,
# there is no model.
LABEL_COLUMN = "is_refund"

# --- Step 2: the as-of filter, applied BEFORE handing the table over. ---
# AutoML will not do this for you, and a leaky table produces a
# spectacular and meaningless cross-validation score.
PREDICTION_CUTOFF = "2026-01-16T00:00:00+00:00"

# --- Step 3: feature engineering in SQL, done here in Python. ---
from collections import defaultdict
from datetime import datetime

history = defaultdict(list)
for r in rows:
    if r["event_dt"] < PREDICTION_CUTOFF:
        history[r["user_id"]].append(r)

training_rows = []
for user_id, events in history.items():
    orders = [e for e in events if e["event_type"] == "order"]
    refunds = [e for e in events if e["event_type"] == "refund"]
    total = sum(o["amount_eur"] for o in orders)
    n_orders = len(orders)
    training_rows.append({
        "user_id": user_id,
        "n_events": len(events),
        "n_orders": n_orders,
        "n_refunds": len(refunds),
        "total_spend_eur": round(total, 2),
        "avg_order_value_eur": round(total / n_orders, 2) if n_orders else 0.0,
        "refund_rate": round(len(refunds) / len(events), 4),
        "region": events[0]["region"],
        "channel": events[0]["channel"],
        LABEL_COLUMN: 1 if refunds else 0,
    })

print(f"training rows: {len(training_rows)}")
positives = sum(r[LABEL_COLUMN] for r in training_rows)
print(f"positives: {positives}  rate: {positives/len(training_rows):.4f}")

# --- Step 4: sanity checks before training. ---
# A label column with one value produces a degenerate model. A table with
# a single feature produces a model with nothing to learn from.
assert len(set(r[LABEL_COLUMN] for r in training_rows)) == 2, "label has one class only"
feature_cols = [c for c in training_rows[0] if c not in ("user_id", LABEL_COLUMN)]
assert len(feature_cols) >= 3, "not enough features"

print(f"feature columns ({len(feature_cols)}): {feature_cols}")
print("\nTable is ready for AutoML Tables / BigQuery ML.")
```

### Exercise 5 — The AutoML Tables training call and the evaluation you get back

```python
def create_automl_tables_model(
    project_id,
    dataset_id,
    table_id,
    label_column,
    model_display_name,
    budget_millis=1800000,
):
    """Kick off an AutoML Tables training job.

    The training budget is in milliseconds of *compute*, not wall clock.
    1_800_000 ms = 30 minutes of training time.
    """
    from google.cloud import aiplatform

    aiplatform.init(
        project=project_id,
        location="us-central1",
    )

    dataset_ref = aiplatform.gapic.DatasetReference(
        project=project_id, dataset_id=dataset_id
    )
    table_ref = aiplatform.gapic.TableReference(
        project=project_id, dataset_id=dataset_id, table_id=table_id
    )

    job = aiplatform.AutoMLTabularTrainingJob(
        display_name=model_display_name,
        optimization_prediction_type="binary",
    )

    model = job.run(
        dataset=dataset_ref,
        target_column=label_column,
        optimization_prediction_type="binary",
        training_budget_millis=budget_millis,
        feature_columns=[
            aiplatform.AutoMLTabularTrainingJob.FeatureColumn(
                name="n_events", type="INT64"
            ),
            aiplatform.AutoMLTabularTrainingJob.FeatureColumn(
                name="total_spend_eur", type="FLOAT64"
            ),
            aiplatform.AutoMLTabularTrainingJob.FeatureColumn(
                name="avg_order_value_eur", type="FLOAT64"
            ),
            aiplatform.AutoMLTabularTrainingJob.FeatureColumn(
                name="refund_rate", type="FLOAT64"
            ),
            aiplatform.AutoMLTabularTrainingJob.FeatureColumn(
                name="region", type="CATEGORY"
            ),
            aiplatform.AutoMLTabularTrainingJob.FeatureColumn(
                name="channel", type="CATEGORY"
            ),
        ],
        sync=True,
    )
    return model


def summarise_automl_evaluation(model):
    """Pull the evaluation metrics out of the trained model.

    AutoML gives you a metrics object with the full confusion matrix and
    the curve data. You want to read the metrics at YOUR operating
    threshold, not the default.
    """
    evaluation = model.evaluate()
    metrics = evaluation.metrics

    print("AUROC      :", metrics.auc_roc)
    print("AUPRC      :", metrics.auc_pr)
    print("Log loss   :", metrics.log_loss)
    print("Brier      :", metrics.brier_score)
    print("Accuracy   :", metrics.accuracy)

    # The confusion matrix at the default threshold.
    cm = metrics.confusion_matrix
    print("\nConfusion matrix:")
    print(f"  true positives : {cm.true_positives}")
    print(f"  false positives: {cm.false_positives}")
    print(f"  true negatives : {cm.true_negatives}")
    print(f"  false negatives: {cm.false_negatives}")

    # Precision and recall at the threshold that was used.
    precision = cm.true_positives / max(
        cm.true_positives + cm.false_positives, 1
    )
    recall = cm.true_positives / max(
        cm.true_positives + cm.false_negatives, 1
    )
    print(f"\nprecision  : {precision:.4f}")
    print(f"recall     : {recall:.4f}")
    return metrics
```

Note `optimization_prediction_type`. It must match the label: `"binary"` for a two-class label, `"multi_class"` for more than two, `"regression"` for a continuous target. Getting this wrong is one of the more common AutoML errors.

### Exercise 6 — Streaming vs batch Speech-to-Text

The two code paths, and the latency difference they produce.

```python
def transcribe_batch(audio_path):
    """Batch recognition: submit a file, poll until the operation ends.

    For files over one minute the API is asynchronous. You get an
    operation name and must poll it. The polling loop below is the
    part people forget to write.
    """
    from google.cloud import speech

    client = speech.SpeechClient()

    with open(audio_path, "rb") as f:
        content = f.read()

    config = {
        "encoding": "LINEAR16",
        "sample_rate_hertz": 16000,
        "language_code": "en-US",
        "enable_word_time_offsets": True,
        # phone audio MUST use the telephony model
        "model": "telephony",
    }

    operation = client.long_running_recognize(
        config=config,
        audio={"content": content},
    )
    response = operation.result(timeout=600)
    return response.results[-1].alternatives[0].transcript


def transcribe_streaming(audio_chunks, interim_results=True):
    """Streaming recognition over a bidirectional gRPC stream.

    Yields interim results as they arrive and a final result at the
    end. The interim results are hypotheses — they get revised as more
    audio arrives — so they are for display only, never for storage.
    """
    from google.cloud import speech

    client = speech.SpeechClient()
    config = speech.StreamingRecognitionConfig(
        config=speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            # single_utterance=True finalises the result at each pause.
            # It cuts latency and is right for command-style audio.
            single_utterance=False,
        ),
        interim_results=interim_results,
    )

    streaming_config = speech.StreamingRecognitionConfig(config=config)

    requests = (
        speech.RecognizeRequest(audio_content=chunk) for chunk in audio_chunks
    )

    responses = client.streaming_recognize(requests, streaming_config)

    final_transcript = []
    for response in responses:
        for result in response.results:
            text = result.alternatives[0].transcript
            if result.is_final:
                final_transcript.append(text)
                yield ("final", text)
            else:
                yield ("interim", text)

    return " ".join(final_transcript)


def measure_streaming_lag(chunks):
    """Measure the lag between end-of-audio and the final result.

    In production this is the number you set your UX budget from.
    """
    import time

    start = time.monotonic()
    last_chunk_at = None
    final_at = None

    for kind, _ in transcribe_streaming(chunks):
        if kind == "final":
            final_at = time.monotonic()

    if final_at and last_chunk_at:
        return final_at - last_chunk_at
    return final_at - start if final_at else None
```

The comment on `single_utterance` is the operational content: `True` finalises at each pause, which is what you want for a voice assistant and wrong for a dictation session.

### Exercise 7 — The decision scorecard

A reusable artefact, because these decisions recur.

```python
def score_prebuilt_vs_automl(
    *,
    concept_is_general: bool,
    data_already_labelled: bool,
    is_tabular: bool,
    monthly_volume: int,
    needs_online_serving: bool,
    needs_explanation: bool,
    label_hours_available: float,
):
    """Score the options and return a recommendation with reasoning.

    This is deliberately explicit about the weights so the decision can
    be argued with rather than accepted.
    """
    scores = {"prebuilt": 0, "automl": 0, "custom": 0}
    reasons = {"prebuilt": [], "automl": [], "custom": []}

    if concept_is_general:
        scores["prebuilt"] += 5
        reasons["prebuilt"].append("concept is general — a pre-trained model covers it")
    else:
        scores["automl"] += 3
        reasons["automl"].append("concept is specific — needs your labels")
        if not data_already_labelled:
            scores["custom"] += 1
            reasons["custom"].append("no labels available — you would need to create them anyway")

    if is_tabular and data_already_labelled:
        scores["automl"] += 4
        reasons["automl"].append("labelled tabular data — no annotation phase needed")
        scores["custom"] -= 1
        reasons["custom"].append("tabular data does not justify a custom pipeline")

    if label_hours_available < 20:
        scores["prebuilt"] += 3
        reasons["prebuilt"].append(
            f"only {label_hours_available:.0f}h of labelling available — "
            "annotation is the binding constraint"
        )
        scores["automl"] -= 2

    if needs_online_serving:
        scores["custom"] += 2
        reasons["custom"].append("online serving with sub-second latency needs an endpoint")
        if monthly_volume > 1_000_000:
            scores["custom"] += 1
            reasons["custom"].append(
                f"{monthly_volume:,}/month — per-unit API cost starts to matter"
            )

    if needs_explanation:
        scores["custom"] += 3
        reasons["custom"].append("explanations required — pre-trained APIs give confidence only")
        scores["prebuilt"] -= 2

    best = max(scores, key=scores.get)
    return {
        "recommendation": best,
        "scores": scores,
        "reasons": reasons,
        "total_label_hours_needed": (
            label_hours_available if best != "automl" else label_hours_available * 1.0
        ),
    }


result = score_prebuilt_vs_automl(
    concept_is_general=False,
    data_already_labelled=True,
    is_tabular=True,
    monthly_volume=50_000,
    needs_online_serving=True,
    needs_explanation=True,
    label_hours_available=40,
)

print(f"Recommendation: {result['recommendation'].upper()}")
print(f"Scores: {result['scores']}")
for option, rs in result["reasons"].items():
    for r in rs:
        print(f"  [{option:8s}] {r}")
```

---

## 🛠️ Common Errors and Fixes

### 1. `google.api_core.exceptions.InvalidArgument: Invalid image` — sending a URL where bytes are expected

**Symptom.**

```text
google.api_core.exceptions.InvalidArgument: 400 Invalid image: URL is not allowed
```

**Cause.** The Vision API rejects remote URLs by default for `batch_annotate_images`. The `image_source.image_uri` field is disabled unless the project is explicitly allowlisted for the `vision.googleapis.com` feature "Read from GCS and Cloud Storage URIs".

**Fix.** Either enable the allowlisting (which requires an allowlist request and goes through Google's abuse-prevention review), or read the bytes yourself and send them:

```python
from google.cloud import vision

# Wrong — rejected by the API.
image = vision.Image(source=vision.ImageSource(image_uri="gs://bucket/img.png"))

# Right — read the bytes and send content.
with open("img.png", "rb") as f:
    image = vision.Image(content=f.read())
```

For GCS-hosted images, the recommended pattern is to use a **Vision product** feature (like Product Search) which does support GCS URIs, or to read the object into memory.

### 2. `google.api_core.exceptions.Forbidden: Permission denied on resource project` — missing IAM roles

**Symptom.**

```text
google.api_core.exceptions.Forbidden: Permission 'vision.images.annotate' denied on resource (or it may not exist)
```

**Cause.** The service account lacks `roles/visionai.user` or the specific permission. Similar failures appear for `ml.developer` (Vertex AI), `logging.viewer` (Writing to log), and `serviceusage.serviceUsageConsumer`.

**Fix.** Grant the narrowest role that works:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:pipeline-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/visionai.user"
```

**A trap:** `roles/editor` will make the error go away and is the wrong answer in production. The owner of a service account that can call every API is a security incident waiting to happen, and the IAM chapter covers why.

### 3. `google.api_core.exceptions.ResourceExhausted: Quota exceeded` — the quota error that is not an exception

**Symptom.** Your pipeline drops 3% of documents, silently, under load.

**Cause.** Vision API has a default per-project quota (roughly 600 requests per minute for `batch_annotate_images`). You hit it and the request fails with 429.

**Fix.** Treat it as expected. Retry with exponential backoff *and full jitter* (see `call_with_backoff` in the Hands-On), and for bulk processing use the **asynchronous batch API** (`async_batch_annotate_files`), which processes a directory of images in GCS server-side and writes the results back to GCS. That is dramatically cheaper in quota terms because it is not one HTTP request per image.

### 4. `google.api_core.exceptions.NotFound: Request contains an invalid argument` — Speech-to-Text audio format mismatch

**Symptom.**

```text
google.api_core.exceptions.InvalidArgument: 400 Request contains an invalid argument.
```

**Cause.** The `encoding` does not match the actual bytes. A WAV file header says it is LINEAR16 but the client is told `FLAC`; or, more commonly, a mono 8 kHz telephony recording is submitted with `sample_rate_hertz: 16000`.

**Fix.** Read the actual format rather than assuming it:

```python
import wave

with wave.open("call.wav", "rb") as wf:
    channels = wf.getnchannels()
    rate = wf.getframerate()
    width = wf.getsampwidth()
    print(f"channels={channels} rate={rate} width={width}")

config = {
    "encoding": "LINEAR16",
    "sample_rate_hertz": rate,      # use the real rate
    "language_code": "en-US",
    "audio_channel_count": channels,
    "model": "telephony" if rate == 8000 else "latest_long",
}
```

Also check that the file is not FLAC-in-a-WAV-container, which the API rejects with `UNSUPPORTED_AUDIO_FORMAT`.

### 5. AutoML Tables: the model is suspiciously perfect

**Symptom.** AUROC 0.99 on a churn problem. Live performance at chance.

**Cause.** Label leakage in the table you handed over. AutoML's cross-validation is honest; your features were not.

**Fix.** Audit every feature against the as-of rule from Chapter 8.1. The most common leaks:

```sql
-- Leaky: aggregates include events after the prediction date.
select user_id, count(*) as n_orders
from `curated.events`
group by user_id

-- Fixed: as-of aggregate.
select user_id, count(*) as n_orders
from `curated.events`
where event_dt < @prediction_date
group by user_id
```

And check the label window: an entity that has not been observable for the full outcome window must be excluded, not defaulted to "no".

### 6. `ValueError: Incompatible schema for type float64: expected 1, got 2` — wrong AutoML prediction type

**Symptom.**

```text
ValueError: Incompatible schema for type float64: expected 1, got 2
```

**Cause.** `optimization_prediction_type` is `"regression"` but the label column is binary (or is `{"binary"}` but the label has three classes).

**Fix.** Match the type to the label, and check the class count before you submit:

```python
from google.cloud import aiplatform

# `training_rows` is the fetched training table; `LABEL_COLUMN` is the
# name of the label column in it.
label_values = set(row[LABEL_COLUMN] for row in training_rows)
if label_values == {0, 1}:
    prediction_type = "binary"
elif all(isinstance(v, (int, float)) for v in label_values):
    prediction_type = "regression"
else:
    prediction_type = "multi_class"

job = aiplatform.AutoMLTabularTrainingJob(
    display_name=model_display_name,
    optimization_prediction_type=prediction_type,
)
```

---

## 💡 Production Notes

- **Reach for a pre-trained API first, every time.** If the concept is general — text, images, speech, language — a custom model is a premature optimisation. The engineering cost of Vertex AI is weeks; the API call is an afternoon.

- **Request only the API features you need.** Vision bills per feature on some configurations and the marginal cost of asking for face detection on every receipt you only need OCR for is a real, avoidable line in the bill.

- **Store the raw API response next to the extracted fields.** Model versions roll out without notice; the raw response is the only way to re-derive a decision from a past input, and it is the only evidence you have when a support ticket disputes a classification.

- **Annotate with a labelling guide, not a convention.** Two labellers who disagree about "billing" versus "technical" will produce a model that learned the disagreement. Write the guide, have both labelers apply it to the same 50 items, and reconcile before labelling thousands.

- **Budget human labelling hours explicitly in every AutoML business case.** 20,000 images at 20 seconds each is 111 hours. At a loaded $60/hour that is $6,667 — often 30× the training compute cost. Quote the label cost, not the training cost.

- **Pin behaviour with a golden-set regression test.** Pre-trained models are updated without your consent. Keep 200 labelled examples in version control, re-run them on every model version bump, and alert on any metric movement beyond your tolerance.

- **Build the API call into a batch job, not a request handler.** For objects landing in a bucket, a Cloud Run Job processing 500 at a time beats a Cloud Function per object on quota, cost, and throughput. Use the asynchronous batch APIs where they exist.

- **Put a dead-letter queue on every API call site.** Quota errors, transient failures, and malformed inputs are normal. An un-retried, un-DLQ'd API call in a pipeline is a silent data-loss bug.

- **Decide the AutoML Tables training budget in compute-milliseconds, and raise it when the score plateaus.** 30 minutes is often too short for a hard tabular problem; 2 hours is cheap insurance. But set it deliberately — the default is a trap either way.

- **Do not let a pre-trained API's confidence score become a decision input for anything regulated.** "The model is 98% sure" is not an audit trail, a justification, or an explanation.

---

## 🔑 Key Takeaways

- **The fastest path to value is a pre-trained API.** 80% of the value for 1% of the engineering cost and zero training cost — but only when the concept is general.
- **The decision rule:** general concept → pre-trained API. Specific concept with labels → AutoML. Tabular with a label column → AutoML Tables or BigQuery ML. Anything needing a custom architecture or explanations → Vertex AI custom training.
- **Vision API** does label detection, OCR, face detection, and document text detection. Its labels are generic — it will not know your product, your packaging, or your internal taxonomy. For structured documents, **Document AI** beats Vision OCR.
- **Natural Language API** extracts entities, sentiment, syntax, and classifies content. Entity analysis only recognises *common* entities — your SKUs and internal codes need AutoML Natural Language or a custom model.
- **Sentiment magnitude beats sentiment score.** A mild score with high magnitude is a stronger signal; teams routinely sort on the wrong field.
- **Speech-to-Text streaming vs batch is an architectural decision.** Streaming gives 200-800 ms latency with revisable interim results; batch is asynchronous and better for archival. The standard pattern is to do both.
- **Use the `telephony` model for 8 kHz phone audio.** Sending it to `latest_short` produces garbage.
- **`single_utterance=True` finalises at each pause** — right for commands, wrong for dictation.
- **Translation API Basic is free and fixed; Advanced has glossary terms, batch, and model adaptation.** Glossary consistency matters more than raw fluency for brands and legal entities.
- **Video Intelligence streaming mode turns live video into a stream of structured events** — a natural Pub/Sub → Dataflow pipeline. It bills per minute processed, so decide at the edge what is worth sending.
- **AutoML Vision** classifies images but needs manual annotation — the bottleneck is human labelling, not compute.
- **AutoML Natural Language** is dramatically cheaper to run than AutoML Vision because labels are inline with the text. **Prefer a text formulation of a problem over an image one when the information content allows.**
- **AutoML Tables needs no annotation phase** — your label is already a column. But it will not protect you from leakage; a leaky table produces a beautiful and meaningless cross-validation score.
- **The cost shape differs fundamentally:** pre-trained is per-unit inference; AutoML and custom are per-training-run plus endpoint. The crossover is usually driven by **label cost**, not inference cost.
- **Training compute is noise; labels are the budget.** 20,000 images at 20 seconds each is $6,667 of human effort against a $200 training bill.
- **A pre-trained model is a black box you did not build.** You cannot inspect it, retrain it, adapt it, or explain it. Confidence is not an explanation.
- **Pre-trained models are updated without your consent.** Log raw responses and keep a golden set for regression testing.
- **AutoML is a black box too, just a smaller one.** It gives feature importances, not control over the objective function, loss, or preprocessing.

---

## 📚 Practice Exercises

1. **Vision API pipeline.** Write `annotate_bucket(bucket, prefix, out_table)` that lists objects in a GCS bucket, calls the Vision API for label detection and OCR on each, parses the responses into warehouse-shaped rows, applies a confidence floor of 0.70, and writes to a partitioned BigQuery table. Include the backoff wrapper and a dead-letter path for objects that fail after the retry budget. Then state the monthly cost at 50,000 and 5,000,000 images.

2. **Label-confidence audit.** Using the project pipeline, take the per-region summary (`render_summary_csv`) and design a labelling guide for a hypothetical "damaged order" classifier over the event data. Define the classes, write two ambiguous example cases, show how they would be labelled differently by two labellers, and explain how that disagreement would manifest in the trained model's metrics.

3. **Break-even analysis.** Build a spreadsheet-style comparison for a document-classification problem: 2 million documents per month, 6 classes, with 5,000 labelled examples already available. Compare (a) the Natural Language API with custom-category training, (b) AutoML Natural Language, (c) a Vertex AI custom training job, (d) BigQuery ML on a feature-extracted table. Include inference cost, one-time training cost, labelling cost, and engineering cost in days. State the conditions under which the answer changes.

4. **Streaming Speech-to-Text.** Implement `transcribe_streaming` with interim results and a `single_utterance` toggle. Measure and report the lag between the last audio chunk and the final transcript in three configurations: `latest_short` + `single_utterance=True`, `latest_long` + `single_utterance=False`, and `latest_long` + `single_utterance=True`. Explain which you would pick for a live subtitling feature and which for call-centre archival, and why.

5. **AutoML Tables preparation.** Using `sample_data/events.csv` and the course pipeline, build a training table with the label column, an as-of filter, and at least six features. Write the equivalent BigQuery DDL and the AutoML training call. Then write the exact SQL that would produce the *leaky* version of the same table, and explain which metric each version would report and why they differ.

6. **Golden-set regression harness.** Write `run_golden_set(endpoint, golden_df)` that sends a labelled golden set to a deployed endpoint and computes accuracy, precision, recall, and calibration error. Define a tolerance policy: what change in which metric triggers a failure, and what you do when it fires. Explain why a golden set of 200 examples is worth more to you than a training set of 200,000.

7. **Glossary and consistency.** Design a Translation API glossary for a company with 40 internal product names and a legal disclaimer. Write the glossary CSV format, explain what it does and does not fix, and describe the workflow for keeping it current as products are renamed. Then state where you would place human review.

8. **Decision memo.** For a concrete business problem — say, moderating 5 million user-uploaded images per month across 6 policy categories — write a one-page recommendation choosing between Vision API moderation, AutoML Vision with custom categories, and a custom Vertex AI vision model. Include the labelling budget, the monthly run rate, the explainability position, and the trigger that would cause you to migrate to the next option.

---

## 📖 Further Reading

- [Cloud Vision API — Documentation](https://cloud.google.com/vision/docs)
- [Cloud Vision API — Image Analysis](https://cloud.google.com/vision/docs/labels)
- [Cloud Natural Language API — Documentation](https://cloud.google.com/natural-language/docs)
- [Cloud Natural Language API — Entity Analysis](https://cloud.google.com/natural-language/docs/analyzing-entities)
- [Cloud Speech-to-Text — Streaming Recognition](https://cloud.google.com/speech-to-text/docs/streaming-recognize)
- [Cloud Translation API (Advanced) — Glossaries](https://cloud.google.com/translate/docs/advanced/glossary)
- [Vertex AI AutoML — Introduction to AutoML](https://cloud.google.com/vertex-ai/docs/tabular-data/classification-regression/overview)
- [Vertex AI AutoML — Image Classification](https://cloud.google.com/gemini-enterprise-agent-platform/machine-learning/tutorials/image-classification-automl/overview)
- [Document AI — Overview](https://cloud.google.com/document-ai/docs/overview)

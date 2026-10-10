# System Design Sub-Lesson 8 — Media Streaming and Content Delivery (the canonical Pattern 8 walkthrough)

> **Media streaming and content delivery are the eighth most common system design pattern.** 5-10% of system design questions involve media (Netflix, YouTube, Spotify, podcast platforms). The FDE signal: a candidate who names the CDN AND the transcoding pipeline AND the adaptive bitrate — is showing they can own a media system. **This sub-lesson walks through the canonical media streaming design.**

---

## Why media streaming is the FDE signal

The 3 things the interviewer is testing:

1. **Can you read the requirements?** Media = video/audio files delivered to millions of users concurrently. The requirement drives the design (CDN, transcoding, adaptive bitrate).
2. **Can you pick the right CDN?** CloudFront, Fastly, Cloudflare. The candidate who names the CDN and the cache hit rate is showing they understand the operational boundary.
3. **Can you handle transcoding?** Videos come in many codecs (H.264, H.265, VP9). The candidate who names the transcoding pipeline is showing they understand the upload + processing flow.
4. **Can you handle adaptive bitrate?** Network conditions vary (3G, WiFi, fiber). The candidate who names the adaptive bitrate ladder is showing they understand the playback experience.

**The FDE pattern:** clarify → decompose → design → tradeoffs. Same as the other patterns, but the design is media-focused.

---

## The canonical media streaming design (worked example)

### The prompt

> "Design a media streaming system: a YouTube-style video platform. 10M videos, 1M daily active users, 100K concurrent viewers, sub-2-second video start time. The system should handle 4K video delivery and survive a single region failure."

### Step 1: Clarify (5-7 minutes)

**The 5 questions:**

1. **What's the user?** Viewers (external) watching videos; uploaders (external) uploading videos.
2. **What's the scale?** 10M videos; 1M DAU; 100K concurrent viewers; 2-second video start time.
3. **What's the constraint?** Sub-2-second start time; cost < $10K/month; survive 1 region failure; adaptive bitrate (3G to fiber).
4. **What's the failure mode?** CDN is down; transcoding fails; region is down.
5. **What's the timeline?** MVP in 8 weeks; full scale in 16 weeks.

### Step 2: Decompose (10-12 minutes)

**The 3 lists:**

**Entities:**
- Video (id, title, owner_id, duration, status, created_at)
- VideoFile (video_id, resolution, codec, bitrate, s3_url)
- View (id, video_id, user_id, timestamp, watch_duration)
- Upload (id, user_id, filename, status, s3_url)

**Services:**
- VideoAPI (CRUD for videos)
- UploadService (handles chunked uploads to S3)
- TranscodingService (FFmpeg worker for transcoding to multiple resolutions)
- CDNService (CloudFront for global delivery)
- AnalyticsService (records views, watch duration)

**Flows:**
- Uploader uploads video → UploadService stores raw video in S3 → TranscodingService transcodes to multiple resolutions → stores transcoded files in S3 → updates Video.status to 'ready'
- Viewer requests video → CDN serves the video from the edge → adaptive bitrate adjusts based on network conditions
- AnalyticsService records views + watch duration for recommendations

### Step 3: Design (15-20 minutes)

**The API contracts (3-5 endpoints):**

```
POST /videos
  Body: {"title": "My Video", "filename": "video.mp4"}
  → 201 Created
  → {"video_id": "VID-12345", "upload_url": "https://s3-presigned...", "status": "uploading"}

GET /videos/{id}
  → 200 OK
  → {"video_id": "VID-12345", "title": "My Video", "duration": 600, "status": "ready", "resolutions": ["360p", "720p", "1080p", "4k"]}

GET /videos/{id}/stream?resolution=auto
  → 302 Redirect
  → Location: https://cdn.example.com/video-12345/manifest.m3u8

POST /videos/{id}/view
  Body: {"watch_duration": 300}
  → 200 OK
  → {"view_id": "VIEW-12345"}
```

**The data model (3-5 tables):**

```
videos (
  id BIGSERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  owner_id BIGINT NOT NULL,
  duration INT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'uploading',  -- uploading, transcoding, ready, failed
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
)

video_files (
  id BIGSERIAL PRIMARY KEY,
  video_id BIGINT REFERENCES videos(id),
  resolution VARCHAR(10) NOT NULL,  -- 360p, 720p, 1080p, 4k
  codec VARCHAR(20) NOT NULL,  -- h264, h265, vp9
  bitrate INT NOT NULL,
  s3_url VARCHAR(255) NOT NULL,
  UNIQUE(video_id, resolution, codec)
)

views (
  id BIGSERIAL PRIMARY KEY,
  video_id BIGINT REFERENCES videos(id),
  user_id BIGINT,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  watch_duration INT NOT NULL
)
```

**The S3 layout:**

```
s3://videos-bucket/
  raw/
    video-12345/
      original.mp4
  transcoded/
    video-12345/
      360p/
        manifest.m3u8
        segment-00001.ts
        ...
      720p/
        ...
      1080p/
        ...
      4k/
        ...
```

**The scale model:**

- **Storage:** 10M videos × 10GB avg (4K) = 100PB raw; 4 resolutions × 10GB = 40PB transcoded
- **Bandwidth:** 100K concurrent viewers × 10Mbps (1080p) = 1TB/sec
- **Cost:** $10K/month (S3 $2K + CloudFront $5K + transcoding $2K + Postgres $500 + CloudWatch $500)

### Step 4: Tradeoffs (5-7 minutes)

**The 3 tradeoffs:**

1. **Transcode at upload vs transcode on demand.** Upload is faster for the viewer but costs more upfront. On-demand is cheaper upfront but slower for the viewer. Pick transcode at upload for popular videos; pick transcode on demand for long-tail.
2. **CloudFront vs Fastly vs Cloudflare.** CloudFront is the AWS default; Fastly has better edge compute; Cloudflare has better DDoS protection. Pick CloudFront for AWS deployments; pick Fastly for low-latency edge compute; pick Cloudflare for DDoS protection.
3. **HLS vs DASH vs progressive download.** HLS is the iOS default; DASH is more codec-agnostic; progressive download is simpler but no adaptive bitrate. Pick HLS for mobile; pick DASH for web; pick progressive for short clips.

**The closing line:** "For 10M videos at 100K concurrent viewers with sub-2-second start time, I'd use S3 for raw + transcoded storage, CloudFront for global CDN delivery, FFmpeg workers for transcoding to 4 resolutions, and HLS for adaptive bitrate. The cost is $10K/month, under the $10K/month ceiling. The failure mode is CDN down; the fallback is S3 with a 5-second timeout."

---

## The 5 most common media streaming questions

The 5 questions that cover 90% of media streaming system design:

1. **"Design a YouTube-style video platform"** — covered by the canonical example above.
2. **"Design a Netflix-style streaming service"** — same pattern, with DRM + recommendation engine.
3. **"Design a Spotify-style music platform"** — same pattern, with audio transcoding + recommendation.
4. **"Design a podcast platform"** — same pattern, with RSS + audio delivery + analytics.
5. **"Design a TikTok-style short video platform"** — same pattern, with low-latency upload + recommendation.

**The pattern:** media streaming = S3 for raw + transcoded + CloudFront for CDN + FFmpeg for transcoding + HLS/DASH for adaptive bitrate. The variations are the codec (H.264, H.265, VP9), the resolution (360p to 4K), and the latency (sub-2-second vs sub-500ms).

---

## The 5 anti-patterns for media streaming

1. **Naming a technology in the first 5 minutes.** The framework says: clarify, decompose, design, tradeoffs. The technology comes in step 3.
2. **Skipping the CDN story.** The candidate who doesn't mention CDN is signaling they don't understand global delivery.
3. **Skipping the transcoding pipeline.** The candidate who doesn't mention transcoding is signaling they don't think about codec compatibility.
4. **Skipping the adaptive bitrate.** The candidate who doesn't mention HLS/DASH is signaling they don't think about network variability.
5. **Skipping the cost calculation.** "It would cost $X/month" without the math is hand-waving. The cost model is the FDE signal.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How do you handle a viral video (1M concurrent viewers)?" | "CloudFront auto-scales. I'd pre-warm the cache for the manifest + the first segment. I'd add a rate limiter on the manifest endpoint." |
| 2. "What if the CDN is down?" | "Fallback to S3 with a longer timeout. The video start time goes from 2 seconds to 10 seconds, but the video still works." |
| 3. "How do you handle live streaming?" | "Use HLS with low-latency extensions. Use WebRTC for sub-second latency. Use a streaming service (e.g., AWS IVS, Mux) for managed live streaming." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../decomposition/README.md` | The 4-step framework (clarify → decompose → design → tradeoffs) |
| `../system-design/06-batch-processing.md` | The transcoding pipeline (similar pattern) |
| `../system-design/README.md` | The 9 patterns cheat sheet (Pattern 8: media streaming) |

---

## The thesis

**Media streaming is the eighth most common system design pattern.** The candidate who names the CDN AND the transcoding pipeline AND the adaptive bitrate — is showing they can own a media system.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The 5 worked examples (YouTube, Netflix, Spotify, podcast, TikTok) are the patterns. Practice them out loud, time yourself at 60 minutes per question, and rehearse with an AI assistant.

**General prep gets you past the resume screen. System design prep gets you past the centerpiece round at Anthropic, OpenAI, AWS FDE, Databricks, and Scale AI.**
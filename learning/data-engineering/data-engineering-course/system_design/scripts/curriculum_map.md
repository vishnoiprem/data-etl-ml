# Curriculum Map

> The canonical 71-lesson curriculum, mapped to the modules in this
> course directory.

| # | Module | Lessons | Title | Pattern focus |
|---|---|---|---|---|
| **00** | Overview | 5 | Interview framework, patterns, rubric | Meta |
| | 5.1 | | Introduction to the System Design Interview | |
| | 5.2 | | How to Answer System Design Interview Questions | |
| | 5.3 | | The Must-Know System Design Patterns | |
| | 5.4 | | Rubric for System Design Interviews | |
| | 5.5 | | How to Use a Whiteboard in System Design Interviews | |
| **01** | Read-Heavy Systems | 6 | | |
| | 6.1 | 01_url_shortener | Design a URL Shortener | Caching, hashing |
| | 6.2 | 02_typeahead | Design Typeahead for Search Box | Trie, FST |
| | 6.3 | 03_instagram | Design Instagram | Fanout-on-write, blob storage |
| | 6.4 | 04_twitter | Design Twitter | Fanout hybrid (write + read) |
| | 6.5 | 05_newsfeed | Design the Newsfeed (Facebook-style) | Ranking |
| | 6.6 | 06_yt_or_netflix + 39_reddit_homepage | Design YouTube/Netflix + Reddit Homepage | CDN, hot-score |
| **02** | Event-Driven Systems | 3 | | |
| | 7.1 | 07_message_queue | Design a Distributed Message Queue | Pub/Sub, partitions, offsets |
| | 7.2 | 08_webhook_delivery | Design Webhook Delivery | Retries, HMAC, DLQ |
| | 7.3 | 09_uber_eats | Design Uber Eats | 3-sided marketplace, state machine |
| **03** | Async Jobs & Workers | 3 | | |
| | 8.1 | 10_web_crawler | Design a Web Crawler | Frontier, politeness, dedup |
| | 8.2 | 11_job_scheduler | Design a Job Scheduler | Cron, DAG, due-heap |
| | 8.3 | 12_user_data_export | Design App that Downloads User Data | Async export pipeline |
| **04** | Distributed Storage & Partitioning | 5 | | |
| | 9.1 | 13_kv_store | Design a Key-Value Store | Consistent hashing, replication |
| | 9.2 | 14_rate_limiter | Design a Rate Limiter | Token bucket, sliding window |
| | 9.3 | 15_distributed_lru | Design a Distributed LRU Cache | Sharding, peer fetch |
| | 9.4 | 16_dropbox | Design Dropbox | Chunking, dedup |
| | 9.5 | 17_s3_storage | Design Distributed Storage (S3) | Object storage, multipart |
| **05** | Transactional Systems | 3 | | |
| | 10.1 | 18_ticketmaster | Design Ticketmaster | Concurrency, seat locking |
| | 10.2 | 19_hotel_booking | Design a Hotel Booking System | Date-range, double-booking |
| | 10.3 | 20_parking_garage | Design a Parking Garage | Real-time spot allocation |
| **06** | Batch Processing & Data Pipelines | 5 | | |
| | 11.1 | 21_metrics_logging | Design a Metrics and Logging Service | Time-series, log search |
| | 11.2 | 22_apm | Design an Application Performance Monitoring | Traces, percentiles |
| | 11.3 | 23_doc_processing | Design a Document Processing Pipeline | State machine, async workers |
| | 11.4 | 24_zillow | Design Zillow | Geospatial search |
| | 11.5 | 25_weather_app | Design a Weather App | Circuit breaker, provider fanout |
| **07** | Real-Time & Collaborative Systems | 5 | | |
| | 12.1 | 26_messenger | Design Facebook Messenger | Presence, SSE |
| | 12.2 | 27_whatsapp | Design WhatsApp | Group chat, E2E (concept) |
| | 12.3 | 28_chess | Design Chess.com | Authoritative game state, validation |
| | 12.4 | 29_slack | Design Slack | Channels, threads, mentions, search |
| | 12.5 | 30_google_docs | Design Google Docs | Op log, version conflict |
| **08** | Media Streaming & Content Delivery | 4 | | |
| | 13.1 | 06_yt_or_netflix | Design YouTube | CDN, transcoding, recommend |
| | 13.2 | 06_yt_or_netflix | Design Netflix | CDN, recommendations |
| | 13.3 | 31_tiktok | Design TikTok | For You, ranking, watch signals |
| | 13.4 | 32_twitch | Design Twitch | Live streaming + chat |
| **09** | Agentic AI Systems | 6 | | |
| | 14.1 | 33_ai_support | Design an AI-Powered Customer Support System | RAG, ticket state |
| | 14.2 | 34_chatgpt | Design ChatGPT | Conversational memory, streaming |
| | 14.3 | 35_file_uploader | File Uploader for AI Chat App | Chunked resumable upload |
| | 14.4 | 36_llm_batching | Design an LLM Query Batching System | Dynamic batching |
| | 14.5 | 37_claude_code | Design Claude Code | Agent loop, tool use, sandbox |
| | 14.6 | 38_voice_ai | Design a Real-Time Voice AI | STT → LLM → TTS pipeline |
| **10** | Appendix: Concepts | 18 | | |
| | 18.1 | 99_appendix | System Design Glossary | |
| | 18.2 | 99_appendix | Top Engineering Blogs | |
| | 18.3 | 99_appendix | Caching | |
| | 18.4 | 99_appendix | CDNs | |
| | 18.5 | 99_appendix | Web Protocol Questions | |
| | 18.6 | 99_appendix | APIs | |
| | 18.7 | 99_appendix | Load Balancing | |
| | 18.8 | 99_appendix | CAP Theorem | |
| | 18.9 | 99_appendix | SQL vs NoSQL | |
| | 18.10 | 99_appendix | Database Sharding | |
| | 18.11 | 99_appendix | Replication | |
| | 18.12 | 99_appendix | Consistent Hashing | |
| | 18.13 | 99_appendix | Asynchronous Processing | |
| | 18.14 | 99_appendix | Encryption | |
| | 18.15 | 99_appendix | Authentication & Authorization | |
| | 18.16 | 99_appendix | Cloud Architecture | |
| | 18.17 | 99_appendix | Availability | |
| | 18.18 | 99_appendix | Reliability | |

**Total: 5 + 6 + 3 + 3 + 5 + 3 + 5 + 5 + 4 + 6 + 18 = 63 system design lessons + 8 overview = 71 lessons.**

The course counts 39 actual services (some modules share a service; e.g. YouTube + Netflix both use `06_yt_or_netflix`). Add `00_overview` for the intro lessons and `99_appendix` for the 18 concept lessons, and you get the full 71.

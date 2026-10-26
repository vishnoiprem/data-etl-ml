# 🎨 The 4-Phase Journey — Pictures First

> **Read this like a comic book.** Each picture shows what you build in one phase. The words under the picture tell you why you should care. If you can read a flowchart, you can read this course.

---

## 🗺️ The whole map (4 phases, 9 weeks)

```
   4th-grader view of the AI FDE course
   ════════════════════════════════════

   🌱 PHASE 1         🚗 PHASE 2         🏎️ PHASE 3         🚀 PHASE 4
   Seed               Car                Race car           Rocket ship
   ──────             ─────              ────────           ──────────
   1 week             2 weeks            2 weeks            4 weeks

   Just on            Anyone can          Survives           The team
   Mei's              use it             crashes            can extend
   laptop                                and storms         it forever

        │                  │                  │                   │
        └──────────────────┴──────────────────┴───────────────────┘
                                  │
                                  ▼
                        4 projects + 5 case studies
                        + 1 portfolio + 1 demo
```

**Translation:** You start with a seed (a CLI tool that only Mei can use). You grow it into a car (a service anyone can call). Then a race car (it survives crashes). Then a rocket ship (the team can add new parts without you).

---

## 🌱 Phase 1 — The Seed (1 week)

```
   ┌──────────────────────────────────────────────────────────┐
   │  📧 Customer email                                      │
   │  "Where is my parcel PF-1003?"                           │
   └────────────────────┬─────────────────────────────────────┘
                        │  Mei types it in
                        ▼
   ┌──────────────────────────────────────────────────────────┐
   │  🐍 Mei's terminal                                      │
   │  ┌────────────────────────────────────────────────┐      │
   │  │  $ python3 drafter.py --shipment PF-1003       │      │
   │  │                                                │      │
   │  │  👉 reads shipments.json    (the tracker)      │      │
   │  │  👉 reads style-guide.md    (how to talk)      │      │
   │  │  👉 asks the LLM            (write a draft)    │      │
   │  │  👉 prints the draft        (Mei copies it)    │      │
   │  └────────────────────────────────────────────────┘      │
   └────────────────────┬─────────────────────────────────────┘
                        │  prints
                        ▼
   ┌──────────────────────────────────────────────────────────┐
   │  ✉️  Draft: "Hi! Your parcel PF-1003 is in customs."      │
   └──────────────────────────────────────────────────────────┘

   😟 Problem:  only Mei can use it.  It lives on her laptop.
                When Mei is on vacation, the drafter doesn't exist.
```

**The motivation:** Mei is one person. If only she can use the drafter, only her customers get fast replies. The other 11 people at PacificFreight have to write every email by hand. **That's why we need Phase 2.**

---

## 🚗 Phase 2 — The Car (2 weeks)

```
                    ┌────────────────────────┐
                    │  📧 Customer email     │
                    │  "Where is my parcel?"  │
                    └───────────┬────────────┘
                                │  HTTP POST
                                ▼
   ┌────────────────────────────────────────────────────────┐
   │  🚗  FastAPI service  (runs on Daniel's VM)            │
   │                                                        │
   │   🟢 GET  /health        ← "are you alive?"           │
   │   📨 POST /draft         ← "write me a draft"         │
   │   🔍 POST /retrieve      ← "find the right chunks"    │
   │   📊 POST /eval          ← "grade yourself"           │
   │                                                        │
   │   (anyone at PacificFreight can call this)             │
   └────┬──────────────┬──────────────┬────────────────────┘
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌──────────┐
   │ 🤖 Mock │   │ 📚 Mock │   │ 📋 30-row │
   │  LLM    │   │  store  │   │  eval set │
   │         │   │         │   │           │
   │ "I'm a  │   │ "I find │   │ "you got  │
   │  fake   │   │  the    │   │  78%      │
   │  AI"    │   │  right  │   │  right!"  │
   │         │   │  stuff" │   │           │
   └─────────┘   └─────────┘   └──────────┘

   📄 You also write 6 documents:
   ┌────────────────────────────────────────────┐
   │ 📋 discovery-deck.md     (what we heard)   │
   │ 📋 pacificfreight-prd.md (what to build)  │
   │ 📋 design-doc.md         (how to build)   │
   │ 📋 ADR-0001-fastapi.md   (why FastAPI)    │
   │ 📋 ADR-0002-mock-store.md(why mock store) │
   │ 📋 ADR-0003-regression.md(why 5% trip)    │
   └────────────────────────────────────────────┘

   ✅ End of Phase 2:  13/13 pytest cases pass.
   🎉 The car drives!
```

**The motivation:** Now the drafter is a car, not a seed. Anyone at the company can ride in it. It has 4 doors (endpoints) and seatbelts (tests). The 6 documents are the owner's manual — when a new engineer joins, they read the manual and know how the car works.

---

## 🏎️ Phase 3 — The Race Car (2 weeks)

The car drives. But what if the road is bad? What if the engine catches fire? **Phase 3 adds the safety gear.**

```
   Same Phase 2 service, but now with safety gear bolted on:

   ┌─────────────────────────────────────────────────────────┐
   │  🏎️  Hardened FastAPI service                           │
   │                                                         │
   │   ⚡ /draft/stream   ← Mei sees the first word in 200ms │
   │   👍 /feedback       ← Mei says "good" or "bad"         │
   │   📈 /metrics        ← Prometheus counters             │
   │   🛡️  /circuit/state  ← "is the engine on fire?"        │
   └────┬──────────────┬──────────────┬──────────────────────┘
        │              │              │
        ▼              ▼              ▼

   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ 🧠 HYBRID  │  │ 🔌 CIRCUIT │  │ 🛡️  CADDY  │
   │  RETRIEVER │  │  BREAKER   │  │  (TLS +    │
   │            │  │            │  │  edge rate │
   │ BM25 ✚    │  │ If OpenAI  │  │  limiting) │
   │ dense ✚   │  │ is down    │  │            │
   │ RRF merge │  │ for 30s,   │  │ Encrypts   │
   │            │  │ use the    │  │ traffic    │
   │ beats the  │  │ cached     │  │ + blocks   │
   │ mock store │  │ last-good  │  │ bad guys   │
   │ on real    │  │ answer     │  │ at the     │
   │ queries    │  │ (no 503!)  │  │ door       │
   └────────────┘  └────────────┘  └────────────┘

   📄 You also write 3 ops docs (the race team):
   ┌─────────────────────────────────────────────────┐
   │ 📕 runbook.md           "what to do at 2am"     │
   │ 📋 raci.md              "who decides what"      │
   │ 📞 on-call-rotation.md  "whose phone rings"     │
   └─────────────────────────────────────────────────┘

   📄 And 3 consulting docs (the racing strategy):
   ┌─────────────────────────────────────────────────┐
   │ 👥 stakeholder-map.md   Mei/Sarah/Daniel + exec │
   │ 🔄 iteration-cadence.md Mon daily/week/month    │
   │ 🪪 5-question handoff   "FDE has left" — pass?  │
   └─────────────────────────────────────────────────┘

   ✅ End of Phase 3:  13/13 pytest still pass.
   🏁 The race car has seatbelts, airbags, and a pit crew.
```

**The motivation:** When OpenAI goes down (it will), the drafter doesn't crash — it shows Mei the last good answer. When Mei's email has a customer's phone number, it doesn't leak into the logs. When Mei accidentally loops the drafter 1000 times, the rate limiter says "no more, that would cost $50." The 3 ops docs are the **pit crew** — when something breaks, the customer can fix it without you.

---

## 🚀 Phase 4 — The Rocket Ship (4 weeks)

Now the drafter is a race car. **But what if the team wants to add new features?** A new tool? A new agent? A new cheaper engine? **Phase 4 turns the car into a rocket ship that the team can re-build without you.**

```
   The Phase 3 race car is now a rocket ship with 4 new modules bolted on:

                  ┌──────────────────────────┐
                  │  🚀 Phase 4 Rocket       │
                  │                          │
                  │   Phase 3 service        │
                  │       +                  │
                  │   4 new modules:         │
                  └──────┬───────────────────┘
                         │
        ┌────────────────┼────────────────┬──────────────────┐
        │                │                │                  │
        ▼                ▼                ▼                  ▼

   ┌──────────┐    ┌──────────┐    ┌──────────┐       ┌──────────┐
   │ 🔧 MCP   │    │ 🤖 AGENT │    │ 🧠 SLM   │       │ 📊 DATA  │
   │  server  │    │  squad   │    │  trained │       │  analyst │
   │          │    │          │    │  by you  │       │          │
   │ Mei adds │    │ 3 agents │    │          │       │ A NEW    │
   │ new tools│    │ handle   │    │ Qwen 1.5B│       │ customer,│
   │ without  │    │ complex  │    │ trained  │       │ a NEW    │
   │ redeploy-│    │ multi-   │    │ on Mei's │       │ domain — │
   │ ing:     │    │ shipment │    │ 4 weeks  │       │ proves   │
   │          │    │ cases    │    │ of       │       │ the FDE  │
   │ • refund │    │          │    │ drafts   │       │ pattern  │
   │ • trans- │    │ • Mei    │    │          │       │ transfers│
   │   late   │    │ • Sarah  │    │ 5% of    │       │          │
   │ • escalate   │ • Daniel │    │ GPT cost │       │ • sandbox│
   │          │    │          │    │ 91% qual │       │ • block- │
   │ (no eng  │    │ (each has│    │          │       │   list   │
   │  needed) │    │  own     │    │ (the cost│       │ • new    │
   │          │    │  circuit)│    │  ceiling │       │   design │
   │          │    │          │    │  stays!) │       │   doc    │
   └──────────┘    └──────────┘    └──────────┘       └──────────┘

   📚 And 5 case studies (the lessons learned):
   ┌────────────────────────────────────────────────────────┐
   │ 📖 engagement-1-pf-drafter.md    the whole story      │
   │ 📖 engagement-2-pivot.md         "we said NO"         │
   │ 📖 engagement-3-postmortem.md    "the 10-min outage"  │
   │ 📖 engagement-4-slm-cost.md      "5% cost, 91% qual"  │
   │ 📖 engagement-5-handoff.md       "FDE has left" test  │
   └────────────────────────────────────────────────────────┘

   🎤 And 1 capstone presentation:
   ┌────────────────────────────────────────────────────────┐
   │ 🎬 7 slides, 10 minutes, live demo to the panel       │
   │                                                        │
   │  1. the FDE pattern              (1 min)               │
   │  2. PF drafter live demo         (3 min)               │
   │  3. MCP server live demo         (2 min)               │
   │  4. multi-agent trace            (1 min)               │
   │  5. SLM cost model               (1 min)               │
   │  6. 5-question handoff test      (1 min)               │
   │  7. what I'd do differently      (1 min)               │
   └────────────────────────────────────────────────────────┘

   ✅ End of Phase 4:  25/25 pytest pass.
   🌍 The rocket flies itself.
```

**The motivation:** The car was great, but it only had one engine. The rocket has 4 engines, and the team can add a 5th without calling the engineer who built it. The SLM is the cheap engine — it costs 5% of the expensive one and does 91% as well. The data analyst is a new rocket for a new customer — proves the same design works for someone else.

---

## 🎯 The big "WHY" (one picture)

```
   Most AI projects die here.                  This course takes you here.
   ════════════════════════                    ═════════════════════════

       📺 DEMO                                       📺 DEMO
        │ works                                       │ works
        ▼                                             ▼
       🧪 PILOT                                      🧪 PILOT
        │ works                                       │ works
        ▼                                             ▼
       😱 "WHO OWNS                                🏭 PRODUCTION
        │  THIS?"                                    │ service
        ▼                                            ▼
       🪦 nobody                  ───────▶         📕 RUNBOOK
        │  the project                             📋 RACI
        ▼  dies                                     📞 ON-CALL
       💀 dead                                      │
                                                    ▼
                                                  ✅ 5-question
                                                     handoff test
                                                    │
                                                    ▼
                                                  🚪 FDE exits.
                                                     System keeps
                                                     running.
                                                     🎉
```

**The story in one line:** Most AI projects die because nobody wrote the runbook. This course makes you write the runbook, the RACI, the on-call rotation, the handoff test. By the end, the customer can fire you tomorrow and the system runs without you. **That is the FDE's job — to make themselves unnecessary.**

---

## ⏱️ How long does the whole course take?

```
   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
   │ PHASE 1 │    │ PHASE 2 │    │ PHASE 3 │    │ PHASE 4 │
   │  🌱     │    │  🚗     │    │  🏎️     │    │  🚀     │
   │         │    │         │    │         │    │         │
   │  1 wk   │ ─▶ │  2 wks  │ ─▶ │  2 wks  │ ─▶ │  4 wks  │
   │         │    │         │    │         │    │         │
   │  ~300   │    │  ~600   │    │ ~1500   │    │ ~3000   │
   │  lines  │    │  lines  │    │  lines  │    │  lines  │
   └─────────┘    └─────────┘    └─────────┘    └─────────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                              │
                              ▼
                    ⏱️  ~9 weeks total
                    📦  ~5400 lines of code
                    📄  ~25 documents
                    🎯  25/25 tests pass
                    🎤  1 capstone presentation
```

That's about **2 months full-time** or **4-5 months part-time**. By the end, you have a working service, a portfolio of 4 projects, 5 case studies, and a demo you can show in a job interview. Enough to walk in and say: **"I build AI services that survive the customer."**

# 07 — Using the Whiteboard

> **Lesson 7 of 9 — Tips & Frameworks** · ~10 min

The 5 whiteboard rules, the 3 common pitfalls,
and the senior SA move: organization, labels,
and cleanup. The whiteboard is a senior tool;
use it deliberately.

---

## 1. Why the whiteboard matters

The whiteboard (or Excalidraw, or shared Miro)
is the surface where the architecture round
plays out. The candidate's whiteboard *style*
signals senior SA as much as the architecture
itself.

A messy whiteboard with no labels reads as "I
don't think in structures." A clean whiteboard
with clear labels reads as "I organize my
thinking for the customer." The whiteboard is
*itself* a signal.

The 5 rules below are the senior SA patterns.

---

## 2. The 5 whiteboard rules

### Rule 1: Logical-level, not physical-level

Draw services, not machines. Boxes for
components, arrows for data flow, not specific
EC2 instance types or RDS class names.

**What it looks like (good):**

```
   [API Gateway] → [Lambda] → [DynamoDB]
                          ↘
                           [S3]
```

**What it looks like (bad):**

```
   [ALB 7G capacity, t3.medium] →
   [Lambda 1024MB, 5 concurrent] →
   [DynamoDB on-demand, 2 tables]
```

The bad version is over-detailed. The good
version is clean and reads in 5 seconds.

### Rule 2: Direction-of-flow arrows

Every arrow has a direction. The customer
should be able to read the diagram in 10
seconds by following the arrows.

**What it looks like (good):**

```
   [Front-end] ──→ [API] ──→ [Service] ──→ [DB]
        ↑                                     ↓
        └────────── [Response] ──────────────┘
```

**What it looks like (bad):**

```
   [Front-end] —— [API]
   [Service]  —— [DB]   (no direction)
```

The bad version is unreadable. Without
direction, the customer doesn't know what
flows where.

### Rule 3: Label everything

Every box has a name. Every arrow has a label.
Every region (e.g., "us-east-1") is marked.

**What it looks like (good):**

```
   [API Gateway (us-east-1)]
        │
        │ HTTPS / JSON
        ↓
   [Lambda: get-user (us-east-1)]
        │
        │ DDB GetItem
        ↓
   [DynamoDB: users table (us-east-1)]
```

**What it looks like (bad):**

```
   [Box1] → [Box2] → [Box3]
```

The bad version is meaningless. The labels
are the substance.

### Rule 4: Mark the hot path

For latency-critical data flows, mark the hot
path with a different color or thicker line.
The customer can see at a glance which parts
of the architecture are performance-critical.

**What it looks like (good):**

```
   [User] ═══════> [API] ═══════> [Feature Store]
       (hot path, double-line)        (< 10ms p99)
                  ↓
              [Cold storage]
              (single-line)
```

**What it looks like (bad):**

```
   All arrows look the same.
```

The hot-path marking signals "I've thought
about which part matters most."

### Rule 5: Annotate failure modes

For each major component, sketch the failure
mode. "If [component] fails, [recovery]."
The annotation signals "I've thought about
what goes wrong."

**What it looks like (good):**

```
   [DynamoDB Global Tables]
       us-east-1            eu-west-1
         ↓ (active)           ↓ (replica)
         ↘────── 5s lag ──────↙
       (failover, RTO 1min)
```

**What it looks like (bad):**

```
   No failure modes anywhere.
```

The annotation signals "I've thought about
production reality, not just happy-path design."

---

## 3. The 3 common pitfalls

### Pitfall 1: Drawing too much

You draw 20 boxes and 30 arrows in 60 seconds,
and the customer can't follow. The whiteboard
becomes noise.

**Fix:** Start with 3-5 boxes. Add boxes as
needed. The senior SA move is *progressive
elaboration*: start simple, add complexity as
the conversation requires.

### Pitfall 2: No spatial organization

You draw boxes in random positions. The
customer has no mental map of the system.

**Fix:** Use spatial conventions:
- Top-to-bottom or left-to-right data flow.
- External systems on the edge (top or left).
- Internal services in the middle.
- Data stores at the bottom or right.
- User-facing components at the top or left.

The conventions are *implicit*. The customer
reads the diagram faster because the conventions
match their expectations.

### Pitfall 3: Forgetting the legend

If you use colors, thicknesses, or symbols
that aren't obvious, you need a legend. Without
it, the customer has to guess.

**Fix:** If you use any non-obvious notation,
add a 1-line legend in the corner. The legend
is small; the value is real.

---

## 4. The "before you draw" routine

The 30 seconds before you start drawing:

1. **Confirm the constraints.** Ask 2-3 clarifying
   questions if you haven't already. (See
   Module 03 Lesson 10.)
2. **State the plan.** "I'll start with the data
   flow, then the processing layer, then the
   storage. Let me know if you want me to go
   deeper on any part."
3. **Sketch the boxes first.** Draw 3-5 boxes
   in their spatial positions *before* drawing
   any arrows.
4. **Connect with arrows.** Once the boxes are
   in position, add the arrows.
5. **Label and annotate.** Once the structure
   is clear, add labels and failure modes.

The 5-step routine takes 30 seconds and saves
the diagram from being chaotic.

---

## 5. The "during the draw" routine

While you're drawing, 3 habits:

1. **Speak as you draw.** "I'm putting the API
   Gateway here, because it's the entry point.
   The Lambda function sits behind it. The
   DynamoDB is the data store." The narration
   makes the diagram understandable.
2. **Pause to check in.** After the basic structure
   is drawn (3-5 minutes), pause and check: "Does
   this match your understanding of the system, or
   is there a part that's different?"
3. **Acknowledge corrections.** If the customer
   points out a wrong detail, fix it *immediately*.
   Don't defend; adapt.

The 3 habits make the whiteboard a *conversation*,
not a performance.

---

## 6. The "cleanup" move

The senior SA move at the end of the diagram:
*clean up*.

If you've crossed out parts, rewrite them.
If you've drawn things that don't matter, erase
them. The final diagram should be readable.

The cleanup takes 30-60 seconds, but it's the
*signal of senior SA*. A messy final diagram
reads as "I lose track of complexity." A clean
final diagram reads as "I organize complexity."

---

## 7. The 3 whiteboard formats

3 whiteboard formats, ranked by ease:

| Format | Pros | Cons |
|---|---|---|
| **Physical whiteboard** | Tactile; easy to draw | Hard to share remotely; needs cleanup |
| **Excalidraw** | Hand-drawn feel; sharable; easy to draw | Less polished than a tool |
| **Miro / FigJam** | Polished; sharable; sticky notes | Slower to draw; less natural |

For in-person interviews, the physical whiteboard
is fine. For video interviews, Excalidraw is the
senior SA move — it's the closest to the physical
whiteboard while being shareable.

Practice with the format you'll use in the
interview. Don't learn a new format on the day.

---

## Try it

For your next 3 architecture mocks, use a
whiteboard (physical or Excalidraw) and apply
the 5 rules. Practice the 5-step "before you
draw" routine and the 3 "during the draw" habits.

After each mock, look at the final diagram and
ask: "Is it readable? Are the labels clear? Is
the hot path marked? Are the failure modes
annotated?" If any answer is "no," fix it
before the next mock.

By the 3rd mock, the whiteboard rules will be
in muscle memory. That's the architecture round
of the interview.

# Building Data-Driven Applications and ML Pipelines With Golang

### Everything you need to know to solve 80% of your data problems — without Spark, Hadoop, or a Kubernetes cluster

*By Prem Vishnoi*

---

## Why This Matters

By 2020, the world had already produced 40× more bytes of data than there are stars in the observable universe. Every minute we generate millions of tweets, videos, sensor readings, transactions, and logs. The *Data Never Sleeps* visualization (now in its 7th edition) makes the scale visceral.

Most engineers react to this with one reflex: **"We need big data tooling."** Out come Hadoop, Spark, Flink, Airflow, Kafka, and a cluster that takes longer to spin up than the query takes to run.

Here's the uncomfortable truth: **most applications don't process data at that scale.** A surprising number of "big data" problems are actually medium-data problems dressed up for a party they were never invited to. There is a well-documented pattern of teams reaching for Spark, spending 15 minutes on cluster ceremony, only to realize a direct SQL query would have finished in 200 milliseconds.

This article is about the other path — using **Go's built-in primitives (goroutines, channels, interfaces)** to build data pipelines that are fast, deployable as a single binary, and capable of handling most real-world workloads without the infrastructure nightmare.

---

## What Is a Data Pipeline, Really?

> A **data pipeline** is a process that takes input data through a series of transformation stages, producing data as output.

A **machine learning pipeline** is a specialization:

> A process that takes *data + code* as input and produces a *trained ML model* as output.

Both follow the same architectural skeleton — the classic **ETL (Extract → Transform → Load)** shape:

```
┌─────────┐   ┌────────┐   ┌─────────┐   ┌────────┐   ┌─────────┐
│ Ingest  │──▶│ Store  │──▶│ Process │──▶│ Store  │──▶│  Serve  │
│ (raw)   │   │ (raw)  │   │ (ETL)   │   │(clean) │   │  (API)  │
└─────────┘   └────────┘   └─────────┘   └────────┘   └─────────┘
```

In this article we focus on **Ingest + Process** — the two stages where Go shines brightest.

---

## The "Taco Bell Programming" Principle

Before we touch any Go code, here's a humbling example from Martin Kleppmann's *Designing Data-Intensive Applications* — analyzing an access log with nothing but Unix pipes:

```bash
cat access.log \
  | awk '{print $7}' \
  | sort \
  | uniq -c \
  | sort -rn \
  | head -n 5
```

Five small programs. Composed with pipes. Each does one thing well.

This deceptively simple pipeline is surprisingly powerful:

- It **spills to disk** automatically when data doesn't fit in RAM.
- It runs **stages in parallel** across multiple cores.
- It's **debuggable** — you can inspect any stage.

The limitation: `awk` is Turing-complete but syntactically painful. Anything more complex than "count top 5 URLs" becomes a Google-and-trial-and-error exercise.

This approach is nicknamed **Taco Bell Programming** — reuse a small set of ingredients to cook up surprisingly complex meals. Go gives us a way to do **advanced Taco Bell programming**: use goroutines for parallelism, channels for composition, and ship the whole thing as a single binary.

---

## Why Go Specifically?

Go was built for concurrent, networked systems. For data pipelines, three features matter most:

| Feature | What it gives you |
|---|---|
| **Goroutines** | Cheap concurrency. Spawn 10,000 workers for fan-out without breaking a sweat. |
| **Channels** | Typed, synchronous communication between stages. Pipelines without queues. |
| **Single static binary** | Deploy with `scp`. No runtime, no JVM, no container orchestration required. |

Add the standard library (`sync`, `context`, `encoding/json`, `bufio`), and you have 90% of what a pipeline framework gives you — minus the framework.

---

## The Core Memory Challenge

Before writing code, let's talk about the main enemy: **memory**.

When your working set exceeds RAM, the OS starts swapping to disk. Disk I/O is an *order of magnitude* slower than memory. Your pipeline doesn't crash — it just becomes horrifyingly slow.

Three techniques push the ceiling up without adding hardware:

### 1. Compression (representational, not gzip)

Don't store a boolean as the string `"true"` (4 bytes + pointer overhead). Store it as a `bool` (1 byte) or a bit in a bitmap (1/8 byte). Choose the smallest data type that holds the value. A `uint8` age field beats an `int64` by 8×.

### 2. Chunking (MapReduce in spirit)

Cut the dataset into logical pieces. Process each in parallel. Merge results at the end.

The classic mental model: **counting books in a library**. One person per shelf. Then everyone adds their count at the end. That's `map` followed by `reduce`.

### 3. Indexing

Don't scan everything every time. Maintain a summary structure (index) that points to where data lives. Log rotation is a real-world example — hour-level files plus an index tell you exactly which file to open for a given timestamp.

---

## The Three Building Blocks of a Go Pipeline

Every pipeline we'll build is made of three primitives:

### 1. Generator (producer)

A function that **returns a channel** of values. Its only job is to emit.

```go
// Type: generator of integers
type IntGenerator func() <-chan int
```

Use cases: stream numbers, read a file line-by-line, query a DB cursor, scrape a website.

### 2. Processor (transformer)

A function that **takes a channel and returns a channel**. Middle of the pipeline.

```go
// Type: transforms one int channel into another
type IntProcessor func(<-chan int) <-chan int
```

Use cases: filtering, aggregation, deduplication, validation, enrichment.

### 3. Consumer (sink)

A function that **takes a channel and does something terminal** — prints, writes to disk, pushes to an API.

```go
type IntConsumer func(<-chan int)
```

Notice the pattern: each stage returns a *function* that returns the expected type. This is the same pattern Go developers use for HTTP middleware — an outer function captures config, an inner function does the work.

---

## Your First Pipeline: A Working Example

Let's build a number-squaring pipeline end to end. This compiles and runs as-is.

```go
package main

import "fmt"

// ---------- Generator ----------
// Emits the given integers on a channel.
func NumberGenerator(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out) // stage that owns the channel closes it
        for _, n := range nums {
            out <- n
        }
    }()
    return out
}

// ---------- Processor ----------
// Squares every integer it receives.
func SquareProcessor(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            out <- n * n
        }
    }()
    return out
}

// ---------- Consumer ----------
// Prints every value until the channel closes.
func PrintConsumer(in <-chan int) {
    for n := range in {
        fmt.Println(n)
    }
}

func main() {
    // Compose the pipeline: 1..5 → square → print
    PrintConsumer(SquareProcessor(NumberGenerator(1, 2, 3, 4, 5)))
    // Output: 1 4 9 16 25
}
```

**What just happened?**

Three goroutines ran concurrently, linked by two channels. The generator produced values as fast as the processor could consume them, which was as fast as the consumer could print them. Backpressure is built in — if the consumer slows down, the processor blocks on `out <- n*n`, which blocks the generator on `out <- n`. No queues. No frameworks. Just the language.

---

## Scaling Out: Fan-Out and Fan-In

One processor goroutine uses one CPU core. To use all 16 cores on your box, you **fan out** the work to multiple workers, then **fan in** their outputs.

Here's a real pipeline that aggregates log counts from multiple files in parallel:

```go
package main

import (
    "bufio"
    "fmt"
    "os"
    "sync"
)

// Generator: stream lines from a single file.
func FileLineGenerator(path string) <-chan string {
    out := make(chan string)
    go func() {
        defer close(out)
        f, err := os.Open(path)
        if err != nil {
            return
        }
        defer f.Close()
        scanner := bufio.NewScanner(f)
        for scanner.Scan() {
            out <- scanner.Text()
        }
    }()
    return out
}

// Processor: count lines containing "ERROR".
func ErrorCounter(in <-chan string) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        count := 0
        for line := range in {
            if containsError(line) {
                count++
            }
        }
        out <- count
    }()
    return out
}

func containsError(line string) bool {
    // simplified — a real impl would use strings.Contains
    for i := 0; i+5 <= len(line); i++ {
        if line[i:i+5] == "ERROR" {
            return true
        }
    }
    return false
}

// Fan-in: merge N channels into one using a WaitGroup.
func Merge(channels ...<-chan int) <-chan int {
    var wg sync.WaitGroup
    out := make(chan int)

    output := func(c <-chan int) {
        defer wg.Done()
        for v := range c {
            out <- v
        }
    }

    wg.Add(len(channels))
    for _, c := range channels {
        go output(c)
    }

    // Close out once all inputs are drained.
    go func() {
        wg.Wait()
        close(out)
    }()

    return out
}

func main() {
    files := []string{"app1.log", "app2.log", "app3.log"}

    // Fan-out: one processor per file.
    channels := make([]<-chan int, len(files))
    for i, f := range files {
        channels[i] = ErrorCounter(FileLineGenerator(f))
    }

    // Fan-in + aggregate.
    total := 0
    for partial := range Merge(channels...) {
        total += partial
    }
    fmt.Printf("Total errors across %d files: %d\n", len(files), total)
}
```

This is MapReduce — written in ~50 lines, no cluster, no YAML, no Jenkins job. It scales linearly until you run out of CPU cores or disk bandwidth.

---

## Graceful Shutdown: The `done` Channel Pattern

Real pipelines break. A downstream processor hits a malformed record and errors out. Now the upstream goroutine is blocked forever on a `chan <- value` send that nobody will ever receive. Congratulations, you've leaked a goroutine.

The idiomatic solution: a **done channel** that signals "stop everything."

```go
func SquareProcessor(done <-chan struct{}, in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            select {
            case out <- n * n:
                // normal path
            case <-done:
                // cancelled from above — exit cleanly
                return
            }
        }
    }()
    return out
}

func main() {
    done := make(chan struct{})
    defer close(done) // triggers shutdown across all stages

    pipeline := SquareProcessor(done, NumberGenerator(1, 2, 3))
    for v := range pipeline {
        fmt.Println(v)
    }
}
```

**Rules of thumb for leak-free pipelines:**

1. The stage that **owns** a channel is responsible for closing it.
2. Every `send` inside a goroutine should be wrapped in a `select` with a `done` case.
3. Use `context.Context` in production — it gives you cancellation + deadlines + request-scoped values for free.

---

## Real-Time Streams: Generators That Never Close

So far every generator has terminated. Streaming is different — the generator runs forever, emitting values as they arrive. The implementation change is tiny:

```go
import (
    "math/rand"
    "time"
)

func RandomStream() <-chan int {
    out := make(chan int)
    go func() {
        for {
            out <- rand.Intn(1000)
            time.Sleep(100 * time.Millisecond) // artificial pacing
        }
        // note: no close() — this runs until process exit
    }()
    return out
}
```

### Rate Limiting with a Ticker

If a stream is too fast — burning CPU, hitting API quotas, overwhelming a database — throttle it:

```go
func Throttle(in <-chan int, rate time.Duration) <-chan int {
    out := make(chan int)
    throttle := make(chan struct{})

    // Ticker fills the throttle channel at the desired rate.
    go func() {
        ticker := time.NewTicker(rate)
        defer ticker.Stop()
        for range ticker.C {
            throttle <- struct{}{}
        }
    }()

    go func() {
        defer close(out)
        for v := range in {
            <-throttle // wait for permission
            out <- v
        }
    }()

    return out
}

// Usage: one value per 500ms max
limited := Throttle(RandomStream(), 500*time.Millisecond)
```

This is a **token bucket** in 20 lines. Replace `time.NewTicker` with `golang.org/x/time/rate.Limiter` for burst-aware rate limiting in production.

---

## ML Pipelines: Same Bones, Different Meat

An ML pipeline is just a data pipeline with a training stage bolted on. The Go primitives don't change; the processors do.

A typical flow:

```
ingest raw events  →  clean/dedupe  →  feature extraction  →  train model  →  serialize (ONNX, pkl, pb)  →  serve via API
```

In Go, each stage is a processor with a typed channel. You can:

- Ingest from Kafka/Kinesis with a generator.
- Stream through feature extractors (e.g., one-hot encoding, hashing, bucketization).
- Shell out to a Python training script — or use Gorgonia / Goro / ONNX-Go for native Go training.
- Serve predictions from a `net/http` handler that holds the loaded model.

The crucial insight: **the inference stage is where Go dominates**. Training in Python is fine (that's where the ecosystem lives), but serving at 100k req/sec with p99 < 10ms is where a Go service shines. Load your serialized model once at startup and hand it to request handlers through a read-only pointer.

---

## When Channels Aren't Enough: Go Open Source Projects

For simple to moderate pipelines, goroutines + channels are all you need. For production systems with heterogeneous sources, delivery guarantees, and ops visibility, three projects stand out.

### Benthos (now Redpanda Connect)

A stream processor written in Go. You describe inputs, processors, and outputs in YAML; Benthos handles connectors, acknowledgments, retries, batching, and observability.

```yaml
input:
  kafka:
    addresses: [kafka:9092]
    topics: [raw_events]

pipeline:
  processors:
    - bloblang: |
        root.user_id = this.user.id
        root.event_ts = this.timestamp.ts_parse("2006-01-02T15:04:05Z")
        root.clean = true

output:
  kafka:
    addresses: [kafka:9092]
    topic: clean_events
```

Under the hood, Benthos uses the same `input → processor → output` abstraction we built above, but with acknowledgments threaded through — every message carries a response channel so the source can be told "yes, this was committed downstream" before removing it from the queue.

**When to use it:** when your pipeline config should live outside your binary, and when you need 50+ connectors out of the box.

### Bigslice

A distributed computing framework by Grail (now part of Insitro) for cluster-scale Go. Think Spark, but server-less and dramatically simpler to deploy. You write functional transformations on slices; Bigslice distributes them across EC2 or Kubernetes workers.

**When to use it:** when a single machine really isn't enough — large genomics, ad-tech, or scientific workloads.

### Otto / Go-streams / similar

Lightweight streaming APIs on top of channels. Good for teaching and prototyping; most production teams end up either using plain channels or graduating to Benthos.

---

## Principles for Pipeline Builders

A recap of the lessons that will save you months:

1. **Default to plain Go.** Channels + goroutines will take you further than you think.
2. **Measure before you cluster.** A 50GB dataset on one SSD with 64GB RAM is not a Spark problem.
3. **Own your channel closures.** Whoever owns the channel closes it — everyone else only reads or writes.
4. **Plumb a `done` signal everywhere.** Or use `context.Context`. Never ship a pipeline without cancellation.
5. **Fan out on CPU-bound stages, fan in before a serial sink.** That's the basic parallelism recipe.
6. **Buffer sparingly.** The creator of Benthos recommends against buffers in most cases — they hide backpressure problems rather than solving them.
7. **Don't put a queue between two services that could just be one pipeline.** Kafka is not free. Operationally it's quite expensive.
8. **Benchmark with realistic data.** The difference between 1k and 1M records often exposes algorithmic choices that looked fine in tests.

---

## The Single-Binary Superpower

Perhaps the most underrated advantage of using Go for data work: **deployment**.

```bash
GOOS=linux GOARCH=amd64 go build -o pipeline ./cmd/pipeline
scp pipeline server:/usr/local/bin/
ssh server 'systemctl restart pipeline'
```

That's it. No JRE to match. No Python virtualenv. No Docker image (unless you want one). No Helm chart. No Kubernetes. Your pipeline boots in milliseconds and uses less RAM than a Spark driver uses to say "hello."

For 80% of data pipelines — the ones that don't trend on Hacker News — this is exactly what you want.

---

## Further Reading

- **Martin Kleppmann — *Designing Data-Intensive Applications*** (O'Reilly). The single best book on data systems.
- **Rob Pike — *Go Concurrency Patterns: Pipelines and Cancellation***. The canonical blog post from the Go team.
- **Sameer Ajmani — *Advanced Go Concurrency Patterns*** (Google I/O talk).
- **Benthos / Redpanda Connect docs** — [docs.redpanda.com/redpanda-connect](https://docs.redpanda.com/redpanda-connect/)
- **Bigslice** — [bigslice.io](https://bigslice.io)
- **Gorgonia** (Go-native ML) — [gorgonia.org](https://gorgonia.org)
- **Data Never Sleeps 7.0** — Domo's visualization of data volumes per minute.

---

## Closing Thought

Big data tooling exists for a reason — there really are workloads that need a thousand nodes. But there are far more workloads that need a laptop, a tight loop, and a few goroutines.

Start simple. Profile. Measure. Only add complexity when the data refuses to cooperate. You'll be surprised how often Go alone is the final answer.

*Happy piping.*

# Go Pipeline — High-Throughput Event Processing for Dataflow
## Production-Grade Go (Golang) for Apache Beam / Dataflow

---

## 🎯 Use Case
**High-throughput event normalization:** 1M+ events/sec, sub-10ms latency, JSON → Avro → BigQuery, with schema validation, dead-letter, and custom metrics. Go chosen for: lower memory footprint, faster startup, better Dataflow runner support (Beam Go SDK).

---

```go
// go_pipeline.go
//
// High-throughput event processing pipeline for Google Cloud Dataflow (Beam Go SDK).
// Demonstrates: JSON parsing, schema validation, Avro serialization, 
// side inputs (via external service), custom metrics, dead-letter handling.
//
// Build & Run:
//   go mod init github.com/yourorg/dataflow-go-pipeline
//   go get github.com/apache/beam/sdks/v2/go/pkg/beam
//   go get github.com/apache/beam/sdks/v2/go/pkg/beam/io/pubsub
//   go get github.com/apache/beam/sdks/v2/go/pkg/beam/io/bigquery
//   go get github.com/linkedin/goavro/v2
//
//   # Flex Template
//   gcloud dataflow flex-template build gs://$BUCKET/templates/go-pipeline \
//       --image=gcr.io/$PROJECT/dataflow-go:latest \
//       --sdk-language=GO

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/apache/beam/sdks/v2/go/pkg/beam"
	"github.com/apache/beam/sdks/v2/go/pkg/beam/io/pubsubio"
	"github.com/apache/beam/sdks/v2/go/pkg/beam/io/bigqueryio"
	"github.com/apache/beam/sdks/v2/go/pkg/beam/log"
	"github.com/apache/beam/sdks/v2/go/pkg/beam/register"
	"github.com/apache/beam/sdks/v2/go/pkg/beam/transforms/stats"
	"github.com/apache/beam/sdks/v2/go/pkg/beam/x/beamx"
	"github.com/linkedin/goavro/v2"
)

// ─── Constants & Configuration ────────────────────────────────────────────

const (
	// Avro schema for normalized events (matches BigQuery table schema)
	eventAvroSchema = `{
		"type": "record",
		"name": "NormalizedEvent",
		"namespace": "com.example.dataflow",
		"fields": [
			{"name": "event_id", "type": "string"},
			{"name": "customer_id", "type": "string"},
			{"name": "event_timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}},
			{"name": "event_type", "type": ["null", "string"], "default": null},
			{"name": "channel", "type": ["null", "string"], "default": null},
			{"name": "amount", "type": ["null", "double"], "default": null},
			{"name": "currency", "type": ["null", "string"], "default": null},
			{"name": "metadata", "type": ["null", {"type": "map", "values": "string"}], "default": null},
			{"name": "processed_timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}},
			{"name": "pipeline_version", "type": "string"}
		]
	}`

	// Valid event types (extend as needed)
	validEventTypes = "purchase,refund,page_view,signup,login,logout,add_to_cart,remove_from_cart"

	// Pipeline version for schema evolution tracking
	pipelineVersion = "1.2.0"
)

// ─── Custom Metrics ────────────────────────────────────────────────────────

var (
	eventsProcessed   = beam.NewCounter("event_pipeline", "events_processed")
	eventsValidated   = beam.NewCounter("event_pipeline", "events_validated")
	eventsEnriched    = beam.NewCounter("event_pipeline", "events_enriched")
	eventsDropped     = beam.NewCounter("event_pipeline", "events_dropped")
	eventsDeadLettered = beam.NewCounter("event_pipeline", "events_dead_lettered")
	processingLatency = beam.NewDistribution("event_pipeline", "processing_latency_ms")
	schemaErrors      = beam.NewCounter("event_pipeline", "schema_errors")
	avroErrors        = beam.NewCounter("event_pipeline", "avro_serialization_errors")
)

// ─── Data Structures ───────────────────────────────────────────────────────

// RawEvent represents the incoming Pub/Sub message
type RawEvent struct {
	EventID       string                 `json:"event_id"`
	CustomerID    string                 `json:"customer_id"`
	EventTS       string                 `json:"event_timestamp"`
	EventType     string                 `json:"event_type,omitempty"`
	Channel       string                 `json:"channel,omitempty"`
	Amount        *float64               `json:"amount,omitempty"`
	Currency      string                 `json:"currency,omitempty"`
	Metadata      map[string]string      `json:"metadata,omitempty"`
}

// NormalizedEvent represents the enriched, validated output
type NormalizedEvent struct {
	EventID           string            `json:"event_id"`
	CustomerID        string            `json:"customer_id"`
	EventTimestamp    int64             `json:"event_timestamp"`    // Unix milliseconds
	EventType         *string           `json:"event_type,omitempty"`
	Channel           *string           `json:"channel,omitempty"`
	Amount            *float64          `json:"amount,omitempty"`
	Currency          *string           `json:"currency,omitempty"`
	Metadata          map[string]string `json:"metadata,omitempty"`
	ProcessedTimestamp int64            `json:"processed_timestamp"` // Unix milliseconds
	PipelineVersion   string            `json:"pipeline_version"`
}

// DeadLetterEvent for failed processing
type DeadLetterEvent struct {
	OriginalEvent  RawEvent `json:"original_event"`
	ErrorCode      string   `json:"error_code"`
	ErrorDetail    string   `json:"error_detail"`
	FailedAt       int64    `json:"failed_at"`       // Unix milliseconds
	Pipeline       string   `json:"pipeline"`
	AttemptCount   int      `json:"attempt_count"`
}

// ─── Schema Validation ─────────────────────────────────────────────────────

var (
	validEventTypesSet = make(map[string]bool)
	avroCodec          *goavro.Codec
)

func init() {
	// Initialize valid event types
	for _, t := range strings.Split(validEventTypes, ",") {
		validEventTypesSet[strings.TrimSpace(t)] = true
	}
	
	// Compile Avro codec
	var err error
	avroCodec, err = goavro.NewCodec(eventAvroSchema)
	if err != nil {
		log.Fatalf(context.Background(), "Failed to compile Avro schema: %v", err)
	}
	
	// Register types for Beam serialization
	register.TypeReflect(&RawEvent{})
	register.TypeReflect(&NormalizedEvent{})
	register.TypeReflect(&DeadLetterEvent{})
}

// ValidateEvent checks business rules and returns error code if invalid
func ValidateEvent(event RawEvent) (string, error) {
	if event.EventID == "" {
		return "MISSING_EVENT_ID", nil
	}
	if event.CustomerID == "" {
		return "MISSING_CUSTOMER_ID", nil
	}
	if event.EventTS == "" {
		return "MISSING_EVENT_TIMESTAMP", nil
	}
	
	// Parse and validate timestamp
	ts, err := parseTimestamp(event.EventTS)
	if err != nil {
		return "INVALID_TIMESTAMP", err
	}
	_ = ts // Use for event-time windowing
	
	// Validate event type if present
	if event.EventType != "" && !validEventTypesSet[event.EventType] {
		return "INVALID_EVENT_TYPE", nil
	}
	
	// Validate amount if present
	if event.Amount != nil && *event.Amount < 0 {
		return "NEGATIVE_AMOUNT", nil
	}
	
	return "", nil // Valid
}

func parseTimestamp(ts string) (int64, error) {
	// Try RFC3339 first
	t, err := time.Parse(time.RFC3339, ts)
	if err == nil {
		return t.UnixMilli(), nil
	}
	
	// Try Unix milliseconds
	if ms, err := strconv.ParseInt(ts, 10, 64); err == nil {
		return ms, nil
	}
	
	return 0, fmt.Errorf("unparseable timestamp: %s", ts)
}

// ─── DoFns ─────────────────────────────────────────────────────────────────

// ParseAndValidateFn parses JSON and validates schema
type ParseAndValidateFn struct{}

func (fn *ParseAndValidateFn) ProcessElement(ctx context.Context, msg pubsubio.Message, 
	validEvents func(NormalizedEvent), deadLetters func(DeadLetterEvent)) {
	
	start := time.Now()
	eventsProcessed.Inc(ctx, 1)
	
	var raw RawEvent
	if err := json.Unmarshal(msg.Data, &raw); err != nil {
		fn.emitDeadLetter(ctx, raw, "JSON_PARSE_ERROR", err.Error(), 1, deadLetters)
		schemaErrors.Inc(ctx, 1)
		return
	}
	
	// Validate
	if errCode, err := ValidateEvent(raw); errCode != "" {
		fn.emitDeadLetter(ctx, raw, errCode, err.Error(), 1, deadLetters)
		eventsDropped.Inc(ctx, 1)
		return
	}
	
	eventsValidated.Inc(ctx, 1)
	
	// Convert to normalized (enrichment happens in next step)
	normalized := fn.toNormalized(raw)
	processingLatency.Update(ctx, float64(time.Since(start).Milliseconds()))
	validEvents(normalized)
}

func (fn *ParseAndValidateFn) emitDeadLetter(ctx context.Context, raw RawEvent, code, detail string, attempt int, emit func(DeadLetterEvent)) {
	dl := DeadLetterEvent{
		OriginalEvent: raw,
		ErrorCode:     code,
		ErrorDetail:   detail,
		FailedAt:      time.Now().UnixMilli(),
		Pipeline:      "go-event-pipeline",
		AttemptCount:  attempt,
	}
	eventsDeadLettered.Inc(ctx, 1)
	emit(dl)
}

func (fn *ParseAndValidateFn) toNormalized(raw RawEvent) NormalizedEvent {
	ts, _ := parseTimestamp(raw.EventTS)
	return NormalizedEvent{
		EventID:            raw.EventID,
		CustomerID:         raw.CustomerID,
		EventTimestamp:     ts,
		EventType:          stringPtr(raw.EventType),
		Channel:            stringPtr(raw.Channel),
		Amount:             raw.Amount,
		Currency:           stringPtr(raw.Currency),
		Metadata:           raw.Metadata,
		ProcessedTimestamp: time.Now().UnixMilli(),
		PipelineVersion:    pipelineVersion,
	}
}

func stringPtr(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}

// EnrichmentFn enriches events with customer profile (side input via external call)
type EnrichmentFn struct {
	ProfileServiceURL string // e.g., Vertex AI Feature Store online endpoint
}

func (fn *EnrichmentFn) ProcessElement(ctx context.Context, event NormalizedEvent,
	enrichedEvents func(NormalizedEvent), deadLetters func(DeadLetterEvent)) {
	
	start := time.Now()
	
	// In production: call Vertex AI Feature Store online serving or Memorystore
	// For this example, simulate enrichment
	profile := fn.fetchProfile(ctx, event.CustomerID)
	if profile == nil {
		// Customer not found - dead letter for investigation
		dl := DeadLetterEvent{
			OriginalEvent: RawEvent{EventID: event.EventID, CustomerID: event.CustomerID},
			ErrorCode:     "CUSTOMER_NOT_FOUND",
			ErrorDetail:   fmt.Sprintf("Customer %s not in profile store", event.CustomerID),
			FailedAt:      time.Now().UnixMilli(),
			Pipeline:      "go-event-pipeline",
			AttemptCount:  1,
		}
		eventsDeadLettered.Inc(ctx, 1)
		deadLetters(dl)
		return
	}
	
	// Merge profile data (in real impl, add fields to NormalizedEvent struct)
	// For Avro compatibility, we'd extend the schema or use a separate enriched schema
	log.Infof(ctx, "Enriched event %s for customer %s (tier: %s)", event.EventID, event.CustomerID, profile["tier"])
	
	eventsEnriched.Inc(ctx, 1)
	processingLatency.Update(ctx, float64(time.Since(start).Milliseconds()))
	enrichedEvents(event)
}

// Simulated profile fetch - replace with actual Vertex AI Feature Store client
func (fn *EnrichmentFn) fetchProfile(ctx context.Context, customerID string) map[string]string {
	// In production:
	// client := aifeaturestore.NewOnlineServingClient(...)
	// response, err := client.ReadFeatureValues(ctx, &aifeaturestore.ReadFeatureValuesRequest{...})
	
	// Mock data
	if customerID == "cust-123" {
		return map[string]string{"tier": "GOLD", "segment": "PREMIUM", "risk_score": "0.1"}
	}
	if customerID == "cust-456" {
		return map[string]string{"tier": "SILVER", "segment": "STANDARD", "risk_score": "0.3"}
	}
	return nil
}

// AvroSerializeFn serializes NormalizedEvent to Avro binary for BigQuery
type AvroSerializeFn struct{}

func (fn *AvroSerializeFn) ProcessElement(ctx context.Context, event NormalizedEvent, 
	serialized func([]byte)) {
	
	native, err := avroCodec.NativeFromTextual(map[string]interface{}{
		"event_id":             event.EventID,
		"customer_id":          event.CustomerID,
		"event_timestamp":      event.EventTimestamp,
		"event_type":           event.EventType,
		"channel":              event.Channel,
		"amount":               event.Amount,
		"currency":             event.Currency,
		"metadata":             event.Metadata,
		"processed_timestamp":  event.ProcessedTimestamp,
		"pipeline_version":     event.PipelineVersion,
	})
	if err != nil {
		avroErrors.Inc(ctx, 1)
		log.Errorf(ctx, "Avro serialization failed for event %s: %v", event.EventID, err)
		return
	}
	
	binary, err := avroCodec.BinaryFromNative(nil, native)
	if err != nil {
		avroErrors.Inc(ctx, 1)
		log.Errorf(ctx, "Avro binary encoding failed for event %s: %v", event.EventID, err)
		return
	}
	
	serialized(binary)
}

// ─── Pipeline Construction ─────────────────────────────────────────────────

func buildPipeline(p *beam.Pipeline, options *PipelineOptions) {
	inputTopic := options.InputTopic
	outputTable := options.OutputTable
	deadLetterTopic := options.DeadLetterTopic
	profileServiceURL := options.ProfileServiceURL
	
	// Read from Pub/Sub
	rawMessages := pubsubio.Read(p, inputTopic)
	
	// Parse, validate, split valid/dead-letter
	validEvents, deadLetters := beam.ParDo2(p, &ParseAndValidateFn{}, rawMessages)
	
	// Enrich valid events
	enrichedEvents, moreDeadLetters := beam.ParDo2(p, &EnrichmentFn{ProfileServiceURL: profileServiceURL}, validEvents)
	
	// Combine dead letters
	allDeadLetters := beam.Flatten(p, deadLetters, moreDeadLetters)
	
	// Serialize to Avro for BigQuery
	avroEvents := beam.ParDo(p, &AvroSerializeFn{}, enrichedEvents)
	
	// Write to BigQuery (Avro format, partitioned by event_timestamp day)
	bigqueryio.Write(p, outputTable, avroEvents,
		bigqueryio.WithSchema(eventAvroSchema),
		bigqueryio.WithWriteDisposition(bigqueryio.WriteAppend),
		bigqueryio.WithCreateDisposition(bigqueryio.CreateIfNeeded),
		bigqueryio.WithTimePartitioning(bigqueryio.TimePartitioning{
			Type:  bigqueryio.DayPartitioning,
			Field: "event_timestamp",
		}),
		bigqueryio.WithClustering(bigqueryio.Clustering{
			Fields: []string{"customer_id", "event_type"},
		}),
	)
	
	// Write dead letters to Pub/Sub
	deadLetterJSON := beam.ParDo(p, func(ctx context.Context, dl DeadLetterEvent) ([]byte, error) {
		return json.Marshal(dl)
	}, allDeadLetters)
	pubsubio.Write(p, deadLetterTopic, deadLetterJSON)
	
	// Add stats for monitoring
	stats.Count(p, "total_events", rawMessages)
	stats.Count(p, "valid_events", validEvents)
	stats.Count(p, "dead_letters", allDeadLetters)
}

// ─── Pipeline Options ──────────────────────────────────────────────────────

type PipelineOptions struct {
	InputTopic         string `json:"input_topic"`
	OutputTable        string `json:"output_table"`
	DeadLetterTopic    string `json:"dead_letter_topic"`
	ProfileServiceURL  string `json:"profile_service_url"`
}

func main() {
	beam.Init()
	
	ctx := context.Background()
	
	// Parse flags
	var options PipelineOptions
	flag.StringVar(&options.InputTopic, "input_topic", "", "Pub/Sub input topic (required)")
	flag.StringVar(&options.OutputTable, "output_table", "", "BigQuery output table project:dataset.table (required)")
	flag.StringVar(&options.DeadLetterTopic, "dead_letter_topic", "", "Pub/Sub dead letter topic (required)")
	flag.StringVar(&options.ProfileServiceURL, "profile_service_url", "", "Profile service URL (Vertex AI Feature Store)")
	flag.Parse()
	
	if options.InputTopic == "" || options.OutputTable == "" || options.DeadLetterTopic == "" {
		log.Fatal(ctx, "Required flags: --input_topic, --output_table, --dead_letter_topic")
	}
	
	p := beam.NewPipeline()
	buildPipeline(p, &options)
	
	if err := beamx.Run(ctx, p); err != nil {
		log.Exitf(ctx, "Pipeline failed: %v", err)
	}
}
```

---

## 🧪 Unit Tests

```go
// go_pipeline_test.go

package main

import (
	"testing"
	"time"

	"github.com/apache/beam/sdks/v2/go/pkg/beam"
	"github.com/apache/beam/sdks/v2/go/pkg/beam/testing/passert"
	"github.com/apache/beam/sdks/v2/go/pkg/beam/testing/ptest"
)

func TestValidateEvent(t *testing.T) {
	tests := []struct {
		name     string
		event    RawEvent
		wantCode string
	}{
		{
			name: "valid event",
			event: RawEvent{
				EventID:    "evt-001",
				CustomerID: "cust-123",
				EventTS:    "2024-01-15T10:00:00Z",
				EventType:  "purchase",
				Amount:     float64Ptr(100.0),
			},
			wantCode: "",
		},
		{
			name:     "missing event_id",
			event:    RawEvent{CustomerID: "cust-123", EventTS: "2024-01-15T10:00:00Z"},
			wantCode: "MISSING_EVENT_ID",
		},
		{
			name:     "missing customer_id",
			event:    RawEvent{EventID: "evt-001", EventTS: "2024-01-15T10:00:00Z"},
			wantCode: "MISSING_CUSTOMER_ID",
		},
		{
			name:     "invalid timestamp",
			event:    RawEvent{EventID: "evt-001", CustomerID: "cust-123", EventTS: "not-a-date"},
			wantCode: "INVALID_TIMESTAMP",
		},
		{
			name:     "invalid event type",
			event:    RawEvent{EventID: "evt-001", CustomerID: "cust-123", EventTS: "2024-01-15T10:00:00Z", EventType: "invalid_type"},
			wantCode: "INVALID_EVENT_TYPE",
		},
		{
			name:     "negative amount",
			event:    RawEvent{EventID: "evt-001", CustomerID: "cust-123", EventTS: "2024-01-15T10:00:00Z", Amount: float64Ptr(-10.0)},
			wantCode: "NEGATIVE_AMOUNT",
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			code, _ := ValidateEvent(tt.event)
			if code != tt.wantCode {
				t.Errorf("ValidateEvent() = %q, want %q", code, tt.wantCode)
			}
		})
	}
}

func TestParseAndValidateFn(t *testing.T) {
	p := beam.NewPipeline()
	s := p.Root()
	
	// Valid event
	validJSON := `{"event_id":"evt-001","customer_id":"cust-123","event_timestamp":"2024-01-15T10:00:00Z","event_type":"purchase","amount":100.0}`
	// Invalid event
	invalidJSON := `{"event_id":"","customer_id":"cust-123","event_timestamp":"2024-01-15T10:00:00Z"}`
	
	// Create test messages
	msgs := beam.CreateList(s, []pubsubio.Message{
		{Data: []byte(validJSON)},
		{Data: []byte(invalidJSON)},
	})
	
	valid, dead := beam.ParDo2(s, &ParseAndValidateFn{}, msgs)
	
	// Expect 1 valid, 1 dead letter
	passert.Equals(s, valid, 1)
	passert.Equals(s, dead, 1)
	
	ptest.Run(p)
}

func TestAvroSerialization(t *testing.T) {
	event := NormalizedEvent{
		EventID:            "evt-001",
		CustomerID:         "cust-123",
		EventTimestamp:     1705312800000,
		EventType:          stringPtr("purchase"),
		Channel:            stringPtr("web"),
		Amount:             float64Ptr(100.0),
		Currency:           stringPtr("USD"),
		Metadata:           map[string]string{"source": "mobile"},
		ProcessedTimestamp: time.Now().UnixMilli(),
		PipelineVersion:    "1.2.0",
	}
	
	fn := &AvroSerializeFn{}
	var output []byte
	fn.ProcessElement(context.Background(), event, func(b []byte) { output = b })
	
	if len(output) == 0 {
		t.Fatal("Avro serialization produced empty output")
	}
	
	// Verify we can decode it back
	native, err := avroCodec.NativeFromBinary(output)
	if err != nil {
		t.Fatalf("Failed to decode Avro: %v", err)
	}
	
	record := native.(map[string]interface{})
	if record["event_id"] != "evt-001" {
		t.Errorf("Decoded event_id = %v, want evt-001", record["event_id"])
	}
}

func float64Ptr(f float64) *float64 { return &f }
```

---

## 🎯 Interview Talking Points

### "Why Go for Dataflow? When would you choose it over Python?"

| Factor | Go | Python |
|--------|-----|--------|
| **Startup Time** | ~100ms | ~2-5s (interpreter + imports) |
| **Memory/Event** | ~2-5 KB | ~10-50 KB |
| **Throughput** | 2-3x higher | Baseline |
| **Dataflow Support** | Beam Go SDK (GA) | Beam Python SDK (mature) |
| **Ecosystem** | Growing | Mature (pandas, numpy, sklearn) |
| **Team Skills** | Need Go expertise | Widely known |

**Choose Go when:**
- High throughput (>500K events/sec/worker)
- Low latency critical (<10ms processing)
- Memory-constrained (Dataflow runner bills by vCPU-hour + memory)
- Team has Go expertise or willing to invest

**Choose Python when:**
- ML integration (TensorFlow, PyTorch, sklearn)
- Rapid prototyping
- Complex data manipulation (pandas)
- Team is Python-centric

### "How does the Go Beam SDK differ from Python?"

1. **Type Safety** — Compile-time checks vs runtime; `register.TypeReflect` required for all types
2. **No Dynamic Side Inputs** — Must use external service calls (Vertex AI Feature Store, Memorystore) instead of Beam side inputs
3. **Metrics** — `beam.NewCounter`, `beam.NewDistribution` vs `Metrics.counter()`
4. **Serialization** — Avro/Protobuf recommended (JSON slower); Python uses pickle/cloudpickle
5. **Testing** — `ptest.Run()` + `passert` vs `TestPipeline` + `assert_that`

### "How do you handle schema evolution in Go?"

1. **Avro Schema Registry** — Store schemas in Confluent Schema Registry or custom service
2. **Backward Compatibility** — Only add optional fields with defaults; never remove/change required fields
3. **Pipeline Version Field** — Every event carries `pipeline_version` for debugging
4. **BigQuery Schema Evolution** — `ALLOW_FIELD_ADDITION`, `ALLOW_FIELD_RELAXATION` in write disposition
5. **CI/CD Gate** — Schema compatibility check in pipeline build (breaking change = fail build)

---

## 📋 Production Checklist

- [ ] **Module** — `go.mod` with pinned Beam SDK version (e.g., `v2.58.0`)
- [ ] **Container** — `gcr.io/dataflow-templates-base/go1.21` base image, multi-stage build
- [ ] **Dependencies** — `goavro/v2` for Avro, `google.golang.org/api` for GCP services
- [ ] **IAM** — Service account: `dataflow.worker`, `pubsub.subscriber`, `bigquery.dataEditor`, `aiplatform.endpoints.predict` (Feature Store)
- [ ] **VPC-SC** — Perimeter with Private Service Connect for BigQuery, Pub/Sub, Vertex AI
- [ ] **Monitoring** — Custom metrics exported to Cloud Monitoring; alert on latency p99, dead letter rate, throughput drop
- [ ] **Runbooks** — Schema evolution procedure, DLQ replay, version rollout (canary 10% → 50% → 100%)
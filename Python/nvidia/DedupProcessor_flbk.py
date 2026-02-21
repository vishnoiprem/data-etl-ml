# Pseudocode (Flink-like syntax)
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import KeyedProcessFunction
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.common.typeinfo import Types

env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(1)

# Read from Kafka topic
stream = env.from_source(
    source=KafkaSource(...),
    watermark_strategy=WatermarkStrategy.for_monotonous_timestamps(),
    type_info=Types.STRING()
)

# Key by event_id
keyed_stream = stream.key_by(lambda x: x.split(",")[0])  # extract ID

# Use stateful processing
class DedupProcessor(KeyedProcessFunction):
    def __init__(self):
        self.last_seen_state = None

    def open(self, context):
        self.last_seen_state = context.get_state(
            ValueStateDescriptor("last_seen", Types.LONG())
        )

    def process_element(self, value, ctx):
        event_id, timestamp = value.split(",")
        now = ctx.timestamp()

        # Check if event is within 10-min window
        if self.last_seen_state.value() and now - self.last_seen_state.value() < 600_000:
            # Suppress duplicate
            return
        else:
            # Emit and update state
            ctx.output(value)
            self.last_seen_state.update(now)

keyed_stream.process(DedupProcessor()).add_sink(...)  # write to sink
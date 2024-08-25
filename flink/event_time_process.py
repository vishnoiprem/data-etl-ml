from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
from pyflink.table.descriptors import Schema, Json, Kafka, Rowtime
from pyflink.table.window import Tumble
from pyflink.table.expressions import col

# Step 1: Set up the execution environment
env = StreamExecutionEnvironment.get_execution_environment()
settings = EnvironmentSettings.new_instance().in_streaming_mode().use_blink_planner().build()
table_env = StreamTableEnvironment.create(env, environment_settings=settings)

# Step 2: Define the Kafka source table with event-time and watermark
table_env.execute_sql("""
    CREATE TABLE events (
        user_id STRING,
        event_type STRING,
        event_time TIMESTAMP(3),
        WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'events',
        'properties.bootstrap.servers' = 'localhost:9092',
        'format' = 'json'
    )
""")

# Step 3: Define the sink table
table_env.execute_sql("""
    CREATE TABLE result_table (
        window_end TIMESTAMP(3),
        user_id STRING,
        event_count BIGINT
    ) WITH (
        'connector' = 'filesystem',
        'path' = 'file:///path/to/output',
        'format' = 'csv'
    )
""")

# Step 4: Perform the windowed aggregation on event-time
table_env.execute_sql("""
    INSERT INTO result_table
    SELECT
        TUMBLE_END(event_time, INTERVAL '10' MINUTE) AS window_end,
        user_id,
        COUNT(event_type) AS event_count
    FROM events
    GROUP BY
        TUMBLE(event_time, INTERVAL '10' MINUTE),
        user_id
""")

# Step 5: Execute the job
env.execute("Flink Python Event-Time Processing Example")

from pyflink.table import EnvironmentSettings, TableEnvironment
from pyflink.table.expressions import col, lit
from pyflink.table.window import Session

# Create an environment for executing Flink SQL
env_settings = EnvironmentSettings.in_streaming_mode()
table_env = TableEnvironment.create(env_settings)

# Sample data: a stream of events
data = [
    ("2023-08-16 10:00:00", "user1", "click"),
    ("2023-08-16 10:02:00", "user1", "view"),
    ("2023-08-16 10:07:00", "user1", "purchase"),
    ("2023-08-16 10:10:00", "user2", "click"),
    ("2023-08-16 10:20:00", "user2", "view"),
    ("2023-08-16 10:25:00", "user2", "purchase")
]

# Create a Table from the sample data
schema = ['event_time', 'user_id', 'event_type']
source_table = table_env.from_elements(data, schema)

# Convert the string timestamp to a proper timestamp type
source_table = source_table.with_columns(
    col("event_time").cast("TIMESTAMP(3)").alias("event_time")
)

# Register the table in the TableEnvironment
table_env.create_temporary_view("events", source_table)



# Define the session window SQL query
query = """
SELECT
    SESSION_START(event_time, INTERVAL '5' MINUTE) AS window_start,
    SESSION_END(event_time, INTERVAL '5' MINUTE) AS window_end,
    user_id,
    COUNT(event_type) AS event_count
FROM events
GROUP BY
    SESSION(event_time, INTERVAL '5' MINUTE),
    user_id
"""

# Execute the query
result_table = table_env.sql_query(query)

# Print the result
table_env.to_pandas(result_table).to_string(index=False)


# Sliding window SQL query
sliding_query = """
SELECT
    HOP_START(event_time, INTERVAL '5' MINUTE, INTERVAL '10' MINUTE) AS window_start,
    HOP_END(event_time, INTERVAL '5' MINUTE, INTERVAL '10' MINUTE) AS window_end,
    user_id,
    COUNT(event_type) AS event_count
FROM events
GROUP BY
    HOP(event_time, INTERVAL '5' MINUTE, INTERVAL '10' MINUTE),
    user_id
"""

# Execute the sliding window query
sliding_result_table = table_env.sql_query(sliding_query)

# Print the result
print(table_env.to_pandas(sliding_result_table).to_string(index=False))


# Session window SQL query
session_query = """
SELECT
    SESSION_START(event_time, INTERVAL '5' MINUTE) AS window_start,
    SESSION_END(event_time, INTERVAL '5' MINUTE) AS window_end,
    user_id,
    COUNT(event_type) AS event_count
FROM events
GROUP BY
    SESSION(event_time, INTERVAL '5' MINUTE),
    user_id
"""

# Execute the session window query
session_result_table = table_env.sql_query(session_query)

# Print the result
print(table_env.to_pandas(session_result_table).to_string(index=False))

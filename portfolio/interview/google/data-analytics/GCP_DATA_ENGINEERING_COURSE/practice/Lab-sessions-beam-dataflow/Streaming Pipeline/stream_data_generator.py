from google.cloud import pubsub_v1
import time
import datetime as dt
import random

# Get project details
project_id = "evening-batch-feb-8pm" 
topic_id = "my-topic"

# Publisher Client
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

for event_nbr in range(1, 100):
    # Generate 5 sample columns with random data 100 records
    col1 = random.randint(1, 100)
    col2 = random.uniform(0.0, 1.0)
    col3 = random.choice(["A", "B", "C"])
    col4 = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    col5 = "Sample String"

    data_str = f'{col1},{col2},{col3},{col4},{col5}' 
    # Data must be a bytestring
    data = data_str.encode("utf-8") 
    time.sleep(1)
    # Add two attributes, origin and username, to the message 
    future = publisher.publish(
        topic_path, data, origin="python-sample", username="gcp"
    )

    # print(future.result())
    print(data)

print(f"Published messages with custom attributes to {topic_path}.")

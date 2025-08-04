import dask.dataframe as dd
from fsspec import open_files

# 1. Define remote CSV (supports HTTP/S3/GCS/Blob Storage)
url = "https://storage.googleapis.com/bigdata-bucket/50gb_dataset.csv"  # Replace with your URL

# 2. Configure remote connection
storage_options = {
    'https': {'timeout': 30},  # Increase timeout for large files
    'headers': {'User-Agent': 'Dask Processor'}  # Some servers require this
}

# 3. Lazy-load the remote file (no full download needed)
ddf = dd.read_csv(
    url,
    blocksize="256MB",  # Adjust based on your network speed
    storage_options=storage_options,
    dtype={'price': 'float32'}  # Reduce memory usage
)

# 4. Process in parallel (streaming chunks)
result = ddf.groupby('category').price.mean().compute()
print(f"Average price by category:\n{result}")
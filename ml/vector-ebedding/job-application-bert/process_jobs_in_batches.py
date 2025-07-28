def process_jobs_in_batches(self, jobs_df: pd.DataFrame, batch_size: int = 100):
    """
    Process large job datasets in batches to manage memory
    """
    total_jobs = len(jobs_df)

    for i in range(0, total_jobs, batch_size):
        batch = jobs_df.iloc[i:i + batch_size]

        print(f"Processing batch {i // batch_size + 1}/{(total_jobs - 1) // batch_size + 1}")

        job_embeddings = []
        for idx, job in batch.iterrows():
            # Process individual job
            embedding = self.process_single_job(job)
            job_embeddings.append(embedding)

        # Upload batch to vector database
        self.vector_db.upsert_jobs(job_embeddings)

        # Clear memory
        del job_embeddings



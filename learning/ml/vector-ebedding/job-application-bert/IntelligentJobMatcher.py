class IntelligentJobMatcher:
    def __init__(self, pinecone_api_key: str, pinecone_env: str):
        self.search_engine = JobSearchEngine()
        self.vector_db = VectorDatabase(
            api_key=pinecone_api_key,
            environment=pinecone_env,
            index_name='job-search-index'
        )

    def process_job_dataset(self, jobs_df: pd.DataFrame):
        """
        Process and index a dataset of job postings
        """
        job_embeddings = []

        for idx, job in jobs_df.iterrows():
            # Preprocess job description
            clean_description = self.search_engine.preprocess_text(
                job['description']
            )

            # Create job data structure
            job_data = {
                'title': job['title'],
                'description': clean_description,
                'company': job.get('company', ''),
                'location': job.get('location', ''),
                'salary': job.get('salary', '')
            }

            # Generate embedding
            embedding = self.search_engine.create_enhanced_embedding(job_data)

            # Extract features for metadata
            features = self.search_engine.extract_job_features(clean_description)

            # Prepare metadata
            metadata = {
                'title': job_data['title'],
                'company': job_data['company'],
                'location': job_data['location'],
                'skills': features['skills'],
                'experience_level': features['experience_level'],
                'salary': job_data['salary']
            }

            job_embeddings.append((f"job_{idx}", embedding, metadata))

        # Upload to vector database
        self.vector_db.upsert_jobs(job_embeddings)
        print(f"Indexed {len(job_embeddings)} jobs successfully!")

    def search_jobs(self, query: str, filters: Dict = None, top_k: int = 10) -> List[Dict]:
        """
        Search for jobs based on natural language query
        """
        # Preprocess query
        clean_query = self.search_engine.preprocess_text(query)

        # Generate query embedding
        query_embedding = self.search_engine.model.encode(clean_query)

        # Search similar jobs
        results = self.vector_db.search_similar_jobs(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters
        )

        return results

    def match_resume_to_jobs(self, resume_text: str, top_k: int = 10) -> List[Dict]:
        """
        Match a resume to relevant job postings
        """
        # Extract skills and experience from resume
        resume_features = self.search_engine.extract_job_features(resume_text)

        # Create enhanced resume text for better matching
        enhanced_resume = f"{resume_text} Skills: {' '.join(resume_features['skills'])}"

        # Search for matching jobs
        return self.search_jobs(enhanced_resume, top_k=top_k)

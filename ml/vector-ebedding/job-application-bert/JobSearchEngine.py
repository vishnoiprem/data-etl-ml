import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import pinecone
import re
from typing import List, Dict, Tuple
import json


class JobSearchEngine:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the job search engine with BERT-based sentence transformer

        Args:
            model_name: Pre-trained sentence transformer model
        """
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess job descriptions and resumes
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\.\,\-\+\#]', '', text)

        # Convert to lowercase
        text = text.lower().strip()

        return text

    def extract_job_features(self, job_description: str) -> Dict:
        """
        Extract structured features from job descriptions
        """
        # Common tech skills patterns
        tech_skills = [
            'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'mongodb',
            'aws', 'docker', 'kubernetes', 'machine learning', 'deep learning',
            'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn'
        ]

        # Experience level patterns
        experience_patterns = {
            'entry': r'(entry.level|junior|0-2 years|fresh graduate)',
            'mid': r'(mid.level|3-5 years|intermediate)',
            'senior': r'(senior|lead|6\+ years|expert)'
        }

        job_description_lower = job_description.lower()

        # Extract skills
        found_skills = [skill for skill in tech_skills
                        if skill in job_description_lower]

        # Extract experience level
        experience_level = 'not_specified'
        for level, pattern in experience_patterns.items():
            if re.search(pattern, job_description_lower):
                experience_level = level
                break

        return {
            'skills': found_skills,
            'experience_level': experience_level,
            'text_length': len(job_description),
            'skill_count': len(found_skills)
        }

    def create_enhanced_embedding(self, job_data: Dict) -> np.ndarray:
        """
        Create enhanced embeddings combining text and structured features
        """
        # Get base BERT embedding
        text_embedding = self.model.encode(job_data['description'])

        # Create feature vector
        features = self.extract_job_features(job_data['description'])

        # Combine text with structured features
        enhanced_text = f"{job_data['title']} {job_data['description']} "
        enhanced_text += f"Skills: {' '.join(features['skills'])} "
        enhanced_text += f"Experience: {features['experience_level']}"

        return self.model.encode(enhanced_text)

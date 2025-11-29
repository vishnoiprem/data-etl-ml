"""
================================================================================
PROJECT 3: KNOWLEDGE ASSISTANT SYSTEM
================================================================================
Preserving institutional knowledge before it walks out the door

This prototype demonstrates the complete pipeline:
1. Fine-tuned LLM + RAG hybrid approach
2. Mandatory citation system
3. Role-based access control
4. Human feedback loops
5. Hallucination detection
6. Continuous improvement pipeline

Tech Stack:
- OpenAI GPT-4 (fine-tuned)
- Pinecone (vector database)
- LangChain (orchestration)
- Label Studio (feedback collection)
- Okta (authentication)
================================================================================
"""

import os
import json
import hashlib
import uuid
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time
from abc import ABC, abstractmethod


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class KnowledgeConfig:
    """Configuration for the Knowledge Assistant"""
    # LLM settings
    base_model: str = "gpt-4-turbo-preview"
    fine_tuned_model: str = "ft:gpt-4:company:knowledge-v2"
    temperature: float = 0.2
    max_tokens: int = 2000
    
    # RAG settings
    embedding_model: str = "text-embedding-ada-002"
    top_k_retrieval: int = 10
    rerank_top_k: int = 5
    similarity_threshold: float = 0.7
    
    # Citation settings
    require_citations: bool = True
    min_confidence_threshold: float = 0.6
    
    # Access control
    enable_rbac: bool = True
    
    # Feedback
    enable_feedback: bool = True
    feedback_review_threshold: int = 3  # Reviews needed before action


# ============================================================================
# DATA MODELS
# ============================================================================

class AccessLevel(Enum):
    """Document access levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class FeedbackType(Enum):
    """Types of user feedback"""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    INCORRECT = "incorrect"
    INCOMPLETE = "incomplete"
    OUTDATED = "outdated"


@dataclass
class User:
    """User with access permissions"""
    user_id: str
    email: str
    name: str
    role: str
    department: str
    access_levels: List[AccessLevel]
    expertise_areas: List[str] = field(default_factory=list)
    is_sme: bool = False  # Subject Matter Expert


@dataclass
class Document:
    """Knowledge document"""
    doc_id: str
    title: str
    content: str
    source_type: str  # manual, wiki, email, transcript
    access_level: AccessLevel
    author: str
    created_at: datetime
    updated_at: datetime
    department: str
    tags: List[str] = field(default_factory=list)
    version: int = 1


@dataclass
class DocumentChunk:
    """Chunk of a document with embedding"""
    chunk_id: str
    doc_id: str
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None
    access_level: AccessLevel = AccessLevel.INTERNAL


@dataclass
class Citation:
    """Citation for a claim in the response"""
    citation_id: str
    source_doc: str
    source_chunk_id: str
    quoted_text: str
    page_or_section: str
    relevance_score: float
    url: Optional[str] = None


@dataclass
class KnowledgeResponse:
    """Response from the knowledge assistant"""
    response_id: str
    query: str
    answer: str
    citations: List[Citation]
    confidence_score: float
    sources_used: int
    processing_time_ms: int
    model_used: str
    warnings: List[str] = field(default_factory=list)


@dataclass
class Feedback:
    """User feedback on a response"""
    feedback_id: str
    response_id: str
    user_id: str
    feedback_type: FeedbackType
    comment: Optional[str]
    correction: Optional[str]  # SME-provided correction
    created_at: datetime
    reviewed: bool = False
    action_taken: Optional[str] = None


# ============================================================================
# ACCESS CONTROL
# ============================================================================

class AccessController:
    """
    Role-based access control for documents.
    Users can only see documents they're authorized to access.
    """
    
    def __init__(self, config: KnowledgeConfig):
        self.config = config
        self.role_mappings = self._load_role_mappings()
    
    def _load_role_mappings(self) -> Dict[str, List[AccessLevel]]:
        """Load role to access level mappings"""
        return {
            "intern": [AccessLevel.PUBLIC],
            "engineer": [AccessLevel.PUBLIC, AccessLevel.INTERNAL],
            "senior_engineer": [AccessLevel.PUBLIC, AccessLevel.INTERNAL, AccessLevel.CONFIDENTIAL],
            "manager": [AccessLevel.PUBLIC, AccessLevel.INTERNAL, AccessLevel.CONFIDENTIAL],
            "director": [AccessLevel.PUBLIC, AccessLevel.INTERNAL, AccessLevel.CONFIDENTIAL, AccessLevel.RESTRICTED],
            "admin": [AccessLevel.PUBLIC, AccessLevel.INTERNAL, AccessLevel.CONFIDENTIAL, AccessLevel.RESTRICTED],
        }
    
    def get_user_access_levels(self, user: User) -> List[AccessLevel]:
        """Get access levels for a user"""
        base_levels = self.role_mappings.get(user.role, [AccessLevel.PUBLIC])
        return list(set(base_levels + user.access_levels))
    
    def can_access(self, user: User, document: Document) -> bool:
        """Check if user can access a document"""
        if not self.config.enable_rbac:
            return True
        
        user_levels = self.get_user_access_levels(user)
        return document.access_level in user_levels
    
    def filter_chunks(
        self, 
        chunks: List[DocumentChunk], 
        user: User
    ) -> List[DocumentChunk]:
        """Filter chunks based on user access"""
        if not self.config.enable_rbac:
            return chunks
        
        user_levels = self.get_user_access_levels(user)
        return [c for c in chunks if c.access_level in user_levels]
    
    def build_access_filter(self, user: User) -> Dict:
        """Build vector DB filter for user's access levels"""
        user_levels = self.get_user_access_levels(user)
        return {
            "access_level": {"$in": [level.value for level in user_levels]}
        }


# ============================================================================
# VECTOR STORE WITH ACCESS CONTROL
# ============================================================================

class SecureVectorStore:
    """
    Vector store with built-in access control.
    """
    
    def __init__(self, config: KnowledgeConfig, access_controller: AccessController):
        self.config = config
        self.access_controller = access_controller
        self.vectors: Dict[str, DocumentChunk] = {}  # Simplified in-memory store
    
    def upsert(self, chunks: List[DocumentChunk]):
        """Store chunks with their embeddings"""
        for chunk in chunks:
            self.vectors[chunk.chunk_id] = chunk
        print(f"Stored {len(chunks)} chunks")
    
    def search(
        self, 
        query_embedding: List[float],
        user: User,
        top_k: int = 10
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Search for relevant chunks with access control.
        """
        # Build access filter
        access_filter = self.access_controller.build_access_filter(user)
        
        # In production: query Pinecone with filter
        """
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=access_filter
        )
        """
        
        # Simplified: filter in-memory
        user_levels = self.access_controller.get_user_access_levels(user)
        
        results = []
        for chunk_id, chunk in self.vectors.items():
            if chunk.access_level in user_levels:
                # Dummy similarity score
                import random
                score = random.uniform(0.7, 0.95)
                results.append((chunk, score))
        
        # Sort by score and return top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


# ============================================================================
# CITATION GENERATOR
# ============================================================================

class CitationGenerator:
    """
    Generates and validates citations for LLM responses.
    This is critical for hallucination prevention.
    """
    
    def __init__(self, config: KnowledgeConfig):
        self.config = config
    
    def generate_citations(
        self, 
        answer: str, 
        contexts: List[Tuple[DocumentChunk, float]]
    ) -> List[Citation]:
        """
        Generate citations linking answer claims to source documents.
        """
        citations = []
        
        for i, (chunk, score) in enumerate(contexts, 1):
            # In production: use NLP to match claims to sources
            citation = Citation(
                citation_id=f"cite_{uuid.uuid4().hex[:8]}",
                source_doc=chunk.metadata.get("doc_title", "Unknown"),
                source_chunk_id=chunk.chunk_id,
                quoted_text=chunk.content[:200] + "...",
                page_or_section=chunk.metadata.get("section", "Unknown"),
                relevance_score=round(score, 3),
                url=chunk.metadata.get("url")
            )
            citations.append(citation)
        
        return citations
    
    def validate_citations(
        self, 
        answer: str, 
        citations: List[Citation]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that answer is properly supported by citations.
        """
        warnings = []
        
        # Check citation count
        if len(citations) == 0:
            warnings.append("No citations provided - answer may not be grounded")
            return False, warnings
        
        # Check citation quality
        low_confidence = [c for c in citations if c.relevance_score < self.config.similarity_threshold]
        if len(low_confidence) > len(citations) / 2:
            warnings.append("Most citations have low relevance scores")
        
        # Check for citation markers in answer
        citation_markers = ["[Source", "[1]", "[2]", "[3]", "according to"]
        has_markers = any(marker.lower() in answer.lower() for marker in citation_markers)
        
        if not has_markers and self.config.require_citations:
            warnings.append("Answer does not contain citation markers")
        
        return len(warnings) == 0, warnings


# ============================================================================
# HALLUCINATION DETECTOR
# ============================================================================

class HallucinationDetector:
    """
    Detects potential hallucinations in LLM responses.
    """
    
    def __init__(self, config: KnowledgeConfig):
        self.config = config
        
        # Patterns that might indicate hallucination
        self.uncertainty_phrases = [
            "I think", "I believe", "probably", "might be",
            "I'm not sure", "possibly", "it seems", "generally"
        ]
        
        self.confidence_phrases = [
            "definitely", "certainly", "always", "never",
            "100%", "guaranteed", "absolutely"
        ]
    
    def analyze(
        self, 
        answer: str, 
        contexts: List[Tuple[DocumentChunk, float]]
    ) -> Dict:
        """
        Analyze response for potential hallucinations.
        """
        result = {
            "confidence_score": 0.0,
            "grounding_score": 0.0,
            "warnings": [],
            "recommendation": "accept"
        }
        
        # Calculate grounding score based on context relevance
        if contexts:
            avg_relevance = sum(score for _, score in contexts) / len(contexts)
            result["grounding_score"] = round(avg_relevance, 2)
        
        # Check for uncertainty language
        uncertainty_count = sum(
            1 for phrase in self.uncertainty_phrases 
            if phrase.lower() in answer.lower()
        )
        
        # Check for overconfident language
        overconfidence_count = sum(
            1 for phrase in self.confidence_phrases 
            if phrase.lower() in answer.lower()
        )
        
        # Calculate confidence score
        base_confidence = result["grounding_score"]
        
        # Penalize overconfidence when grounding is low
        if overconfidence_count > 0 and base_confidence < 0.8:
            result["warnings"].append(
                "High confidence language with low grounding - potential hallucination"
            )
            base_confidence -= 0.1 * overconfidence_count
        
        # Uncertainty is okay when grounding is low
        if uncertainty_count > 0 and base_confidence < 0.7:
            base_confidence += 0.05  # Reward appropriate uncertainty
        
        result["confidence_score"] = round(max(0, min(1, base_confidence)), 2)
        
        # Determine recommendation
        if result["confidence_score"] < self.config.min_confidence_threshold:
            result["recommendation"] = "flag_for_review"
            result["warnings"].append(
                f"Confidence below threshold ({self.config.min_confidence_threshold})"
            )
        elif result["grounding_score"] < 0.6:
            result["recommendation"] = "add_disclaimer"
            result["warnings"].append("Low grounding - answer may not be fully supported")
        
        return result


# ============================================================================
# FINE-TUNED MODEL INTERFACE
# ============================================================================

class FineTunedModel:
    """
    Interface to the fine-tuned model with domain knowledge.
    """
    
    def __init__(self, config: KnowledgeConfig):
        self.config = config
        
        self.system_prompt = """You are an expert engineering knowledge assistant for [Company Name].

Your role is to help engineers find accurate information from internal documentation.

CRITICAL RULES:
1. ONLY provide information that is supported by the provided context
2. ALWAYS cite your sources using [Source N] format
3. If information is not in the context, say "I don't have documentation on that topic"
4. Be precise with technical details - errors can cause safety issues
5. If you're uncertain, express that uncertainty
6. For procedures, list steps clearly and completely

RESPONSE FORMAT:
- Start with a direct answer to the question
- Provide relevant technical details with citations
- End with any caveats or related information
- Always include source references"""

    def generate(
        self, 
        query: str, 
        contexts: List[Tuple[DocumentChunk, float]]
    ) -> str:
        """
        Generate response using fine-tuned model.
        """
        # Build context string
        context_parts = []
        for i, (chunk, score) in enumerate(contexts, 1):
            source_info = f"[Source {i}: {chunk.metadata.get('doc_title', 'Unknown')}]"
            context_parts.append(f"{source_info}\n{chunk.content}")
        
        context_string = "\n\n---\n\n".join(context_parts)
        
        user_prompt = f"""Context from internal documentation:

{context_string}

---

Question: {query}

Please provide a comprehensive answer based on the documentation above. 
Cite all sources using [Source N] format."""

        # In production: call fine-tuned OpenAI model
        """
        from openai import OpenAI
        client = OpenAI()
        
        response = client.chat.completions.create(
            model=self.config.fine_tuned_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )
        
        return response.choices[0].message.content
        """
        
        # Demo response
        return f"""Based on the internal documentation, here is the answer to your question:

{query}

According to our engineering standards [Source 1], the recommended procedure involves the following steps:

1. First, verify all prerequisites are met as specified in the safety documentation [Source 2]
2. Follow the standard operating procedure outlined in the maintenance manual
3. Document all actions in the maintenance log

Key technical specifications from the documentation:
- Parameter A should be set to X [Source 1]
- Tolerance levels are defined in Appendix B [Source 3]

Important notes:
- Always follow lockout-tagout procedures before maintenance [Source 2]
- Contact the on-call engineer if you encounter unexpected conditions

Sources used: [Source 1] Engineering Standards, [Source 2] Safety Manual, [Source 3] Technical Specifications"""


# ============================================================================
# FEEDBACK SYSTEM
# ============================================================================

class FeedbackSystem:
    """
    Manages user feedback and SME corrections.
    """
    
    def __init__(self, config: KnowledgeConfig):
        self.config = config
        self.feedback_store: Dict[str, Feedback] = {}
        self.response_feedback: Dict[str, List[str]] = {}  # response_id -> feedback_ids
    
    def submit_feedback(
        self, 
        response_id: str,
        user: User,
        feedback_type: FeedbackType,
        comment: Optional[str] = None,
        correction: Optional[str] = None
    ) -> Feedback:
        """
        Submit feedback on a response.
        """
        feedback = Feedback(
            feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
            response_id=response_id,
            user_id=user.user_id,
            feedback_type=feedback_type,
            comment=comment,
            correction=correction if user.is_sme else None,  # Only SMEs can provide corrections
            created_at=datetime.utcnow(),
            reviewed=False
        )
        
        self.feedback_store[feedback.feedback_id] = feedback
        
        if response_id not in self.response_feedback:
            self.response_feedback[response_id] = []
        self.response_feedback[response_id].append(feedback.feedback_id)
        
        # Check if action needed
        self._check_feedback_threshold(response_id)
        
        return feedback
    
    def _check_feedback_threshold(self, response_id: str):
        """
        Check if feedback threshold is met for action.
        """
        feedback_ids = self.response_feedback.get(response_id, [])
        
        if len(feedback_ids) < self.config.feedback_review_threshold:
            return
        
        feedbacks = [self.feedback_store[fid] for fid in feedback_ids]
        
        # Count negative feedback
        negative_types = [FeedbackType.INCORRECT, FeedbackType.NOT_HELPFUL, FeedbackType.OUTDATED]
        negative_count = sum(1 for f in feedbacks if f.feedback_type in negative_types)
        
        if negative_count >= self.config.feedback_review_threshold:
            self._trigger_review(response_id, feedbacks)
    
    def _trigger_review(self, response_id: str, feedbacks: List[Feedback]):
        """
        Trigger SME review for a problematic response.
        """
        print(f"⚠️  Review triggered for response {response_id}")
        print(f"   Negative feedback count: {len(feedbacks)}")
        
        # In production: send to Label Studio or review queue
        # - Create review task
        # - Notify relevant SMEs
        # - Track in dashboard
    
    def get_feedback_stats(self) -> Dict:
        """
        Get feedback statistics for dashboard.
        """
        total = len(self.feedback_store)
        
        if total == 0:
            return {"total": 0}
        
        by_type = {}
        for feedback in self.feedback_store.values():
            type_name = feedback.feedback_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
        
        return {
            "total": total,
            "by_type": by_type,
            "reviewed": sum(1 for f in self.feedback_store.values() if f.reviewed),
            "pending_review": sum(1 for f in self.feedback_store.values() if not f.reviewed)
        }


# ============================================================================
# TRAINING DATA COLLECTOR
# ============================================================================

class TrainingDataCollector:
    """
    Collects data for continuous model improvement.
    """
    
    def __init__(self, config: KnowledgeConfig):
        self.config = config
        self.training_examples: List[Dict] = []
    
    def collect_positive_example(
        self, 
        query: str, 
        response: str, 
        contexts: List[DocumentChunk]
    ):
        """
        Collect a positive training example from good responses.
        """
        example = {
            "type": "positive",
            "query": query,
            "response": response,
            "context_ids": [c.chunk_id for c in contexts],
            "collected_at": datetime.utcnow().isoformat()
        }
        self.training_examples.append(example)
    
    def collect_correction(
        self, 
        query: str,
        original_response: str,
        corrected_response: str,
        sme_user_id: str
    ):
        """
        Collect SME correction as training example.
        """
        example = {
            "type": "correction",
            "query": query,
            "original_response": original_response,
            "corrected_response": corrected_response,
            "corrected_by": sme_user_id,
            "collected_at": datetime.utcnow().isoformat()
        }
        self.training_examples.append(example)
    
    def export_for_finetuning(self, output_path: str) -> int:
        """
        Export collected data in OpenAI fine-tuning format.
        """
        finetune_data = []
        
        for example in self.training_examples:
            if example["type"] == "positive":
                finetune_data.append({
                    "messages": [
                        {"role": "user", "content": example["query"]},
                        {"role": "assistant", "content": example["response"]}
                    ]
                })
            elif example["type"] == "correction":
                finetune_data.append({
                    "messages": [
                        {"role": "user", "content": example["query"]},
                        {"role": "assistant", "content": example["corrected_response"]}
                    ]
                })
        
        with open(output_path, 'w') as f:
            for item in finetune_data:
                f.write(json.dumps(item) + '\n')
        
        return len(finetune_data)


# ============================================================================
# MAIN KNOWLEDGE ASSISTANT PIPELINE
# ============================================================================

class KnowledgeAssistant:
    """
    Complete Knowledge Assistant pipeline.
    """
    
    def __init__(self, config: Optional[KnowledgeConfig] = None):
        self.config = config or KnowledgeConfig()
        
        # Initialize components
        self.access_controller = AccessController(self.config)
        self.vector_store = SecureVectorStore(self.config, self.access_controller)
        self.citation_generator = CitationGenerator(self.config)
        self.hallucination_detector = HallucinationDetector(self.config)
        self.model = FineTunedModel(self.config)
        self.feedback_system = FeedbackSystem(self.config)
        self.training_collector = TrainingDataCollector(self.config)
        
        print("Knowledge Assistant initialized")
        print(f"  - Base model: {self.config.base_model}")
        print(f"  - Fine-tuned model: {self.config.fine_tuned_model}")
        print(f"  - RBAC enabled: {self.config.enable_rbac}")
        print(f"  - Citations required: {self.config.require_citations}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        # In production: use OpenAI API
        import random
        return [random.random() for _ in range(1536)]
    
    def index_document(self, document: Document, chunk_size: int = 500):
        """
        Index a document into the knowledge base.
        """
        print(f"📄 Indexing: {document.title}")
        
        # Split into chunks
        chunks = []
        content = document.content
        
        for i in range(0, len(content), chunk_size):
            chunk_content = content[i:i + chunk_size]
            
            chunk = DocumentChunk(
                chunk_id=f"{document.doc_id}_chunk_{i // chunk_size}",
                doc_id=document.doc_id,
                content=chunk_content,
                metadata={
                    "doc_title": document.title,
                    "source_type": document.source_type,
                    "author": document.author,
                    "department": document.department,
                    "section": f"Section {i // chunk_size + 1}"
                },
                access_level=document.access_level
            )
            
            # Generate embedding
            chunk.embedding = self._generate_embedding(chunk_content)
            chunks.append(chunk)
        
        self.vector_store.upsert(chunks)
        print(f"  ✅ Indexed {len(chunks)} chunks")
    
    def query(self, question: str, user: User) -> KnowledgeResponse:
        """
        Answer a question with full pipeline.
        """
        start_time = time.time()
        response_id = f"resp_{uuid.uuid4().hex[:8]}"
        
        print(f"\n❓ Query: {question}")
        print(f"   User: {user.name} ({user.role})")
        
        # Step 1: Generate query embedding
        print("  → Generating query embedding...")
        query_embedding = self._generate_embedding(question)
        
        # Step 2: Retrieve relevant chunks (with access control)
        print("  → Retrieving relevant documents...")
        contexts = self.vector_store.search(
            query_embedding=query_embedding,
            user=user,
            top_k=self.config.top_k_retrieval
        )
        print(f"    Found {len(contexts)} relevant chunks")
        
        if not contexts:
            return KnowledgeResponse(
                response_id=response_id,
                query=question,
                answer="I don't have access to documentation that can answer this question. This might be because:\n1. The information doesn't exist in our knowledge base\n2. You don't have access to the relevant documents\n\nPlease contact your manager if you believe you should have access.",
                citations=[],
                confidence_score=0.0,
                sources_used=0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                model_used=self.config.base_model,
                warnings=["No relevant documents found"]
            )
        
        # Step 3: Generate response with fine-tuned model
        print("  → Generating response...")
        answer = self.model.generate(question, contexts)
        
        # Step 4: Generate citations
        print("  → Generating citations...")
        citations = self.citation_generator.generate_citations(answer, contexts)
        
        # Step 5: Validate citations
        citation_valid, citation_warnings = self.citation_generator.validate_citations(
            answer, citations
        )
        
        # Step 6: Check for hallucinations
        print("  → Checking for hallucinations...")
        hallucination_check = self.hallucination_detector.analyze(answer, contexts)
        
        # Step 7: Build response
        warnings = citation_warnings + hallucination_check["warnings"]
        
        # Add disclaimer if needed
        if hallucination_check["recommendation"] == "add_disclaimer":
            answer += "\n\n⚠️ Note: This answer may not be fully supported by available documentation. Please verify critical information with a subject matter expert."
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = KnowledgeResponse(
            response_id=response_id,
            query=question,
            answer=answer,
            citations=citations,
            confidence_score=hallucination_check["confidence_score"],
            sources_used=len(contexts),
            processing_time_ms=processing_time,
            model_used=self.config.fine_tuned_model,
            warnings=warnings
        )
        
        # Collect training data if response is good
        if hallucination_check["confidence_score"] >= 0.8:
            self.training_collector.collect_positive_example(
                question, 
                answer, 
                [ctx for ctx, _ in contexts]
            )
        
        print(f"  ✅ Response generated (confidence: {response.confidence_score})")
        
        return response
    
    def submit_feedback(
        self,
        response_id: str,
        user: User,
        feedback_type: FeedbackType,
        comment: Optional[str] = None,
        correction: Optional[str] = None
    ) -> Feedback:
        """
        Submit feedback on a response.
        """
        return self.feedback_system.submit_feedback(
            response_id=response_id,
            user=user,
            feedback_type=feedback_type,
            comment=comment,
            correction=correction
        )


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def main():
    """Demonstrate the Knowledge Assistant"""
    
    print("=" * 70)
    print("KNOWLEDGE ASSISTANT SYSTEM - DEMO")
    print("=" * 70)
    
    # Initialize assistant
    config = KnowledgeConfig(
        enable_rbac=True,
        require_citations=True,
        min_confidence_threshold=0.6
    )
    
    assistant = KnowledgeAssistant(config)
    
    # Create sample users
    engineer = User(
        user_id="user_001",
        email="john.doe@company.com",
        name="John Doe",
        role="engineer",
        department="Operations",
        access_levels=[AccessLevel.INTERNAL],
        is_sme=False
    )
    
    senior_engineer = User(
        user_id="user_002",
        email="jane.smith@company.com",
        name="Jane Smith",
        role="senior_engineer",
        department="Operations",
        access_levels=[AccessLevel.CONFIDENTIAL],
        expertise_areas=["pump_maintenance", "safety"],
        is_sme=True
    )
    
    # Index some sample documents
    print("\n" + "=" * 70)
    print("PHASE 1: INDEXING DOCUMENTS")
    print("=" * 70)
    
    documents = [
        Document(
            doc_id="doc_001",
            title="Pump Maintenance SOP",
            content="""Standard Operating Procedure for Pump Maintenance
            
            1. Pre-Maintenance Safety Check
            - Verify lockout-tagout is complete
            - Check for residual pressure
            - Ensure proper PPE is worn
            
            2. Inspection Procedure
            - Check impeller condition
            - Inspect mechanical seals
            - Review bearing temperature logs
            - Check alignment
            
            3. Maintenance Tasks
            - Replace worn components
            - Lubricate as per schedule
            - Update maintenance log""",
            source_type="manual",
            access_level=AccessLevel.INTERNAL,
            author="Jane Smith",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            department="Operations",
            tags=["pump", "maintenance", "safety"]
        ),
        Document(
            doc_id="doc_002",
            title="Safety Manual - LOTO Procedures",
            content="""Lockout-Tagout (LOTO) Safety Procedures
            
            Purpose: Prevent unexpected energization during maintenance
            
            Steps:
            1. Notify affected personnel
            2. Identify all energy sources
            3. Shut down equipment
            4. Isolate energy sources
            5. Apply locks and tags
            6. Verify zero energy state
            7. Perform maintenance
            8. Remove locks in reverse order
            
            Required Documentation:
            - LOTO permit form
            - Energy isolation checklist
            - Verification signature""",
            source_type="manual",
            access_level=AccessLevel.INTERNAL,
            author="Safety Team",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            department="Safety",
            tags=["safety", "loto", "lockout"]
        ),
        Document(
            doc_id="doc_003",
            title="Confidential - Incident Report Analysis",
            content="""Incident Analysis Report - Q3 2024
            
            Summary of incidents and root causes...
            [Confidential information]""",
            source_type="report",
            access_level=AccessLevel.CONFIDENTIAL,
            author="Safety Team",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            department="Safety",
            tags=["incident", "analysis", "confidential"]
        )
    ]
    
    for doc in documents:
        assistant.index_document(doc)
    
    # Query as regular engineer
    print("\n" + "=" * 70)
    print("PHASE 2: QUERIES (as Engineer)")
    print("=" * 70)
    
    questions = [
        "What's the procedure for pump maintenance?",
        "How do I perform lockout-tagout?",
        "What were the incidents last quarter?"  # Should be blocked by RBAC
    ]
    
    for question in questions:
        response = assistant.query(question, engineer)
        
        print("\n" + "-" * 50)
        print(f"Q: {question}")
        print("-" * 50)
        print(f"\nA: {response.answer[:500]}...")
        print(f"\n📚 Sources: {response.sources_used}")
        print(f"🎯 Confidence: {response.confidence_score}")
        print(f"⏱️  Time: {response.processing_time_ms}ms")
        
        if response.warnings:
            print(f"⚠️  Warnings: {response.warnings}")
        
        print("\n📎 Citations:")
        for citation in response.citations[:3]:
            print(f"   - {citation.source_doc} ({citation.relevance_score})")
    
    # Query as senior engineer (has access to confidential)
    print("\n" + "=" * 70)
    print("PHASE 3: QUERIES (as Senior Engineer)")
    print("=" * 70)
    
    response = assistant.query(
        "What were the incidents last quarter?", 
        senior_engineer
    )
    
    print(f"\nQ: What were the incidents last quarter?")
    print(f"A: {response.answer[:300]}...")
    print(f"📚 Sources: {response.sources_used}")
    
    # Submit feedback
    print("\n" + "=" * 70)
    print("PHASE 4: FEEDBACK SYSTEM")
    print("=" * 70)
    
    # Positive feedback
    feedback = assistant.submit_feedback(
        response_id=response.response_id,
        user=engineer,
        feedback_type=FeedbackType.HELPFUL,
        comment="Very helpful, found exactly what I needed"
    )
    print(f"\n✅ Feedback submitted: {feedback.feedback_id}")
    
    # SME correction
    correction_feedback = assistant.submit_feedback(
        response_id=response.response_id,
        user=senior_engineer,
        feedback_type=FeedbackType.INCOMPLETE,
        comment="Missing important step",
        correction="The procedure should also include checking the impeller clearance..."
    )
    print(f"✅ SME correction submitted: {correction_feedback.feedback_id}")
    
    # Show feedback stats
    stats = assistant.feedback_system.get_feedback_stats()
    print(f"\n📊 Feedback Statistics: {stats}")


if __name__ == "__main__":
    main()

"""
Supplier Document LLM - RAG System for CLP
============================================
This module implements a Retrieval-Augmented Generation system
for querying supplier contracts and compliance documents.

Author: Prem Vishnoi
Date: March 2026
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class RAGConfig:
    """Configuration for RAG system"""
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4"
    top_k: int = 5
    temperature: float = 0.0
    max_tokens: int = 1000


# ============================================================================
# DOCUMENT PROCESSING
# ============================================================================

class DocumentProcessor:
    """
    Handles document loading and chunking for the RAG pipeline.
    
    Supports:
    - Markdown (.md)
    - PDF (.pdf) - requires PyPDF2
    - Word (.docx) - requires python-docx
    - Plain text (.txt)
    """
    
    def __init__(self, config: RAGConfig):
        self.config = config
    
    def load_documents(self, directory: str) -> List[Dict[str, Any]]:
        """Load all documents from a directory"""
        documents = []
        
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            
            if filename.endswith('.md') or filename.endswith('.txt'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        'content': content,
                        'metadata': {
                            'source': filename,
                            'type': 'text'
                        }
                    })
            
            # Add PDF/DOCX loaders as needed
            # elif filename.endswith('.pdf'):
            #     content = self._load_pdf(filepath)
            #     documents.append(...)
        
        print(f"Loaded {len(documents)} documents")
        return documents
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Split documents into chunks with overlap"""
        chunks = []
        
        for doc in documents:
            content = doc['content']
            metadata = doc['metadata']
            
            # Simple chunking by character count with overlap
            start = 0
            chunk_id = 0
            
            while start < len(content):
                end = start + self.config.chunk_size
                chunk_text = content[start:end]
                
                # Try to break at sentence boundary
                if end < len(content):
                    last_period = chunk_text.rfind('.')
                    if last_period > self.config.chunk_size * 0.5:
                        chunk_text = chunk_text[:last_period + 1]
                        end = start + last_period + 1
                
                chunks.append({
                    'content': chunk_text.strip(),
                    'metadata': {
                        **metadata,
                        'chunk_id': chunk_id,
                        'start_char': start,
                        'end_char': end
                    }
                })
                
                start = end - self.config.chunk_overlap
                chunk_id += 1
        
        print(f"Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks


# ============================================================================
# VECTOR STORE (SIMULATED FOR DEMO)
# ============================================================================

class SimpleVectorStore:
    """
    Simple in-memory vector store for demonstration.
    
    In production, use:
    - ChromaDB (local)
    - Pinecone (managed)
    - Weaviate (self-hosted)
    - Azure Cognitive Search
    """
    
    def __init__(self):
        self.documents = []
        self.embeddings = []
    
    def add_documents(self, chunks: List[Dict], embeddings: List[List[float]]):
        """Add documents with their embeddings"""
        self.documents = chunks
        self.embeddings = embeddings
        print(f"Added {len(chunks)} documents to vector store")
    
    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """Find most similar documents using cosine similarity"""
        import math
        
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            dot_product = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x ** 2 for x in a))
            norm_b = math.sqrt(sum(x ** 2 for x in b))
            return dot_product / (norm_a * norm_b) if norm_a * norm_b > 0 else 0
        
        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            sim = cosine_similarity(query_embedding, doc_embedding)
            similarities.append((i, sim))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k documents
        results = []
        for idx, score in similarities[:top_k]:
            results.append({
                'content': self.documents[idx]['content'],
                'metadata': self.documents[idx]['metadata'],
                'score': score
            })
        
        return results


# ============================================================================
# EMBEDDING SERVICE (SIMULATED FOR DEMO)
# ============================================================================

class EmbeddingService:
    """
    Embedding service for converting text to vectors.
    
    In production, use:
    - OpenAI: openai.embeddings.create()
    - Azure OpenAI: Same API, different endpoint
    - Sentence Transformers: Local model
    """
    
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.dimension = 256  # Simulated dimension
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        DEMO: Returns deterministic pseudo-embeddings based on text hash.
        PRODUCTION: Call OpenAI API
        """
        import hashlib
        
        embeddings = []
        for text in texts:
            # Create deterministic pseudo-embedding from text hash
            hash_bytes = hashlib.sha256(text.encode()).digest()
            embedding = [((b - 128) / 128) for b in hash_bytes[:self.dimension]]
            
            # Normalize
            import math
            norm = math.sqrt(sum(x ** 2 for x in embedding))
            embedding = [x / norm for x in embedding]
            
            embeddings.append(embedding)
        
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query"""
        return self.embed([query])[0]


# ============================================================================
# LLM SERVICE (SIMULATED FOR DEMO)
# ============================================================================

class LLMService:
    """
    LLM service for generating responses.
    
    In production, use:
    - OpenAI: openai.chat.completions.create()
    - Azure OpenAI
    - Anthropic Claude
    """
    
    def __init__(self, model: str = "gpt-4", temperature: float = 0.0):
        self.model = model
        self.temperature = temperature
    
    def generate(self, prompt: str, context: str) -> str:
        """
        Generate response using LLM.
        
        DEMO: Returns a template response using the context.
        PRODUCTION: Call LLM API
        """
        # In demo mode, extract key information from context
        response = self._simulate_response(prompt, context)
        return response
    
    def _simulate_response(self, query: str, context: str) -> str:
        """Simulate LLM response for demo purposes"""
        query_lower = query.lower()
        
        # Simple keyword matching for demo
        if 'warranty' in query_lower:
            if 'siemens' in context.lower():
                return """Based on the supplier documents:

**Siemens Energy Warranty Terms:**
- Gas Turbines (SGT-800): **24 months warranty** from commissioning date
- Spare parts availability guaranteed for 10 years

The warranty covers defects in materials and workmanship. Emergency response is included with 4-hour on-site response for critical failures.

*Source: CLP-SUP-2024-001 (Siemens Energy Hong Kong Ltd)*"""
            
        if 'lead time' in query_lower:
            return """Based on the supplier documents, here are the lead times:

| Supplier | Product | Lead Time |
|----------|---------|-----------|
| Siemens Energy | Gas Turbines (SGT-800) | **18-24 months** |
| ABB Power Grids | High-Voltage Transformers | **12-18 months** |
| ABB Power Grids | Switchgear (GIS/AIS) | **8-12 months** |
| Vestas | Wind Turbines (V150-4.2 MW) | **24-30 months** |

*Sources: CLP-SUP-2024-001, CLP-SUP-2024-002, CLP-SUP-2024-003*"""

        if 'certified' in query_lower or 'certification' in query_lower:
            return """Based on the supplier compliance documents:

**Required Certifications for CLP Suppliers:**
1. **Quality:** ISO 9001:2015 (mandatory)
2. **Environmental:** ISO 14001:2015
3. **Safety:** ISO 45001 / OHSAS 18001

**High Voltage Work Certifications:**
- Grade A Electrical Worker Registration (EMSD)
- Confined Space Certification (OSHC)
- Working at Heights Certification (OSHC)

All three major suppliers (Siemens, ABB, Vestas) are fully certified.

*Source: Supplier Compliance Document*"""

        if 'emergency' in query_lower or 'response time' in query_lower:
            return """Based on the supplier contracts:

**Emergency Response Times:**

| Supplier | Response Time | Service |
|----------|---------------|---------|
| Siemens Energy | **4 hours** on-site | Critical turbine failures |
| ABB Power Grids | **2 hours** phone, **8 hours** on-site | HK Island |
| General SLA | **1 hour** for critical issues | Per escalation matrix |

**24/7 Support Hotlines:**
- Siemens: +852 9999 8888
- ABB: Remote diagnostic monitoring included

*Sources: CLP-SUP-2024-001, CLP-SUP-2024-002*"""

        # Default response
        return f"""Based on the supplier documents, I found relevant information:

{context[:500]}...

Please ask a more specific question about:
- Warranty terms
- Lead times
- Certifications
- Emergency response
- Pricing

*Multiple sources available*"""


# ============================================================================
# RAG PIPELINE
# ============================================================================

class SupplierRAG:
    """
    Main RAG pipeline for supplier document Q&A.
    
    Usage:
        rag = SupplierRAG()
        rag.load_documents("./data")
        response = rag.query("What are the warranty terms for Siemens turbines?")
    """
    
    def __init__(self, config: RAGConfig = None):
        self.config = config or RAGConfig()
        self.processor = DocumentProcessor(self.config)
        self.embedding_service = EmbeddingService(self.config.embedding_model)
        self.vector_store = SimpleVectorStore()
        self.llm = LLMService(self.config.llm_model, self.config.temperature)
        self.is_loaded = False
    
    def load_documents(self, directory: str):
        """Load and index documents"""
        print(f"\n{'='*60}")
        print("LOADING DOCUMENTS")
        print('='*60)
        
        # Load documents
        documents = self.processor.load_documents(directory)
        
        # Chunk documents
        chunks = self.processor.chunk_documents(documents)
        
        # Generate embeddings
        print("Generating embeddings...")
        texts = [chunk['content'] for chunk in chunks]
        embeddings = self.embedding_service.embed(texts)
        
        # Store in vector database
        self.vector_store.add_documents(chunks, embeddings)
        self.is_loaded = True
        
        print("Document loading complete!")
        print('='*60 + '\n')
    
    def query(self, question: str, verbose: bool = True) -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            question: User's question
            verbose: Print intermediate steps
        
        Returns:
            Dict with 'answer', 'sources', and 'context'
        """
        if not self.is_loaded:
            raise ValueError("No documents loaded. Call load_documents() first.")
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"QUERY: {question}")
            print('='*60)
        
        # Step 1: Embed the query
        query_embedding = self.embedding_service.embed_query(question)
        
        # Step 2: Retrieve relevant documents
        relevant_docs = self.vector_store.similarity_search(
            query_embedding, 
            top_k=self.config.top_k
        )
        
        if verbose:
            print(f"\nRetrieved {len(relevant_docs)} relevant chunks:")
            for i, doc in enumerate(relevant_docs[:3]):
                print(f"  {i+1}. {doc['metadata']['source']} (score: {doc['score']:.3f})")
        
        # Step 3: Build context from retrieved documents
        context = "\n\n---\n\n".join([doc['content'] for doc in relevant_docs])
        
        # Step 4: Generate response with LLM
        prompt = f"""You are a helpful assistant for CLP Power Hong Kong. 
Answer the question based on the provided context from supplier documents.
Always cite your sources.

Context:
{context}

Question: {question}

Answer:"""
        
        answer = self.llm.generate(prompt, context)
        
        if verbose:
            print(f"\n{'='*60}")
            print("ANSWER:")
            print('='*60)
            print(answer)
            print('='*60 + '\n')
        
        return {
            'answer': answer,
            'sources': [doc['metadata']['source'] for doc in relevant_docs],
            'context': context,
            'scores': [doc['score'] for doc in relevant_docs]
        }


# ============================================================================
# PRODUCTION VERSION (WITH REAL APIs)
# ============================================================================

class ProductionSupplierRAG:
    """
    Production-ready RAG implementation using real APIs.
    
    Requirements:
        pip install openai langchain chromadb
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize with OpenAI API key.
        
        In production, use environment variable:
            export OPENAI_API_KEY=sk-...
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # These would be initialized with real libraries
        self._setup_langchain()
    
    def _setup_langchain(self):
        """Setup LangChain components"""
        # This is the actual production code:
        
        langchain_code = '''
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# 1. Load documents
loader = DirectoryLoader('./data', glob="**/*.md", loader_cls=TextLoader)
documents = loader.load()

# 2. Split into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\\n\\n", "\\n", ".", " "]
)
chunks = text_splitter.split_documents(documents)

# 3. Create embeddings and vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# 4. Create retrieval chain
llm = ChatOpenAI(model="gpt-4", temperature=0)

prompt_template = """You are a helpful assistant for CLP Power Hong Kong.
Answer the question based on the provided context from supplier documents.
Always cite your sources with contract reference numbers.

Context:
{context}

Question: {question}

Answer:"""

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT}
)

# 5. Query
result = qa_chain({"query": "What are the warranty terms for Siemens turbines?"})
print(result["result"])
'''
        self.production_code = langchain_code


# ============================================================================
# DEMO / MAIN
# ============================================================================

def demo():
    """Run demonstration of the Supplier RAG system"""
    
    print("\n" + "="*70)
    print("  SUPPLIER DOCUMENT LLM - RAG SYSTEM DEMO")
    print("  CLP Power Hong Kong - AI Interview Project")
    print("="*70 + "\n")
    
    # Initialize RAG system
    rag = SupplierRAG()
    
    # Load documents
    data_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(data_dir, "..", "data")
    
    # Check if data exists, otherwise use current directory
    if not os.path.exists(data_path):
        data_path = "./data"
    
    rag.load_documents(data_path)
    
    # Demo queries
    queries = [
        "What are the warranty terms for Siemens turbines?",
        "What's the lead time for transformer parts?",
        "Which suppliers are certified for high-voltage work?",
        "What are the emergency response times?",
    ]
    
    print("\n" + "="*70)
    print("  RUNNING DEMO QUERIES")
    print("="*70)
    
    for query in queries:
        result = rag.query(query)
        print("\n" + "-"*70 + "\n")
    
    # Interactive mode
    print("\n" + "="*70)
    print("  INTERACTIVE MODE")
    print("  Type 'quit' to exit")
    print("="*70 + "\n")
    
    while True:
        user_query = input("\nYour question: ").strip()
        if user_query.lower() in ['quit', 'exit', 'q']:
            break
        if user_query:
            rag.query(user_query)


if __name__ == "__main__":
    demo()

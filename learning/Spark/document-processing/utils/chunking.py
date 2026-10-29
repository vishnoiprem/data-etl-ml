"""
Document chunking utilities for RAG (Retrieval Augmented Generation)
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Strategies for document chunking"""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"


@dataclass
class ChunkingConfig:
    """Configuration for document chunking"""
    strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    chunk_size: int = 1000  # Characters
    chunk_overlap: int = 200  # Characters
    separators: List[str] = None
    max_chunks: int = 1000
    respect_sentence_boundaries: bool = True

    def __post_init__(self):
        if self.separators is None:
            if self.strategy == ChunkingStrategy.RECURSIVE:
                self.separators = ["\n\n", "\n", " ", ""]
            elif self.strategy == ChunkingStrategy.SENTENCE:
                self.separators = [". ", "! ", "? ", "\n"]
            elif self.strategy == ChunkingStrategy.PARAGRAPH:
                self.separators = ["\n\n", "\n"]
            else:
                self.separators = [" "]


class DocumentChunker:
    """Chunk documents for RAG applications"""

    def __init__(self, config: ChunkingConfig = None):
        self.config = config or ChunkingConfig()
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficient text splitting"""
        # Sentence boundary patterns
        self.sentence_pattern = re.compile(r'(?<=[.!?])\s+')

        # Paragraph boundary patterns
        self.paragraph_pattern = re.compile(r'\n\s*\n')

        # Special pattern for code blocks
        self.code_block_pattern = re.compile(r'```.*?```', re.DOTALL)

        # Pattern for preserving markdown headers
        self.header_pattern = re.compile(r'^#{1,6}\s+.+$', re.MULTILINE)

    def chunk_document(self,
                       text: str,
                       metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Chunk a document based on configured strategy

        Args:
            text: Document text to chunk
            metadata: Optional metadata to include with chunks

        Returns:
            List of chunk dictionaries
        """
        if not text or not text.strip():
            return []

        # Preprocess text
        clean_text = self._preprocess_text(text)

        # Apply chunking strategy
        if self.config.strategy == ChunkingStrategy.FIXED_SIZE:
            chunks = self._chunk_fixed_size(clean_text)
        elif self.config.strategy == ChunkingStrategy.SENTENCE:
            chunks = self._chunk_by_sentences(clean_text)
        elif self.config.strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraphs(clean_text)
        elif self.config.strategy == ChunkingStrategy.RECURSIVE:
            chunks = self._chunk_recursive(clean_text)
        elif self.config.strategy == ChunkingStrategy.SEMANTIC:
            chunks = self._chunk_semantic(clean_text)
        else:
            chunks = self._chunk_fixed_size(clean_text)  # Default fallback

        # Add metadata and format chunks
        formatted_chunks = []
        for i, chunk_text in enumerate(chunks):
            if not chunk_text.strip():
                continue

            chunk_metadata = {
                'chunk_id': f"chunk_{i:04d}",
                'chunk_index': i,
                'chunk_size': len(chunk_text),
                'word_count': len(chunk_text.split()),
                'character_count': len(chunk_text)
            }

            # Merge with provided metadata
            if metadata:
                chunk_metadata.update(metadata)

            formatted_chunks.append({
                'text': chunk_text,
                'metadata': chunk_metadata
            })

            # Limit number of chunks
            if len(formatted_chunks) >= self.config.max_chunks:
                break

        return formatted_chunks

    def _chunk_fixed_size(self, text: str) -> List[str]:
        """Chunk text into fixed-size pieces"""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            # Calculate end position
            end = min(start + self.config.chunk_size, text_length)

            # If we're not at the end, try to find a good break point
            if end < text_length and self.config.respect_sentence_boundaries:
                # Look for sentence boundaries near the end
                look_ahead = min(100, text_length - end)
                search_text = text[end:end + look_ahead]

                # Find the next sentence boundary
                sentence_match = self.sentence_pattern.search(search_text)
                if sentence_match:
                    end += sentence_match.end()
                else:
                    # Fall back to space or newline
                    look_back = min(100, end - start)
                    for separator in self.config.separators:
                        if separator:
                            last_sep = text[:end].rfind(separator, end - look_back, end)
                            if last_sep > start:
                                end = last_sep + len(separator)
                                break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position for next chunk (with overlap)
            start = end - self.config.chunk_overlap
            if start < 0:
                start = 0

        return chunks

    def _chunk_by_sentences(self, text: str) -> List[str]:
        """Chunk text by sentences, grouping them to reach target size"""
        # Split into sentences
        sentences = self.sentence_pattern.split(text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            # If adding this sentence would exceed chunk size (and we already have content)
            if current_size + sentence_size > self.config.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)

                # Start new chunk with overlap
                overlap_sentences = []
                overlap_size = 0

                # Include last few sentences for overlap
                for s in reversed(current_chunk):
                    if overlap_size + len(s) <= self.config.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += len(s)
                    else:
                        break

                current_chunk = overlap_sentences
                current_size = overlap_size

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_size += sentence_size

        # Add the last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)

        return chunks

    def _chunk_by_paragraphs(self, text: str) -> List[str]:
        """Chunk text by paragraphs"""
        # Split into paragraphs
        paragraphs = self.paragraph_pattern.split(text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk = []
        current_size = 0

        for paragraph in paragraphs:
            paragraph_size = len(paragraph)

            # If adding this paragraph would exceed chunk size
            if current_size + paragraph_size > self.config.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(chunk_text)

                # Start new chunk with overlap
                current_chunk = [paragraph]  # Start with current paragraph
                current_size = paragraph_size
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_size

        # Add the last chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(chunk_text)

        return chunks

    def _chunk_recursive(self, text: str, separators: List[str] = None) -> List[str]:
        """Recursively split text using separators"""
        if separators is None:
            separators = self.config.separators

        # Get the first separator
        separator = separators[0]

        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)  # Split into characters

        # Merge splits if they're too small
        merged_splits = []
        current_split = ""

        for split in splits:
            if separator:
                # Add separator back
                combined = current_split + separator + split if current_split else split
            else:
                combined = current_split + split

            if len(combined) <= self.config.chunk_size:
                current_split = combined
            else:
                if current_split:
                    merged_splits.append(current_split)
                current_split = split

        if current_split:
            merged_splits.append(current_split)

        # If we have more separators to try
        if len(separators) > 1:
            chunks = []
            for split in merged_splits:
                if len(split) > self.config.chunk_size:
                    # Recursively split further
                    sub_chunks = self._chunk_recursive(split, separators[1:])
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(split)
            return chunks
        else:
            return merged_splits

    def _chunk_semantic(self, text: str) -> List[str]:
        """
        Semantic chunking - attempt to keep semantically related content together

        Note: This is a simplified version. In production, you might want to
        use more sophisticated NLP techniques or ML models.
        """
        # First, split by major sections (headers, etc.)
        sections = self._split_by_sections(text)

        chunks = []
        for section in sections:
            # For each section, use recursive chunking
            section_chunks = self._chunk_recursive(section)
            chunks.extend(section_chunks)

        return chunks

    def _split_by_sections(self, text: str) -> List[str]:
        """Split text by major sections (headers, etc.)"""
        sections = []
        current_section = []
        lines = text.split('\n')

        for line in lines:
            # Check if this line looks like a header
            is_header = self.header_pattern.match(line) or \
                        (line.strip().endswith(':') and len(line.strip()) < 100)

            if is_header and current_section:
                # Start a new section
                sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)

        # Add the last section
        if current_section:
            sections.append('\n'.join(current_section))

        return sections

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text before chunking"""
        if not text:
            return ""

        # Remove extra whitespace but preserve meaningful formatting
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.rstrip()  # Remove trailing whitespace
            if line.strip():  # Keep non-empty lines
                cleaned_lines.append(line)
            else:
                # Keep only one empty line between paragraphs
                if not cleaned_lines or cleaned_lines[-1] != "":
                    cleaned_lines.append("")

        # Join back with newlines
        cleaned_text = '\n'.join(cleaned_lines)

        # Remove multiple consecutive empty lines
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)

        return cleaned_text

    def chunk_by_pages(self,
                       content: str,
                       pages: List[Dict]) -> List[Dict[str, Any]]:
        """
        Chunk document while preserving page boundaries

        Args:
            content: Full document content
            pages: List of page dictionaries with text and metadata

        Returns:
            List of chunks with page information
        """
        chunks = []

        if pages:
            # Group pages into chunks
            current_chunk_pages = []
            current_chunk_text = ""

            for page in pages:
                page_text = page.get('text', '')
                page_number = page.get('page_number', 0)

                # Check if adding this page would exceed chunk size
                if len(current_chunk_text) + len(page_text) > self.config.chunk_size and current_chunk_text:
                    # Save current chunk
                    chunk_metadata = {
                        'page_range': {
                            'start': current_chunk_pages[0]['page_number'],
                            'end': current_chunk_pages[-1]['page_number']
                        },
                        'pages': current_chunk_pages
                    }
                    chunks.append({
                        'text': current_chunk_text,
                        'metadata': chunk_metadata
                    })

                    # Start new chunk with overlap
                    # Keep last page for overlap if it's not too large
                    if len(page_text) <= self.config.chunk_overlap:
                        current_chunk_text = page_text
                        current_chunk_pages = [page]
                    else:
                        # Split the page for overlap
                        overlap_text = page_text[:self.config.chunk_overlap]
                        current_chunk_text = overlap_text
                        current_chunk_pages = [{
                            'page_number': page_number,
                            'text': overlap_text,
                            'is_partial': True
                        }]
                else:
                    current_chunk_text += "\n" + page_text if current_chunk_text else page_text
                    current_chunk_pages.append(page)

            # Add the last chunk
            if current_chunk_text:
                chunk_metadata = {
                    'page_range': {
                        'start': current_chunk_pages[0].get('page_number', 0),
                        'end': current_chunk_pages[-1].get('page_number', 0)
                    },
                    'pages': current_chunk_pages
                }
                chunks.append({
                    'text': current_chunk_text,
                    'metadata': chunk_metadata
                })
        else:
            # Fall back to regular chunking if no page info
            chunks = self.chunk_document(content)

        return chunks

    @staticmethod
    def create_default_config() -> ChunkingConfig:
        """Create default chunking configuration"""
        return ChunkingConfig(
            strategy=ChunkingStrategy.RECURSIVE,
            chunk_size=1000,
            chunk_overlap=200,
            respect_sentence_boundaries=True
        )
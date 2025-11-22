"""
Sentinell RAG System - Knowledge Retrieval

Uses ChromaDB to store and query troubleshooting documentation.
The agent uses this to find relevant solutions for detected problems.
"""
import os
import logging
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class SentinellRAG:
    """RAG system for SRE documentation retrieval."""

    def __init__(self, docs_dir: str = "/app/docs", persist_dir: str = "/app/chroma_db"):
        """
        Initialize the RAG system.

        Args:
            docs_dir: Directory containing documentation markdown files
            persist_dir: Directory to persist ChromaDB data
        """
        self.docs_dir = docs_dir
        self.persist_dir = persist_dir

        # Initialize ChromaDB with persistence
        logger.info(f"🗄️ Initializing ChromaDB at {persist_dir}")
        self.client = chromadb.PersistentClient(path=persist_dir)

        # Use default embedding function (all-MiniLM-L6-v2)
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="sentinell_docs",
            embedding_function=self.embedding_function,
            metadata={"description": "SRE troubleshooting documentation"}
        )

        logger.info(f"✅ ChromaDB collection ready: {self.collection.count()} documents")

    def ingest_documents(self) -> int:
        """
        Ingest all markdown files from docs directory into ChromaDB.

        Returns:
            Number of documents ingested
        """
        if not os.path.exists(self.docs_dir):
            logger.warning(f"Docs directory not found: {self.docs_dir}")
            return 0

        docs_ingested = 0

        for filename in os.listdir(self.docs_dir):
            if not filename.endswith('.md'):
                continue

            file_path = os.path.join(self.docs_dir, filename)

            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Split into sections (by ## headers)
                sections = self._split_into_sections(content, filename)

                # Add each section as a document
                for i, section in enumerate(sections):
                    doc_id = f"{filename}_{i}"
                    self.collection.upsert(
                        ids=[doc_id],
                        documents=[section['content']],
                        metadatas=[{
                            "source": filename,
                            "section": section['title'],
                            "chunk_id": i
                        }]
                    )
                    docs_ingested += 1

                logger.info(f"📄 Ingested {len(sections)} sections from {filename}")

            except Exception as e:
                logger.error(f"Failed to ingest {filename}: {e}")

        logger.info(f"✅ Ingested {docs_ingested} document sections")
        return docs_ingested

    def _split_into_sections(self, content: str, filename: str) -> List[Dict]:
        """
        Split markdown content into sections by ## headers.

        Args:
            content: Markdown file content
            filename: Name of the source file

        Returns:
            List of section dictionaries with title and content
        """
        sections = []
        lines = content.split('\n')

        current_title = filename
        current_content = []

        for line in lines:
            # Check if this is a section header (## or ###)
            if line.startswith('## ') or line.startswith('### '):
                # Save previous section
                if current_content:
                    sections.append({
                        'title': current_title,
                        'content': '\n'.join(current_content).strip()
                    })
                    current_content = []

                # Start new section
                current_title = line.strip('#').strip()

            current_content.append(line)

        # Add last section
        if current_content:
            sections.append({
                'title': current_title,
                'content': '\n'.join(current_content).strip()
            })

        return sections

    def query(self, query_text: str, n_results: int = 3) -> List[Dict]:
        """
        Query the knowledge base for relevant documentation.

        Args:
            query_text: The question or problem description
            n_results: Number of results to return

        Returns:
            List of relevant document sections with metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )

            # Format results
            documents = []
            if results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    documents.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    })

            logger.info(f"🔍 Retrieved {len(documents)} relevant docs for: {query_text[:50]}...")
            return documents

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def get_relevant_context(self, problem_description: str) -> str:
        """
        Get relevant context as a formatted string for the agent.

        Args:
            problem_description: Description of the problem

        Returns:
            Formatted string with relevant documentation
        """
        docs = self.query(problem_description, n_results=3)

        if not docs:
            return "No relevant documentation found."

        context_parts = ["# Relevant Documentation\n"]

        for i, doc in enumerate(docs, 1):
            metadata = doc['metadata']
            section = metadata.get('section', 'Unknown')
            source = metadata.get('source', 'Unknown')

            context_parts.append(f"## {i}. {section} (from {source})")
            context_parts.append(doc['content'])
            context_parts.append("\n---\n")

        return "\n".join(context_parts)

    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            self.client.delete_collection(name="sentinell_docs")
            self.collection = self.client.get_or_create_collection(
                name="sentinell_docs",
                embedding_function=self.embedding_function
            )
            logger.info("🗑️ Cleared document collection")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")


# Global RAG instance
_rag_instance = None


def get_rag() -> SentinellRAG:
    """Get or create the global RAG instance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = SentinellRAG()

        # Auto-ingest docs if collection is empty
        if _rag_instance.collection.count() == 0:
            logger.info("📚 Collection empty, ingesting documents...")
            _rag_instance.ingest_documents()

    return _rag_instance

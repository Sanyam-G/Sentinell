"""
Vector DB utility for retrieving relevant code context from Pinecone.
"""

import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()


def search_codebase(query: str, top_k: int = 5) -> str:
    """
    Search the codebase and return formatted context.

    Args:
        query: Error message or natural language query
        top_k: Number of code snippets to retrieve

    Returns:
        Formatted string with relevant code context
    """
    try:
        from pinecone import Pinecone
        from openai import OpenAI

        # Initialize clients
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(os.getenv("PINECONE_INDEX", "codebase"))
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Generate query embedding
        response = openai_client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding

        # Search Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        if not results['matches']:
            return "No relevant code found in vector database."

        # Format results for LLM
        context_parts = ["Relevant code from codebase:\n"]

        for i, match in enumerate(results['matches'], 1):
            file_path = match['metadata'].get('file_path', 'unknown')
            code = match['metadata'].get('code', '')
            score = match['score']

            context_parts.append(f"\n--- File: {file_path} (relevance: {score:.2f}) ---")
            context_parts.append(code)

        return "\n".join(context_parts)

    except Exception as e:
        print(f"Error searching vector DB: {e}")
        return f"Error accessing vector database: {str(e)}"

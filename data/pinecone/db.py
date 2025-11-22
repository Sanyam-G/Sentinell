from pinecone import Pinecone, ServerlessSpec
import os

# Load Pinecone credentials from environment
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "rag-index"                    # Name of your Pinecone index

# Initialize Pinecone client (new API)
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create the index if it doesn't exist
existing_indexes = [idx.name for idx in pc.list_indexes()]
if INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=INDEX_NAME,
        dimension=1024,  # 1024 = text-embedding-3-large dimension (matching your Pinecone config)
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# Connect to the index
index = pc.Index(INDEX_NAME)

def upsert_vectors(vectors: list, ids: list, metadata: list = None):
    """
    Upsert vectors into Pinecone.
    
    vectors: list of embedding vectors
    ids: list of unique string IDs
    metadata: optional list of dicts (e.g., {'text': original_text})
    """
    items = []
    for i, vec in zip(ids, vectors):
        item = {
            'id': i,
            'values': vec,
            'metadata': metadata[int(i)] if metadata else {}
        }
        items.append(item)
    index.upsert(items)
    print(f"Upserted {len(vectors)} vectors into Pinecone index '{INDEX_NAME}'.")

def query_vector(vector, top_k=5):
    """
    Query Pinecone index with a vector.
    
    Returns top_k matches including metadata.
    """
    results = index.query(vector=vector, top_k=top_k, include_metadata=True)
    # Convert to dict format for backward compatibility
    return {
        'matches': [
            {
                'id': match.id,
                'score': match.score,
                'metadata': match.metadata
            }
            for match in results.matches
        ]
    }

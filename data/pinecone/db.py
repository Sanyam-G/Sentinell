import pinecone
import os

# Load Pinecone credentials from environment
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")   # ex: "us-east1-gcp"
INDEX_NAME = "rag-index"                    # Name of your Pinecone index

# Initialize Pinecone client
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)

# Create the index if it doesn't exist
if INDEX_NAME not in pinecone.list_indexes():
    pinecone.create_index(INDEX_NAME, dimension=1536)  # 1536 = OpenAI embedding size

# Connect to the index
index = pinecone.Index(INDEX_NAME)

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
    return index.query(vector, top_k=top_k, include_metadata=True)

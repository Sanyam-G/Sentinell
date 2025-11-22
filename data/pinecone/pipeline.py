from data_loader import load_data
from vectorizer import get_embeddings
from db import upsert_vectors

def run_pipeline(raw_input):
    """
    Full pipeline:
    1. Standardize input
    2. Convert to embeddings
    3. Upsert into Pinecone
    """
    # Step 1: Load and standardize data
    data = load_data(raw_input)
    
    # Step 2: Vectorize
    texts = [d['text'] for d in data]
    embeddings = get_embeddings(texts)
    
    # Step 3: Upsert into Pinecone
    ids = [d['id'] for d in data]
    metadata = [{'text': d['text']} for d in data]
    upsert_vectors(embeddings, ids, metadata)
    
    print(f"Pipeline complete! {len(data)} vectors upserted.")

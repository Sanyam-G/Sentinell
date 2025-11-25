"""
Script to load vector_db_payload.json into Pinecone index.
"""

import json
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_NAME = "test-rag-index"

def load_json_data(file_path):
    """Load the JSON payload file."""
    with open(file_path, 'r') as f:
        # Handle the file starting with empty lines
        content = f.read().strip()
        if content.startswith(','):
            content = '[' + content[1:] + ']'
        elif not content.startswith('['):
            content = '[' + content + ']'
        return json.loads(content)

def get_embeddings(texts, model="text-embedding-3-large", dimensions=1024):
    """Get embeddings for texts."""
    client = OpenAI(api_key=OPENAI_API_KEY)
    embeddings = []
    for text in texts:
        response = client.embeddings.create(
            input=text,
            model=model,
            dimensions=dimensions
        )
        embeddings.append(response.data[0].embedding)
    return embeddings

def main():
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Check if index exists, create if not
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME not in existing_indexes:
        print(f"Creating index: {INDEX_NAME}")
        pc.create_index(
            name=INDEX_NAME,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        print(f"Index {INDEX_NAME} created!")
    else:
        print(f"Index {INDEX_NAME} already exists")
    
    # Connect to index
    index = pc.Index(INDEX_NAME)
    
    # Load JSON data
    print("Loading JSON data...")
    data = load_json_data("../vector_db_payload.json")
    print(f"Loaded {len(data)} items")
    
    # Prepare data for upsert
    texts = []
    ids = []
    metadatas = []
    
    for item in data:
        texts.append(item['text'])
        ids.append(item['id'])
        # Include all metadata plus the text
        metadata = item.get('metadata', {}).copy()
        metadata['text'] = item['text']
        metadata['type'] = item.get('type', 'unknown')
        metadata['timestamp'] = item.get('timestamp', '')
        metadatas.append(metadata)
    
    # Get embeddings in batches
    print("Generating embeddings...")
    batch_size = 100
    all_vectors = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        embeddings = get_embeddings(batch)
        all_vectors.extend(embeddings)
    
    # Upsert to Pinecone
    print("Upserting to Pinecone...")
    vectors_to_upsert = []
    for i, (vec, metadata) in enumerate(zip(all_vectors, metadatas)):
        vectors_to_upsert.append({
            'id': ids[i],
            'values': vec,
            'metadata': metadata
        })
    
    # Upsert in batches
    upsert_batch_size = 100
    for i in range(0, len(vectors_to_upsert), upsert_batch_size):
        batch = vectors_to_upsert[i:i+upsert_batch_size]
        index.upsert(vectors=batch)
        print(f"Upserted batch {i//upsert_batch_size + 1}/{(len(vectors_to_upsert)-1)//upsert_batch_size + 1}")
    
    print(f"\n✅ Successfully loaded {len(data)} vectors into {INDEX_NAME}!")
    
    # Verify
    stats = index.describe_index_stats()
    print(f"Index stats: {stats}")

if __name__ == "__main__":
    main()


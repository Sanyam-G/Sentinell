from openai import OpenAI

client = OpenAI()

def get_embeddings(texts: list, model: str = "text-embedding-3-large", dimensions: int = 1024) -> list:
    """
    Converts a list of text strings into embedding vectors.
    
    Args:
        texts: List of text strings to embed
        model: OpenAI embedding model to use
        dimensions: Dimension of the embedding vectors (default 1024 to match Pinecone index)
    """
    embeddings = []
    for t in texts:
        emb = client.embeddings.create(
            input=t, 
            model=model,
            dimensions=dimensions
        ).data[0].embedding
        embeddings.append(emb)
    return embeddings

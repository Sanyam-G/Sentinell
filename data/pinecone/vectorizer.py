from openai import OpenAI

client = OpenAI()

def get_embeddings(texts: list, model: str = "text-embedding-3-large") -> list:
    """
    Converts a list of text strings into embedding vectors.
    """
    embeddings = []
    for t in texts:
        emb = client.embeddings.create(input=t, model=model).data[0].embedding
        embeddings.append(emb)
    return embeddings

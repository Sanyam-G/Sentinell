import os
import pinecone
from openai import OpenAI

# ----------------------------
# 1️⃣ Load env vars
# ----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")

# ----------------------------
# 2️⃣ Initialize clients
# ----------------------------
# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Pinecone client
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
INDEX_NAME = "test-rag-index"

# Create the index if it doesn't exist
if INDEX_NAME not in pinecone.list_indexes():
    # 3072 dims for text-embedding-3-large
    pinecone.create_index(INDEX_NAME, dimension=3072)

index = pinecone.Index(INDEX_NAME)

# ----------------------------
# 3️⃣ Sample text data
# ----------------------------
texts = [
    "Hey team, we need to update the documentation.",
    "Meeting notes: discussed the new RAG pipeline and workflow.",
    "Reminder: submit your project updates by Friday."
]

# ----------------------------
# 4️⃣ Generate embeddings
# ----------------------------
embeddings = []
for t in texts:
    resp = client.embeddings.create(
        input=t,
        model="text-embedding-3-large"
    )
    embeddings.append(resp.data[0].embedding)

# ----------------------------
# 5️⃣ Upsert vectors into Pinecone
# ----------------------------
ids = [str(i) for i in range(len(texts))]
metadata = [{"text": t} for t in texts]

items = []
for i, vec in zip(ids, embeddings):
    items.append({
        "id": i,
        "values": vec,
        "metadata": metadata[int(i)]
    })

index.upsert(items)
print(f"✅ Upserted {len(items)} vectors into Pinecone!")

# ----------------------------
# 6️⃣ Query example
# ----------------------------
query_text = "Update the project docs"
query_vec = client.embeddings.create(
    input=query_text,
    model="text-embedding-3-large"
).data[0].embedding

results = index.query(vector=query_vec, top_k=2, include_metadata=True)
print("🔎 Query results:")
for match in results['matches']:
    print(f"Score: {match['score']:.4f}, Text: {match['metadata']['text']}")


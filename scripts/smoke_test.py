import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import httpx

load_dotenv()

# 1. Pinecone setup
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME", "recon-v1")

if not pc.has_index(index_name):
    pc.create_index(
        name=index_name,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

index = pc.Index(index_name)

# 2. Embedding model (downloads ~500MB first time)
embedder = SentenceTransformer(
    "nomic-ai/nomic-embed-text-v1.5",
    trust_remote_code=True,
)

# 3. Grab a test page
html = httpx.get("https://linear.app", timeout=30).text
chunk = html[:2000]

# 4. Embed and upsert
vec = embedder.encode(chunk).tolist()
index.upsert([{
    "id": "linear-home-1",
    "values": vec,
    "metadata": {"company": "Linear", "type": "homepage"},
}])

# 5. Query
q = embedder.encode("project management for software teams").tolist()
res = index.query(vector=q, top_k=3, include_metadata=True)

for m in res["matches"]:
    print(f"score={m['score']:.3f}  meta={m['metadata']}")

print("✅ Pipeline working")
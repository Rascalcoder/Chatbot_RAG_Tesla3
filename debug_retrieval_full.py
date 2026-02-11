"""
Full retrieval pipeline debug
"""
from src.rag_system import RAGSystem

print("="*60)
print("TELJES RETRIEVAL PIPELINE DEBUG")
print("="*60)

# RAG system
rag = RAGSystem()

# Stats
stats = rag.get_stats()
print(f"\n[1] Vector DB Status:")
print(f"    Documents: {stats.get('vector_db', {}).get('document_count', 0)}")
print(f"    Threshold: {rag.retrieval_engine.similarity_threshold}")

# Test query
query = "How to open the door?"
print(f"\n[2] Test Query: '{query}'")

# Generate query embedding
print(f"\n[3] Generating query embedding...")
query_embedding = rag.embedding_model.embed_text(query)
print(f"    Embedding shape: {len(query_embedding)}")
print(f"    Embedding sample: {query_embedding[:5]}")

# Search vector store directly
print(f"\n[4] Direct vector store search...")
try:
    raw_results = rag.vector_store.search(
        query_embedding=query_embedding,
        top_k=10
    )
    print(f"    Raw results count: {len(raw_results)}")
    
    if raw_results:
        print(f"\n    Top 3 raw results:")
        for i, doc in enumerate(raw_results[:3], 1):
            distance = doc.get('distance', 'N/A')
            text = doc.get('text', '')[:60]
            print(f"      [{i}] Distance: {distance} | {text}...")
    else:
        print("    NO RAW RESULTS!")
except Exception as e:
    print(f"    ERROR: {e}")

# Retrieval engine retrieve
print(f"\n[5] Retrieval engine retrieve...")
try:
    retrieved = rag.retrieval_engine.retrieve(query, top_k=10)
    print(f"    Retrieved count: {len(retrieved)}")
    
    if retrieved:
        print(f"\n    Top 3 retrieved:")
        for i, doc in enumerate(retrieved[:3], 1):
            similarity = doc.get('similarity', 'N/A')
            text = doc.get('text', '')[:60]
            print(f"      [{i}] Similarity: {similarity} | {text}...")
    else:
        print("    NO RETRIEVED RESULTS!")
        print("    Possible issue: similarity filtering too strict")
except Exception as e:
    print(f"    ERROR: {e}")

print("\n" + "="*60)



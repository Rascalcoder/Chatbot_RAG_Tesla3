"""Test ChromaDB distance metric and similarity calculation"""
from src.rag_system import RAGSystem
import numpy as np

print("="*60)
print("CHROMADB DISTANCE METRIC TESZT")
print("="*60)

rag = RAGSystem()

# Test queries
queries = [
    "How to open the door?",  # Releváns (angol)
    "Hogyan nyitom ki az ajtot?",  # Releváns (magyar)
    "What is quantum physics?",  # Nem releváns
]

for i, query in enumerate(queries, 1):
    print(f"\n{'='*60}")
    print(f"[{i}] Query: '{query}'")
    print(f"{'='*60}")
    
    # Retrieval (raw results)
    query_embedding = rag.embedding_model.embed_text(query)
    results = rag.vector_store.search(
        query_embedding=query_embedding,
        top_k=5
    )
    
    print(f"\n  Returned {len(results)} results")
    print(f"\n  Distance értékek:")
    
    distances = []
    for j, result in enumerate(results, 1):
        distance = result.get('distance', None)
        distances.append(distance)
        
        # Jelenlegi számítás
        similarity_current = 1.0 - (distance / 2.0)
        
        # Text preview
        text = result.get('text', '')[:60]
        
        print(f"    [{j}] distance={distance:.4f}, similarity={similarity_current:.4f}")
        print(f"        text: {text}...")
    
    # Statisztikák
    distances = [d for d in distances if d is not None]
    if distances:
        print(f"\n  Statisztikák:")
        print(f"    Min distance: {min(distances):.4f}")
        print(f"    Max distance: {max(distances):.4f}")
        print(f"    Mean distance: {np.mean(distances):.4f}")
        print(f"    Median distance: {np.median(distances):.4f}")
        
        # Ellenőrzés: [0, 2] tartomány?
        if all(0 <= d <= 2 for d in distances):
            print(f"    [OK] Minden distance [0, 2] tartományban (cosine distance)")
        else:
            print(f"    [X] VAN distance [0, 2] tartomanyon KIVUL!")
            print(f"       -> A similarity szamitas ROSSZ!")
        
        # Similarity tartomány
        similarities = [1.0 - (d / 2.0) for d in distances]
        print(f"    Similarity tartomány: [{min(similarities):.4f}, {max(similarities):.4f}]")
        
        # Jelenlegi threshold (0.3)
        threshold = 0.3
        passed = [s for s in similarities if s >= threshold]
        print(f"    Threshold (0.3) átmegy: {len(passed)}/{len(similarities)} chunk")

print("\n" + "="*60)
print("DIAGNÓZIS:")
print("="*60)

# ChromaDB metadata check
print("\nChromaDB collection metadata:")
try:
    collection = rag.vector_store._collection
    print(f"  Collection name: {collection.name}")
    print(f"  Count: {collection.count()}")
    # Try to get metadata if available
    metadata = collection.metadata if hasattr(collection, 'metadata') else {}
    print(f"  Metadata: {metadata}")
except Exception as e:
    print(f"  Error getting metadata: {e}")

print("\n" + "="*60)


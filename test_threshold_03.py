"""
Threshold 0.3 teszt magyar query-vel
"""
from src.rag_system import RAGSystem

print("="*60)
print("THRESHOLD 0.3 TESZT - MAGYAR QUERY")
print("="*60)

# RAG system (default threshold = 0.3)
rag = RAGSystem()

print(f"\n[1] Threshold: {rag.retrieval_engine.similarity_threshold}")

# Magyar query
query_hu = "Hogyan nyitom ki az ajtot?"
print(f"\n[2] Magyar Query: '{query_hu}'")

# Retrieval
retrieved_hu = rag.retrieval_engine.retrieve(query_hu, top_k=10)
print(f"\n[3] Retrieved chunks: {len(retrieved_hu)}")

if retrieved_hu:
    print("\n  Top 5 retrieved (similarity):")
    for i, doc in enumerate(retrieved_hu[:5], 1):
        sim = doc.get('similarity', 0)
        text = doc.get('text', '')[:70]
        print(f"    [{i}] Similarity: {sim:.3f} | {text}...")
else:
    print("  ❌ NINCS TALÁLAT! (similarity < 0.3)")

# Angol query (összehasonlítás)
query_en = "How to open the door?"
print(f"\n[4] Angol Query: '{query_en}' (összehasonlítás)")

retrieved_en = rag.retrieval_engine.retrieve(query_en, top_k=10)
print(f"    Retrieved chunks: {len(retrieved_en)}")

if retrieved_en:
    print("\n  Top 3 retrieved (similarity):")
    for i, doc in enumerate(retrieved_en[:3], 1):
        sim = doc.get('similarity', 0)
        text = doc.get('text', '')[:70]
        print(f"    [{i}] Similarity: {sim:.3f} | {text}...")

print("\n" + "="*60)
print("ÉRTÉKELÉS:")
print("="*60)

if len(retrieved_hu) == 0:
    print("❌ THRESHOLD 0.3 TÚL MAGAS magyar query-khoz!")
    print("   → Magyar query similarity: ~0.12-0.16")
    print("   → 0.3 threshold → 0 találat")
    print("   → AJÁNLÁS: threshold = 0.0 (minden chunk visszakerül)")
elif len(retrieved_hu) < 3:
    print("⚠️ THRESHOLD 0.3 KÖZEPESEN MŰKÖDIK")
    print(f"   → Csak {len(retrieved_hu)} chunk található")
    print("   → Lehet, hogy releváns chunk-ok kiesnek")
else:
    print("✅ THRESHOLD 0.3 MŰKÖDIK magyar query-khoz!")
    print(f"   → {len(retrieved_hu)} chunk található")

print("\n" + "="*60)



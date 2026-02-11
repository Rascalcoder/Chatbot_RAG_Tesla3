"""
Reranking működésének ellenőrzése
"""
from src.rag_system import RAGSystem

print("="*60)
print("RERANKING TESZT")
print("="*60)

# RAG system inicializálása
print("\n[1/5] RAG system betöltése...")
rag = RAGSystem()

# Reranker státusz
print(f"\n[2/5] Reranker státusz:")
print(f"  - use_reranking: {rag.reranker.use_reranking}")
print(f"  - model_name: {rag.reranker.model_name}")
print(f"  - model loaded: {rag.reranker._model is not None}")

# Teszt query
query = "Hogyan nyitom ki az ajtot?"
print(f"\n[3/5] Teszt query: '{query}'")

# Retrieval (rerank nélkül)
print(f"\n[4/5] Retrieval (top_k=10)...")
retrieved = rag.retrieval_engine.retrieve(query, top_k=10)
print(f"  Retrieved: {len(retrieved)} chunks")

if retrieved:
    print("\n  Top 5 retrieved chunk similarity:")
    for i, doc in enumerate(retrieved[:5], 1):
        sim = doc.get('similarity', 0)
        text_preview = doc.get('text', '')[:80]
        print(f"    [{i}] Similarity: {sim:.3f} | {text_preview}...")

# Reranking
print(f"\n[5/5] Reranking (top_k=3)...")
reranked = rag.reranker.rerank(query, retrieved, top_k=3)
print(f"  Reranked: {len(reranked)} chunks")

if reranked:
    print("\n  Top 3 reranked chunks:")
    for i, doc in enumerate(reranked, 1):
        rerank_score = doc.get('rerank_score', 0)
        original_sim = doc.get('similarity', 0)
        text_preview = doc.get('text', '')[:80]
        page_num = doc.get('metadata', {}).get('page_number')
        print(f"\n    [{i}] Rerank Score: {rerank_score:.3f} (orig sim: {original_sim:.3f})")
        print(f"        Page: {page_num}")
        print(f"        Text: {text_preview}...")

print("\n" + "="*60)
print("ÉRTÉKELÉS:")
print("="*60)

# Értékelés
if not rag.reranker.use_reranking:
    print("❌ RERANKING NINCS BEKAPCSOLVA!")
    print("   → Lehet, hogy a modell betöltése sikertelen.")
elif not rag.reranker._model:
    print("❌ RERANKING MODELL NINCS BETÖLTVE!")
    print("   → CrossEncoder inicializálás hibás.")
elif not reranked:
    print("❌ RERANKING NEM TALÁLT SEMMIT!")
    print("   → Nincs dokumentum feltöltve vagy retrieval sikertelen.")
else:
    print("✅ RERANKING MŰKÖDIK!")
    print(f"   → {len(reranked)} chunk került átrangsorolásra")
    
    # Score vizsgálat
    avg_rerank_score = sum(doc.get('rerank_score', 0) for doc in reranked) / len(reranked)
    print(f"   → Átlag rerank score: {avg_rerank_score:.3f}")
    
    if avg_rerank_score < -5:
        print("   ⚠️ ALACSONY RERANK SCORE-OK!")
        print("      → A cross-encoder nem találja relevánsnak a chunk-okat")
        print("      → Lehetséges okok:")
        print("         - Magyar query vs. angol chunk")
        print("         - ms-marco-MiniLM gyenge cross-lingual")
    elif avg_rerank_score > 5:
        print("   ✅ MAGAS RERANK SCORE-OK - Releváns találatok!")
    else:
        print("   ⚠️ KÖZEPES RERANK SCORE-OK")
        print("      → Működik, de lehet optimalizálni")

print("\n" + "="*60)



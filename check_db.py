from src.rag_system import RAGSystem
rag = RAGSystem()
stats = rag.get_stats()
print(f"Vector DB chunks: {stats.get('vector_db', {}).get('document_count', 0)}")

"""Check vector DB status"""
from src.rag_system import RAGSystem

print("Checking vector DB...")
rag = RAGSystem()
stats = rag.get_stats()
vector_stats = stats.get('vector_db', {})

doc_count = vector_stats.get('document_count', 0)
print(f"\nVector DB document count: {doc_count}")

if doc_count == 0:
    print("\n[WARNING] Vector DB is EMPTY! No documents uploaded.")
    print("You need to upload documents (e.g., model_3.pdf) in the Streamlit UI.")
else:
    print(f"\n[OK] Vector DB has {doc_count} documents.")
    print(f"Collection info: {vector_stats}")




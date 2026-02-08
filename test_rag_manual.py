#!/usr/bin/env python3
"""
Manual test: RAG System initialization and model_3.pdf processing
"""
import sys
sys.path.insert(0, '.')

from src.rag_system import RAGSystem
import logging

# Logging setup: both console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_rag_manual.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

print("\n" + "="*60)
print("=== RAG Sistem inicializálása ===")
print("="*60 + "\n")

try:
    rag = RAGSystem()
    print("✅ RAG rendszer sikeresen inicializálva\n")
    
    print("="*60)
    print("=== model_3.pdf feldolgozása ===")
    print("="*60 + "\n")
    rag.add_documents(['./model_3.pdf'])
    print("✅ Dokumentum sikeresen hozzáadva\n")
    
    print("="*60)
    print("=== RAG Statisztikák ===")
    print("="*60 + "\n")
    stats = rag.get_stats()
    vector_db_docs = stats.get("vector_db", {}).get("document_count", 0)
    print(f"Vector DB dokumentumok: {vector_db_docs}\n")
    
    print("="*60)
    print("=== Tesztkérdés ===")
    print("="*60 + "\n")
    response = rag.query('Mi a Tesla legújabb technológiája?', stream=False)
    answer = response.get("response", "N/A")
    context_count = len(response.get("context", []))
    
    print(f"Válasz (első 500 char): {answer[:500]}...\n")
    print(f"Felhasznált kontextus dokumentumok: {context_count}\n")
    
    print("="*60)
    print("✅ FRONTEND MŰKÖDTEST SIKERES")
    print("="*60 + "\n")
    
except Exception as e:
    print(f"\n❌ HIBA TÖRTÉNT: {type(e).__name__}")
    print(f"Üzenet: {e}\n")
    print("="*60)
    print("TELJES STACK TRACE:")
    print("="*60 + "\n")
    import traceback
    traceback.print_exc()
    print("\n" + "="*60)
    sys.exit(1)

"""Test system prompt loading"""
import os
from src.rag_system import RAGSystem

print("="*50)
print("RAG SYSTEM PROMPT TEST")
print("="*50)

try:
    print("\n[1/3] Initializing RAG system...")
    rag = RAGSystem()
    print("✅ RAG system initialized")
    
    print(f"\n[2/3] System message status:")
    print(f"  - Is None: {rag.system_message is None}")
    print(f"  - Length: {len(rag.system_message) if rag.system_message else 0}")
    
    if rag.system_message:
        print(f"\n[3/3] System message content (first 300 chars):")
        print("-" * 50)
        print(rag.system_message[:300])
        print("-" * 50)
        print("\n✅ System prompt loaded successfully!")
    else:
        print("\n❌ System prompt is None - using default prompt!")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()




"""Test system prompt loading - simple version"""
import os
from src.rag_system import RAGSystem

print("="*50)
print("SYSTEM PROMPT TEST")
print("="*50)

try:
    print("\nInitializing RAG system...")
    rag = RAGSystem()
    print("OK - RAG initialized")
    
    print(f"\nSystem message is None: {rag.system_message is None}")
    
    if rag.system_message:
        print(f"System message length: {len(rag.system_message)}")
        print("\nFirst 300 characters:")
        print("-" * 50)
        print(rag.system_message[:300])
        print("-" * 50)
    else:
        print("WARNING: System prompt is None!")
        
except Exception as e:
    print(f"Error: {e}")




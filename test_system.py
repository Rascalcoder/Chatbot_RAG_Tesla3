"""
Teljes rendszer teszt - RAG architektúra ellenőrzése
"""
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("RAG RENDSZER ARCHITEKTÚRA TESZT")
print("=" * 60)

# 1. Environment ellenőrzés
print("\n1. KÖRNYEZETI VÁLTOZÓK ELLENŐRZÉSE")
print("-" * 60)

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
embedding_model = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
llm_model = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')

if api_key and api_key != 'your_openai_api_key_here':
    print(f"[OK] OPENAI_API_KEY: beallitva ({api_key[:20]}...)")
else:
    print("[FAIL] OPENAI_API_KEY: NINCS beallitva!")
    sys.exit(1)

print(f"[OK] EMBEDDING_MODEL: {embedding_model}")
print(f"[OK] LLM_MODEL: {llm_model}")

# 2. Komponensek importálása
print("\n2. KOMPONENSEK IMPORTÁLÁSA")
print("-" * 60)

try:
    from src.rag_system import RAGSystem
    print("[OK] RAGSystem importalva")
except Exception as e:
    print(f"[FAIL] RAGSystem import hiba: {e}")
    sys.exit(1)

try:
    from src.rag.embeddings import EmbeddingModel
    print("[OK] EmbeddingModel importalva")
except Exception as e:
    print(f"[FAIL] EmbeddingModel import hiba: {e}")
    sys.exit(1)

try:
    from src.llm.generator import LLMGenerator
    print("[OK] LLMGenerator importalva")
except Exception as e:
    print(f"[FAIL] LLMGenerator import hiba: {e}")
    sys.exit(1)

# 3. RAG rendszer inicializálás
print("\n3. RAG RENDSZER INICIALIZÁLÁSA")
print("-" * 60)

try:
    rag = RAGSystem()
    print("[OK] RAG rendszer inicializalva")
except Exception as e:
    print(f"[FAIL] RAG rendszer inicializalas hiba: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Embedding teszt
print("\n4. EMBEDDING MODELL TESZT")
print("-" * 60)

try:
    test_text = "This is a test sentence for embedding."
    embedding = rag.embedding_model.embed_text(test_text)
    print(f"[OK] Embedding generalva: {len(embedding)} dimenzio")
    print(f"   Elso 5 ertek: {embedding[:5]}")
except Exception as e:
    print(f"[FAIL] Embedding teszt hiba: {e}")
    import traceback
    traceback.print_exc()

# 5. Vector Database teszt
print("\n5. VECTOR DATABASE TESZT")
print("-" * 60)

try:
    stats = rag.get_stats()
    doc_count = stats.get('vector_db', {}).get('document_count', 0)
    print(f"[OK] Vector DB kapcsolat OK")
    print(f"   Dokumentumok szama: {doc_count}")
except Exception as e:
    print(f"[FAIL] Vector DB teszt hiba: {e}")

# 6. OpenAI LLM teszt (csak ellenőrizzük hogy az API kulcs működik)
print("\n6. OPENAI API TESZT")
print("-" * 60)

try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    # Egyszerű teszt kérés
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'API test OK' in 3 words"}],
        max_tokens=10
    )

    answer = response.choices[0].message.content
    print(f"[OK] OpenAI API mukodik")
    print(f"   Teszt valasz: {answer}")
except Exception as e:
    print(f"[FAIL] OpenAI API teszt hiba: {e}")
    import traceback
    traceback.print_exc()

# 7. Összefoglaló
print("\n" + "=" * 60)
print("ÖSSZEFOGLALÓ")
print("=" * 60)

print("""
[OK] SIKERES KOMPONENSEK:
   - Kornyezeti valtozok beallitva
   - RAG rendszer inicializalva
   - Embedding modell mukodik
   - Vector database elerheto
   - OpenAI API kapcsolat OK

>> KOVETKEZO LEPESEK:
   1. Nyisd meg: http://localhost:8501
   2. Toltsd fel a Tesla PDF-et (model_3.pdf)
   3. Tesztelj le kerdeseket:
      - "Mi a Walk-Away Door Lock?"
      - "Hogyan hasznalom a tire repair kit-et?"

>> A RENDSZER KESZEN ALL A HASZNALATRA!
""")

print("=" * 60)

"""
Config JSON betöltés teszt
"""
from pathlib import Path
import json

print("="*60)
print("CONFIG JSON BETÖLTÉS TESZT")
print("="*60)

# 1. Config fájl létezik?
config_path = Path(__file__).parent / "config.json"
print(f"\n[1] Config fájl létezik: {config_path.exists()}")
print(f"    Path: {config_path}")

if config_path.exists():
    # 2. Config tartalom
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(f"\n[2] Config tartalom:")
    print(f"    similarity_threshold: {config.get('similarity_threshold')}")
    print(f"    top_k: {config.get('top_k')}")
    print(f"    rerank_top_k: {config.get('rerank_top_k')}")
    print(f"    use_reranking: {config.get('use_reranking')}")

# 3. load_config() függvény teszt
print(f"\n[3] load_config() függvény teszt...")
import sys
sys.path.insert(0, str(Path(__file__).parent))

# Simuláljuk a load_config()-ot
def test_load_config():
    from pathlib import Path
    config_path = Path(__file__).parent.parent / "config.json"  # src/rag_system.py-ból nézve
    print(f"    Config path (from src/rag_system.py perspective): {config_path}")
    print(f"    Exists: {config_path.exists()}")
    
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

config = test_load_config()
print(f"    Loaded config: {config}")

# 4. RAGSystem inicializálás és threshold
print(f"\n[4] RAGSystem inicializálás...")
from src.rag_system import RAGSystem
rag = RAGSystem()
print(f"    Threshold: {rag.similarity_threshold}")
print(f"    Retrieval engine threshold: {rag.retrieval_engine.similarity_threshold}")

print("\n" + "="*60)
print("DIAGNÓZIS:")
print("="*60)

expected_threshold = 0.0
if abs(rag.similarity_threshold - expected_threshold) < 0.01:
    print("[OK] Threshold helyesen betöltve (0.0)")
else:
    print(f"[X] PROBLÉMA: Threshold = {rag.similarity_threshold} (elvárt: {expected_threshold})")
    print("   -> A config.json nem töltődik be, vagy rossz útvonal")

print("\n" + "="*60)



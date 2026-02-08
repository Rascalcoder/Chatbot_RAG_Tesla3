# Változások

## Lokális Modellek Integrációja

### BGE-M3 Embedding Modell
- ✅ BGE-M3 embedding modell integrálva (`BAAI/bge-m3`)
- ✅ FlagEmbedding és sentence-transformers támogatás
- ✅ Alapértelmezett embedding modellként beállítva
- ✅ 1024 dimenziós embedding vektorok

### Qwen-4B LLM Modell
- ✅ Qwen-4B Instruct modell integrálva (`Qwen/Qwen2.5-4B-Instruct`)
- ✅ Lokális generálás transformers könyvtárral
- ✅ Streaming támogatás TextIteratorStreamer-rel
- ✅ GPU és CPU támogatás
- ✅ Alapértelmezett LLM modellként beállítva

### Módosított Fájlok
- `src/rag/embeddings.py` - BGE-M3 támogatás
- `src/llm/generator.py` - Qwen-4B lokális generálás
- `src/llm/streaming.py` - Qwen-4B streaming
- `src/rag_system.py` - Alapértelmezett lokális modellek
- `requirements.txt` - Új függőségek (FlagEmbedding, transformers, torch)

### Új Dokumentáció
- `MODEL_INFO.md` - Részletes modell információk
- `CHANGELOG.md` - Ez a fájl

### Konfiguráció
- Alapértelmezetten lokális modellek használata
- OpenAI API opcionális (csak ha explicit módon bekapcsolod)
- `.env` fájl opcionális (alapértelmezett értékek használata)

## Használat

A projekt mostantól **automatikusan** a BGE-M3 és Qwen-4B modelleket használja lokálisan.
Nincs szükség OpenAI API kulcsra, kivéve ha explicit módon OpenAI-t szeretnél használni.

Az első futtatáskor a modellek automatikusan letöltődnek (~10 GB összesen).


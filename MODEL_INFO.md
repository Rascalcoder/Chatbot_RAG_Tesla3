# Modell Információk

## Használt Modellek

### BGE-M3 Embedding Modell
- **Modell**: `BAAI/bge-m3`
- **Típus**: Multilingual embedding modell
- **Dimenzió**: 1024
- **Használat**: Dokumentumok és query-k embedding generálásához
- **Könyvtár**: FlagEmbedding vagy sentence-transformers
- **Méret**: ~2.2 GB

**Telepítés**:
```bash
pip install FlagEmbedding sentence-transformers
```

**Első használatkor** automatikusan letöltődik a Hugging Face-ről.

### Qwen-4B LLM Modell
- **Modell**: `Qwen/Qwen2.5-4B-Instruct`
- **Típus**: Instruct-finetuned nyelvi modell
- **Méret**: ~8 GB
- **Használat**: Válaszgenerálás RAG kontextussal
- **Könyvtár**: transformers (Hugging Face)
- **Támogatás**: Streaming válaszok

**Telepítés**:
```bash
pip install transformers torch accelerate
```

**Első használatkor** automatikusan letöltődik a Hugging Face-ről.

## Hardver Követelmények

### Minimális
- **RAM**: 16 GB (8 GB modell + 8 GB rendszer)
- **GPU**: Opcionális, de ajánlott (CUDA kompatibilis)
- **Tárhely**: ~15 GB (modellek + adatok)

### Ajánlott
- **RAM**: 32 GB
- **GPU**: NVIDIA GPU 8+ GB VRAM (pl. RTX 3060, RTX 4060)
- **Tárhely**: 20+ GB

## GPU Használat

Ha NVIDIA GPU-d van, a modellek automatikusan GPU-ra töltődnek:
- CUDA 11.8+ szükséges
- PyTorch automatikusan detektálja a GPU-t

CPU-n is működik, de lassabb lesz.

## Alternatív Modellek

Ha más modelleket szeretnél használni, módosítsd a `.env` fájlban:

```env
EMBEDDING_MODEL=egyéb-embedding-modell
LLM_MODEL=egyéb-llm-modell
```

Vagy a kódban közvetlenül:
```python
embedding_model = EmbeddingModel(model_name="egyéb-modell", use_openai=False)
llm_generator = LLMGenerator(model_name="egyéb-modell", use_openai=False)
```

## Teljesítmény Optimalizálás

### Quantizáció (8-bit)
A Qwen modell 8-bit quantizációval is használható kevesebb memóriához:

```python
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0
)
```

### Batch Processing
A BGE-M3 embedding batch-ben is futtatható több dokumentumhoz egyszerre.

## Hibaelhárítás

### "Out of Memory" hiba
- Csökkentsd a `max_tokens` értékét
- Használj 8-bit quantizációt
- Csökkentsd a batch méretet

### Lassú generálás
- Használj GPU-t ha van
- Csökkentsd a `max_tokens` értékét
- Használj streaming-et a jobb UX-hez

### Modell letöltési hiba
- Ellenőrizd az internetkapcsolatot
- Próbáld meg manuálisan letölteni a Hugging Face-ről
- Használj Hugging Face token-t ha szükséges


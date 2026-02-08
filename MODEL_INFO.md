# Modell Információk

## 🎯 Támogatott Konfigurációk

A projekt **HIBRID konfigurációt** támogat - választhatsz a rendszered szerint.

### Konfiguráció A: Hibrid (Ajánlott 8 GB RAM-hoz)
**Embedding**: Helyi kis modell
**LLM**: OpenAI felhő API

### Konfiguráció B: Teljes Lokális (16+ GB RAM-hoz)
**Embedding**: Helyi nagy modell
**LLM**: Helyi Qwen modell

---

## Embedding Modellek

### 🔹 MiniLM (Kis, Gyors)
- **Modell**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimenzió**: 384
- **Méret**: ~90 MB
- **RAM igény**: ~500 MB
- **Használat**: Kisebb rendszerekhez, HIBRID konfigurációhoz
- **Könyvtár**: sentence-transformers

**Előnyök**: Gyors, kis memóriaigény, megfelelő pontosság
**Hátrányok**: Kisebb dimenzió (384 vs 1024)

### 🔹 BGE-M3 (Nagy, Pontos)
- **Modell**: `BAAI/bge-m3`
- **Dimenzió**: 1024
- **Méret**: ~1.2 GB
- **RAM igény**: ~2-3 GB
- **Használat**: Teljes lokális konfigurációhoz
- **Könyvtár**: FlagEmbedding vagy sentence-transformers

**Előnyök**: Magas pontosság, multilingual támogatás
**Hátrányok**: Nagyobb memóriaigény

**Telepítés**:
```bash
pip install FlagEmbedding sentence-transformers
```

---

## LLM Modellek

### 🔹 OpenAI GPT-3.5-turbo (Felhő)
- **Modell**: `gpt-3.5-turbo`
- **Típus**: OpenAI API
- **Költség**: ~$0.0005-0.001 / válasz
- **RAM igény**: 0 GB (felhő)
- **Sebesség**: Gyors (~1-3 másodperc)
- **Használat**: HIBRID konfigurációhoz

**Előnyök**: Nincs RAM igény, gyors, megbízható
**Hátrányok**: API kulcs és internet szükséges, költség

**Beállítás**:
```env
OPENAI_API_KEY=your_api_key_here
LLM_MODEL=gpt-3.5-turbo
```

### 🔹 Qwen3-4B (Lokális)
- **Modell**: `Qwen/Qwen3-4B-Instruct-2507`
- **Típus**: Instruction-tuned nyelvi modell
- **Méret**: ~8-10 GB
- **RAM igény**: ~10-12 GB
- **Sebesség**: Lassabb CPU-n (~10-30s), gyors GPU-n (~1-3s)
- **Használat**: Teljes lokális konfigurációhoz
- **Könyvtár**: transformers (Hugging Face)
- **Támogatás**: Streaming válaszok

**Előnyök**: Ingyenes, privát, offline működés
**Hátrányok**: Nagy RAM igény, lassabb CPU-n

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


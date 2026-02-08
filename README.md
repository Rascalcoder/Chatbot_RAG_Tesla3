# RAG Alapú AI Asszisztens

Ez a projekt egy teljes körű RAG (Retrieval-Augmented Generation) alapú AI asszisztens implementációja, amely képes dokumentumok feldolgozására, releváns információk visszakeresésére és intelligens válaszok generálására.

## 🚀 Funkciók

### RAG Rendszer Architektúra
- ✅ Dokumentum feldolgozás és chunking stratégia
- ✅ Embedding modell integráció (OpenAI, lokális alternatívák)
- ✅ Vektor adatbázis (ChromaDB)
- ✅ Retrieval és reranking mechanizmus
- ✅ LLM integráció válaszgeneráláshoz (streaming támogatással)

### Alkalmazás Funkciók
- ✅ Webes felület (Streamlit)
- ✅ Dokumentum feltöltés és kezelés
- ✅ Streaming válaszok támogatása
- ✅ Session/conversation management

### Háromszintű Evaluation Framework
- ✅ **RAG szintű értékelés**: Retrieval minőség (precision, recall, MRR), embedding modell teljesítmény, chunking stratégia hatékonysága
- ✅ **Prompt szintű értékelés**: Single-turn eval, context relevance, hallucináció detektálás, LLM-as-Judge
- ✅ **Alkalmazás szintű értékelés**: Teljes user journey tesztelés, response quality, latency és performance metrikák

### Monitoring és Analitika
- ✅ Token használat és költség tracking
- ✅ Latency metrikák (first token, total response time)

## 📋 Telepítés

### Előfeltételek
- Python 3.9 vagy újabb
- pip vagy conda

### Lépések

1. **Repository klónozása**
```bash
git clone <repository-url>
cd "7.het_Záró projekt"
```

2. **Virtuális környezet létrehozása (ajánlott)**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# vagy
venv\Scripts\activate  # Windows
```

3. **Függőségek telepítése**
```bash
pip install -r requirements.txt
```

4. **Környezeti változók beállítása**
```bash
cp .env.example .env
# Szerkeszd a .env fájlt és add hozzá az API kulcsokat
```

5. **Alkalmazás indítása**
```bash
streamlit run app.py
```

A böngészőben automatikusan megnyílik a `http://localhost:8501` címen.

## 🔧 Konfiguráció

A projekt **HIBRID konfigurációt** támogat - rugalmasan választhatsz helyi és felhő alapú modellek között:

### 🎯 Ajánlott Konfiguráció (8 GB RAM-hoz):
- **Embedding**: `sentence-transformers/all-MiniLM-L6-v2` (helyi, ~90 MB)
- **LLM**: `gpt-3.5-turbo` (OpenAI API, nincs RAM igény)
- **RAM igény**: ~1-2 GB ✅

### 🚀 Teljes Lokális Konfiguráció (16+ GB RAM-hoz):
- **Embedding**: `BAAI/bge-m3` (helyi, ~1.2 GB)
- **LLM**: `Qwen/Qwen3-4B-Instruct-2507` (helyi, ~8-10 GB)
- **RAM igény**: ~12-15 GB

A `.env` fájlban beállítható környezeti változók:
- `OPENAI_API_KEY`: OpenAI API kulcs (ha OpenAI LLM-et használsz)
- `EMBEDDING_MODEL`: Embedding modell neve
  - Lokális: `BAAI/bge-m3`, `sentence-transformers/all-MiniLM-L6-v2`
  - OpenAI: `text-embedding-ada-002`
- `LLM_MODEL`: LLM modell neve
  - Lokális: `Qwen/Qwen3-4B-Instruct-2507`
  - OpenAI: `gpt-3.5-turbo`, `gpt-4`
- `VECTOR_DB_PATH`: Vektor adatbázis elérési útja
- `CHUNK_SIZE`: Dokumentum chunk méret (alapértelmezett: 1000)
- `CHUNK_OVERLAP`: Chunk átfedés (alapértelmezett: 200)

**Fontos**: A helyi modellek automatikusan letöltődnek az első használatkor. A rendszer automatikusan felismeri az OpenAI modelleket (ha a modell név tartalmazza a "gpt-" előtagot).

## 📁 Projekt Struktúra

```
.
├── app.py                      # Streamlit főalkalmazás
├── src/
│   ├── __init__.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── document_processor.py    # Dokumentum feldolgozás
│   │   ├── chunking.py              # Chunking stratégia
│   │   ├── embeddings.py            # Embedding kezelés
│   │   ├── vector_store.py           # Vektor adatbázis
│   │   ├── retrieval.py              # Retrieval mechanizmus
│   │   └── reranking.py              # Reranking
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── generator.py              # LLM válaszgenerálás
│   │   └── streaming.py              # Streaming támogatás
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── rag_eval.py                # RAG szintű értékelés
│   │   ├── prompt_eval.py             # Prompt szintű értékelés
│   │   ├── app_eval.py                # Alkalmazás szintű értékelés
│   │   └── test_cases.py              # Teszt esetek
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── metrics.py                 # Metrikák gyűjtése
│   │   └── analytics.py               # Analitika
│   └── utils/
│       ├── __init__.py
│       └── session_manager.py         # Session kezelés
├── data/
│   └── documents/                    # Feltöltött dokumentumok
├── evaluations/
│   ├── rag_evaluation_results.json
│   ├── prompt_evaluation_results.json
│   └── app_evaluation_results.json
├── tests/
│   ├── test_rag.py
│   ├── test_retrieval.py
│   └── test_evaluation.py
├── requirements.txt
├── .env.example
└── README.md
```

## 🧪 Evaluation Futtatása

### RAG Szintű Evaluation
```bash
python -m src.evaluation.rag_eval
```

### Prompt Szintű Evaluation
```bash
python -m src.evaluation.prompt_eval
```

### Alkalmazás Szintű Evaluation
```bash
python -m src.evaluation.app_eval
```

## 📊 Monitoring Dashboard

A monitoring dashboard elérhető a Streamlit alkalmazásban a "Monitoring" oldalon, ahol megtekinthetők:
- Token használat statisztikák
- Latency metrikák
- Költség tracking
- Használati trendek

## 📝 Használat

### Alapvető Használat

1. **Dokumentum feltöltés**: A főoldalon tölts fel PDF, TXT vagy DOCX fájlokat
2. **Kérdések feltevése**: A chat felületen tegyél fel kérdéseket a feltöltött dokumentumokról
3. **Eredmények megtekintése**: A válaszok streaming formában jelennek meg
4. **Evaluation futtatása**: Az Evaluation oldalon futtathatsz teszteket

### Tesla Model 3 Kézikönyv Használata

Ha a `model_3.pdf` fájl a projekt könyvtárában van:

**Opció 1: Streamlit app-ban**
1. Indítsd el az app-ot: `streamlit run app.py`
2. A sidebar-ban töltsd fel a `model_3.pdf` fájlt
3. Kérdezz a Model 3-ról!

**Opció 2: Teszt script**
```bash
python test_model3_manual.py
```

Ez automatikusan betölti a PDF-et és futtat teszt kérdéseket, majd interaktív módba lép.

**Opció 3: Előre betöltés**
```bash
python load_model3_manual.py
```

Ez előre betölti a dokumentumot, így a Streamlit app indításakor már elérhető lesz.

## 🎥 Videó Prezentációk

A projekthez 2 db Loom videó készül:
1. **Technikai bemutató** (5 perc): Architektúra, RAG pipeline, evaluation framework, monitoring
2. **Felhasználói demo** (5 perc): Dokumentum feltöltés, kérdések, hibakezelés, teljesítmény

## 📄 Licenc

Ez a projekt egy záróprojekt része.

## 👥 Szerző

Projekt készítő: [Név]

---

Sikeres használatot kívánunk! 🚀

## 🔐 HuggingFace token (biztonság)

Ha a projekt HuggingFace modellekhez hozzáférést igényel, a token kezelése legyen biztonságos:

- Ajánlott: futtasd a `huggingface-cli login` parancsot (telepítsd a `huggingface-hub`-ot), ez menti a tokent lokálisan a cache-be.
- Alternatíva: hozz létre egy lokális `.env` fájlt a projekt gyökerében (ne committeld):

```env
# .env (NE add hozzá a git-hez)
HUGGINGFACE_HUB_TOKEN=hf_xxxYOURTOKENxxxxx
```

- Ügyelj rá, hogy a `HUGGINGFACE_HUB_TOKEN.env` vagy `.env` fájlok NEM kerüljenek a verziókezelésbe; a projekt `.gitignore` tartalmazza ezeket.

Ha bizonytalan vagy, használd a `huggingface-cli login`-t.


# Telepítési Útmutató

## Gyors Kezdés

### 1. Függőségek Telepítése

```bash
pip install -r requirements.txt
```

### 2. Környezeti Változók Beállítása (Opcionális)

A projekt alapértelmezetten **BGE-M3 embedding** és **Qwen-4B LLM** lokális modelleket használ.
Ha szeretnél `.env` fájlt létrehozni (opcionális, csak ha más modelleket szeretnél):

```env
# Opcionális - csak ha OpenAI-t szeretnél használni
OPENAI_API_KEY=your_api_key_here

# Alapértelmezett lokális modellek (nem kell beállítani)
EMBEDDING_MODEL=BAAI/bge-m3
LLM_MODEL=Qwen/Qwen2.5-4B-Instruct

VECTOR_DB_PATH=./data/vector_db
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=5
```

**Megjegyzés**: Az első futtatáskor a modellek automatikusan letöltődnek (~8-10 GB).

### 3. Alkalmazás Indítása

```bash
streamlit run app.py
```

A böngészőben automatikusan megnyílik a `http://localhost:8501` címen.

## Evaluation Futtatása

### RAG Szintű Evaluation

```bash
python run_evaluation.py --type rag
```

### Prompt Szintű Evaluation

```bash
python run_evaluation.py --type prompt
```

### Alkalmazás Szintű Evaluation

```bash
python run_evaluation.py --type app
```

### Összes Evaluation

```bash
python run_evaluation.py --type all
```

## Használat

### Általános Használat

1. **Dokumentum Feltöltés**: 
   - A bal oldali sidebar-ban tölts fel PDF, TXT vagy DOCX fájlokat
   - Kattints a "Dokumentumok Hozzáadása" gombra

2. **Kérdések Feltevése**:
   - A chat mezőben tegyél fel kérdéseket a feltöltött dokumentumokról
   - A válaszok streaming formában jelennek meg

3. **Monitoring**:
   - A "Monitoring" oldalon tekintheted meg a használati statisztikákat
   - Token használat, költség, latency metrikák

### Tesla Model 3 Kézikönyv

Ha a `model_3.pdf` fájl a projekt könyvtárában van:

**Gyors tesztelés:**
```bash
python test_model3_manual.py
```

**Előre betöltés (ajánlott):**
```bash
python load_model3_manual.py
streamlit run app.py
```

Ezután a Streamlit app-ban már elérhető lesz a Model 3 kézikönyv, és közvetlenül kérdezhetsz rá!

## Hibaelhárítás

### Hiba: "OPENAI_API_KEY nincs beállítva"

- Ellenőrizd, hogy a `.env` fájl létezik és tartalmazza az `OPENAI_API_KEY` változót

### Hiba: "chromadb nincs telepítve"

```bash
pip install chromadb
```

### Hiba: Dokumentumok nem töltődnek be

- Ellenőrizd a fájl formátumot (PDF, TXT, DOCX)
- Nézd meg a konzol üzeneteket hibákért

## További Információk

Lásd a `README.md` fájlt részletesebb dokumentációért.


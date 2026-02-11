# Bugfix: Cross-lingual Query Support (Magyar → Angol)

## Probléma

A chatbot nem a feltöltött dokumentumból válaszolt magyar query-k esetén, mert:

1. **Threshold túl korán szűrt**: A retrieval-ben alkalmazott 0.3-as similarity threshold 0 chunk-ot adott vissza cross-lingual esetben (magyar query + angol PDF → 0.12-0.16 similarity).

2. **Cross-lingual matching gyenge**: Az embedding modell (`all-MiniLM-L6-v2`) nem támogatja jól a cross-lingual matching-et, ezért magyar query-k esetén alacsony similarity score-okat adott.

3. **Reranking nem működött**: A cross-encoder (`ms-marco-MiniLM-L-6-v2`) negatív score-okat adott cross-lingual esetben (-9.8 vs +7.9 angol query esetén).

## Megoldás

### 1. Threshold eltávolítása a retrieval-ből
**Fájl**: `src/rag/retrieval.py`

A threshold-ot csak figyelmeztetésként használjuk, nem szűrünk vele:

```python
# Threshold csak WARNING-ként, nem filterként
if self.similarity_threshold > 0:
    below_threshold = [r for r in scored_results if r['similarity'] < self.similarity_threshold]
    if below_threshold:
        logger.warning(f"Retrieval: {len(below_threshold)}/{len(scored_results)} chunk similarity < {self.similarity_threshold}")

logger.info(f"Retrieval: {len(scored_results)} találat (threshold nem alkalmazva, reranking majd szűr)")
return scored_results
```

### 2. Reranking fallback similarity alapján
**Fájl**: `src/rag_system.py`

Ha a reranking negatív score-okat ad (cross-lingual probléma), similarity alapján választunk:

```python
if self.reranker.use_reranking and retrieved:
    reranked = self.reranker.rerank(query_for_retrieval, retrieved, top_k=top_k or self.top_k)
    
    # Ha a reranking negatív score-okat ad, similarity alapján választunk
    if reranked and reranked[0].get('rerank_score', 0) < -5:
        logger.warning(f"Reranking negatív score-okat ad, similarity alapján választunk (fallback)")
        retrieved_sorted = sorted(retrieved, key=lambda x: x.get('similarity', 0), reverse=True)
        reranked = retrieved_sorted[:top_k or self.top_k]
```

### 3. Automatikus query fordítás angolra
**Fájl**: `src/rag_system.py`

Magyar query-k automatikus fordítása angolra az OpenAI API-val a retrieval előtt:

```python
def _translate_query_if_needed(self, query: str) -> str:
    """Query fordítása angolra, ha szükséges"""
    # Magyar ékezetes karakterek VAGY gyakori magyar szavak detektálása
    hungarian_chars = 'áéíóöőúüűÁÉÍÓÖŐÚÜŰ'
    hungarian_words = ['hogyan', 'miért', 'milyen', 'hol', 'mikor', 'mit', 'ki', 'be', 'fel', 'le', 'meg', 'el', 'vissza']
    
    query_lower = query.lower()
    has_hungarian_char = any(char in query for char in hungarian_chars)
    has_hungarian_word = any(word in query_lower for word in hungarian_words)
    
    if not (has_hungarian_char or has_hungarian_word):
        return query  # Már angol
    
    # OpenAI API-val fordítás
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Translate the following query to English. Return only the translation, no explanations."},
                {"role": "user", "content": query}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        translated = response.choices[0].message.content.strip()
        logger.info(f"Query fordítva: '{query}' -> '{translated}'")
        return translated
        
    except Exception as e:
        logger.warning(f"Query fordítási hiba: {e}. Eredeti query használata.")
        return query
```

**Használat**:
```python
def query(self, query: str, stream: bool = False, top_k: Optional[int] = None):
    original_query = query
    query_for_retrieval = self._translate_query_if_needed(query)  # Fordítás
    
    # Retrieval fordított query-vel
    retrieved = self.retrieval_engine.retrieve(query_for_retrieval, top_k=...)
    
    # Reranking fordított query-vel
    reranked = self.reranker.rerank(query_for_retrieval, retrieved, top_k=...)
    
    # LLM EREDETI query-vel (nem fordítottal!)
    answer = self.llm_generator.generate(original_query, reranked, system_message=...)
```

## Eredmények

### Előtte (nem működött):
```
Query: "Hogyan nyitom ki az ajtot?"
Translated: "Hogyan nyitom ki az ajtot?" (nem fordította)
Retrieved: 10 chunks (de similarity < 0.3, mind kiszűrve)
Reranked: 0 chunks
Context: Nincs
Answer: Általános válasz (nem a dokumentumból)
```

### Utána (működik):
```
Query: "Hogyan nyitom ki az ajtot?"
Translated: "How do I open the door?" (lefordította!)
Retrieved: 10 chunks (similarity 0.12-0.16, de nem szűr)
Reranked: 5 chunks (rerank score: 7.8)
Context: "Using Exterior Door Handles..." (releváns!)
Answer: "Külső ajtókilincs használata..." (a dokumentumból!)
```

## Tesztelés

```bash
python test_translation_fix.py
```

Vagy a Streamlit UI-ban:
1. Kérdezz magyarul: "Hogyan nyitom ki az ajtot?"
2. Ellenőrizd a forrásokat: releváns context chunk-ok jelennek meg
3. A válasz a dokumentumból jön

## Megjegyzések

- A fordítás csak akkor történik, ha magyar karaktereket vagy magyar szavakat detektál
- A fordítás OpenAI API-t használ (gpt-3.5-turbo), ezért szükséges az `OPENAI_API_KEY`
- Az LLM-nek mindig az **eredeti** (magyar) query-t adjuk át, hogy magyar nyelven válaszoljon
- A retrieval és reranking a **fordított** (angol) query-vel dolgozik



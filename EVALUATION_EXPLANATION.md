# Miért jönnek ki mindig ugyanazok az eredmények?

## Rövid válasz

Az evaluation **tényleg újrafut** minden alkalommal, de az eredmények **determinisztikusak**, mert:

1. **Statikus tesztesetek**: A `PROMPT_TEST_CASES` mindig ugyanazokat a query-ket tartalmazza
2. **Determinisztikus LLM**: Az LLM `temperature=0`-val fut, ami mindig ugyanazt a választ adja ugyanarra a query-re
3. **Ugyanaz a dokumentum**: A vector DB tartalma nem változik

Ez **nem bug, hanem szándékos design**! Az evaluation célja a **reprodukálhatóság** és **összehasonlíthatóság**.

---

## Részletes magyarázat

### 1. Statikus tesztesetek

```python
PROMPT_TEST_CASES = [
    {
        'query': 'Hol kapcsolom be a Walk Away Lock-ot?',
        'context': [...],  # Mindig ugyanaz
        'expected_contains': ['Controls', 'Locks', 'Walk Away Lock']
    },
    # ... további tesztesetek
]
```

**Következmény**: Minden futtatáskor ugyanazokat a query-ket teszteljük.

### 2. Determinisztikus LLM (temperature=0)

**Fájl**: `src/evaluation/prompt_eval.py`

```python
response = self._judge_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[...],
    temperature=0  # ← Determinisztikus!
)
```

**Következmény**: 
- Ugyanaz a query + ugyanaz a context = **mindig ugyanaz a válasz**
- Ez **szándékos**, mert az evaluation **reprodukálható** kell legyen

### 3. Ugyanaz a dokumentum

A vector DB tartalma nem változik futtatások között, ezért:
- Ugyanaz a query → ugyanazok a retrieved chunk-ok
- Ugyanazok a chunk-ok → ugyanaz a context
- Ugyanaz a context → ugyanaz a válasz

---

## Mikor változnak az eredmények?

Az eredmények **csak akkor** változnak, ha:

1. **Új dokumentumot töltesz fel**: Más chunk-ok → más context → más válaszok
2. **Módosítod a teszteseteket**: Más query-k → más válaszok
3. **Módosítod a system promptot**: Más instrukciók → más válaszok
4. **Módosítod a chunking stratégiát**: Más chunk-ok → más context → más válaszok
5. **Módosítod a retrieval/reranking beállításokat**: Más chunk-ok kerülnek elő → más context

---

## Hogyan ellenőrizheted, hogy tényleg újrafut?

### Módszer 1: Időbélyeg

Az UI most már mutatja az utolsó futtatás időpontját:

```
⏱️ Utolsó futtatás: 2026-02-10 15:30:45 (12.3s)
```

Minden gombnyomáskor ez az időbélyeg frissül, ami bizonyítja, hogy újrafut.

### Módszer 2: Cache törlése

Használd a "🗑️ Cache Törlése" gombot:
1. Töröld a cache-t
2. Futtasd újra az evaluationt
3. Az eredmények **ugyanazok** lesznek (mert determinisztikus)

### Módszer 3: Módosítsd a teszteseteket

Ha más query-t adsz meg, más eredményeket kapsz:

```python
# src/evaluation/test_cases.py
PROMPT_TEST_CASES = [
    {
        'query': 'Új kérdés, amit még nem teszteltem',  # ← Új query
        'context': [...],
        'expected_contains': [...]
    }
]
```

---

## Miért jó ez így?

### ✅ Reprodukálhatóság
- Ugyanazok az eredmények → könnyű összehasonlítani verziókat
- "A múlt héten 0.97 volt a context relevance, most is 0.97" → **nincs regresszió**

### ✅ Konzisztencia
- Determinisztikus LLM → nincs random fluktuáció
- Könnyebb debugolni, ha mindig ugyanaz az eredmény

### ✅ Költséghatékonyság
- Nem kell minden alkalommal újra generálni a válaszokat
- Session state cache → gyors UI frissítés

---

## Mit tehetsz, ha változatosságot akarsz?

### Opció 1: Növeld a temperature-t

**Fájl**: `src/evaluation/prompt_eval.py`

```python
response = self._judge_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[...],
    temperature=0.7  # ← Változatosabb válaszok
)
```

**Hátrány**: Az eredmények nem lesznek reprodukálhatóak.

### Opció 2: Adj hozzá új teszteseteket

**Fájl**: `src/evaluation/test_cases.py`

Adj hozzá új query-ket, és az evaluation új eredményeket fog adni ezekre.

### Opció 3: Változtasd meg a dokumentumot

Tölts fel egy másik PDF-et, és az evaluation más chunk-okkal fog dolgozni.

---

## Összefoglalás

| Kérdés | Válasz |
|--------|--------|
| **Újrafut-e az evaluation?** | ✅ Igen, minden gombnyomáskor |
| **Miért ugyanazok az eredmények?** | Determinisztikus LLM (temperature=0) + statikus tesztesetek |
| **Ez bug?** | ❌ Nem, ez szándékos (reprodukálhatóság) |
| **Hogyan ellenőrzöm?** | Időbélyeg az UI-ban |
| **Hogyan változtatom meg?** | Új tesztesetek / új dokumentum / temperature növelése |

**Konklúzió**: Az evaluation **helyesen működik**. Az eredmények azért ugyanazok, mert az evaluation **reprodukálható** és **determinisztikus**, ami egy **jó dolog** production környezetben! 🎯



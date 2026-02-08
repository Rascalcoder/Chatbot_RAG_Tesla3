# 🚀 GYORS INDÍTÁSI ÚTMUTATÓ - RAG CHATBOT

## ⚠️ FONTOS: Chat üres? Ez normális!

A chat akkor jelenik meg, ha **legalább 1 dokumentumot feltöltöttél**.

---

## 📍 LÉPÉSRŐL LÉPÉSRE

### 1️⃣ SIDEBAR MEGNYITÁSA (Ha nem látszik)

**A bal felső sarokban** (a Streamlit logo mellett) van egy **`>`** nyíl:
- Kattints rá → **Sidebar kinyílik**

Ha már látod a bal oldali panelt, ugorj a 2. lépésre!

---

### 2️⃣ DOKUMENTUM FELTÖLTÉS (BAL OLDALI SIDEBAR)

#### Amit látnod kell a bal oldalon:

```
┌─────────────────────────────┐
│  📄 Dokumentum Feltöltés    │
├─────────────────────────────┤
│                             │
│  💬 Chat vezérlés           │
│  [Új chat] [Chat törlése]  │
│                             │
│  ☐ Források megjelenítése   │
│                             │
│  ┌─────────────────────┐   │
│  │  Browse files       │   │  ← IDE KATTINTS!
│  │  Drag and drop      │   │
│  └─────────────────────┘   │
│                             │
│  [Dokumentumok Hozzáadása] │  ← AZTÁN IDE!
│                             │
└─────────────────────────────┘
```

#### Lépések:

1. **"Browse files"** gombra kattints
2. Válassz egy fájlt:
   - ✅ PDF (pl. `model_3.pdf`)
   - ✅ TXT
   - ✅ DOCX
3. **"Dokumentumok Hozzáadása"** gombra kattints (nagy kék gomb)
4. **Várj 10-30 másodpercet** (spinner megjelenik: "Dokumentumok feldolgozása...")

---

### 3️⃣ ELSŐ FELTÖLTÉS - VÁRHATÓ IDŐ

**⚠️ ELSŐ alkalommal LASSÚ lesz (csak egyszer!):**

#### Miért?
- **BGE-M3 modell letöltése**: ~2GB (5-10 perc)
- **Embedding generálás**: CPU-n 10-30 másodperc

#### Mit látsz?
```
🔄 Dokumentumok feldolgozása...
```

**NE ZÁRD BE!** Várj türelemmel.

#### Sikeres feltöltés után:
```
✅ 1 dokumentum sikeresen hozzáadva!
```

---

### 4️⃣ CHAT HASZNÁLAT (FŐOLDAL - KÖZÉP)

**MOST már megjelenik a chat!**

#### Amit látsz:

```
┌─────────────────────────────────────┐
│  💬 Chat                            │
├─────────────────────────────────────┤
│                                     │
│  [Kérdezz valamit a                │  ← IDE ÍRD A KÉRDÉST!
│   dokumentumokról...]              │
│                                     │
└─────────────────────────────────────┘
```

#### Példa kérdések:

```
"Foglalja össze a dokumentumot"
"Miről szól ez a dokumentum?"
"Keress kulcsszavakat: [témád]"
```

---

### 5️⃣ ELSŐ VÁLASZ - VÁRHATÓ IDŐ

**⚠️ Az első válasz ideje a konfigurációtól függ:**

#### HIBRID Konfiguráció (Ajánlott - 8 GB RAM):
- **MiniLM embedding letöltése**: ~90 MB (1-2 perc)
- **Válasz generálás**: OpenAI API, gyors (~1-3 másodperc)
- ✅ **Teljes első válasz**: ~2-3 perc

#### Teljes Lokális Konfiguráció (16+ GB RAM):
- **BGE-M3 + Qwen3-4B letöltése**: ~10 GB (10-20 perc)
- **Válasz generálás**: CPU-n 10-30 másodperc, GPU-n 1-3 másodperc
- ⚠️ **Teljes első válasz**: ~15-25 perc

#### Mit látsz?
```
🤖 (asszisztens válaszol...)
```

**MÁSODIK kérdéstől** már gyorsabb lesz!

---

## ❌ HIBAELHÁRÍTÁS

### Probléma 1: "Sidebar nem látszik"
**Megoldás**: 
- Bal felső sarok → `>` nyílra kattints

### Probléma 2: "Browse files nincs a sidebar-ban"
**Megoldás**:
- Görgess le a sidebar-ban
- Lehet alul van a "Dokumentum Feltöltés" rész

### Probléma 3: "Feltöltés után is üres a chat"
**Megoldás**:
- Frissítsd az oldalt (F5)
- Ellenőrizd a sidebar alján: "Dokumentumok (vector DB): 1" látható?

### Probléma 4: "Spinning marad, nem töltődik fel"
**Megoldás**:
- Nyomd meg F12 → Console
- Küld el a hibaüzenetet
- VAGY: Nézd a terminált (ahol fut a streamlit)

### Probléma 5: "Chat input nem jelenik meg feltöltés után"
**Megoldás**:
```python
# Ellenőrizd a sidebar alján:
Dokumentumok (vector DB): 0  ← ROSSZ (nincs feltöltve)
Dokumentumok (vector DB): 1  ← JÓ (feltöltve van)
```

Ha "0"-t látsz, akkor nem sikerült a feltöltés!

---

## 🎯 GYORS TESZT DOKUMENTUM

Ha nincs saját fájlod, készíts egy egyszerű TXT fájlt:

**test_doc.txt**:
```
Ez egy teszt dokumentum.
A RAG chatbot ezt a szöveget fogja használni.
Teszteld a következő kérdéssel: "Miről szól ez a dokumentum?"
```

Mentsd el és töltsd fel!

---

## 📊 STÁTUSZ ELLENŐRZÉS

### Bal sidebar alján látnod kell:

```
ℹ️ Információk
───────────────────
Dokumentumok (vector DB)
         1              ← Feltöltött dokumentumok száma

Session: session_abc123  ← Session azonosító
```

**Ha "0"-t látsz**: Nincs feltöltve dokumentum → Nincs chat!
**Ha "1"-t vagy többet**: Van dokumentum → Chat működik!

---

## ✅ SIKERES HASZNÁLAT CHECKLIST

- [ ] Sidebar látható (bal oldalon)
- [ ] "Browse files" gomb látható
- [ ] Fájl kiválasztva
- [ ] "Dokumentumok Hozzáadása" gombra kattintottam
- [ ] Megvártam a feldolgozást (spinner eltűnt)
- [ ] "✅ sikeres hozzáadva" üzenet megjelent
- [ ] Sidebar alján: "Dokumentumok: 1" látszik
- [ ] Chat input mező megjelent a középen
- [ ] Kérdést írtam be
- [ ] Válasz generálódik

---

## 🆘 SEGÍTSÉG

Ha még mindig nem működik:

1. **F12 megnyitása** (Developer Tools)
2. **Console tab**
3. **Piros hibák** másolása
4. **Terminál** ellenőrzése (ahol a streamlit fut)
5. Küldd el a hibaüzeneteket!

---

## 🎉 SIKERES HASZNÁLAT

Ha minden működik, ezt fogod látni:

```
┌─ SIDEBAR ─────┐  ┌─ FŐOLDAL ──────────────────┐
│               │  │  💬 Chat                   │
│ 📄 Dokumentum │  │                            │
│               │  │  👤 Miről szól a dok?     │
│ [Browse...]   │  │                            │
│               │  │  🤖 Ez a dokumentum...    │
│ [Hozzáadás]   │  │     [streaming válasz]    │
│               │  │                            │
│ Dokumentumok  │  │  ▼ Források / Kontextus   │
│      1        │  │     [1] test_doc.txt      │
│               │  │                            │
└───────────────┘  └────────────────────────────┘
```

**Gratulálok! A RAG chatbot működik!** 🚀

---

**Készítette**: AI Asszisztens  
**URL**: http://localhost:8501  
**Port**: 8501


# Tesla Model 3 Kézikönyv Használata

Ez a dokumentum bemutatja, hogyan használhatod a RAG rendszert a Tesla Model 3 Owner's Manual PDF-jével.

## Előfeltételek

1. A `model_3.pdf` fájlnak a projekt gyökerében kell lennie
2. A RAG rendszer telepítve és konfigurálva legyen

## Használati Módok

### 1. Streamlit Webes Felület

**Lépések:**
1. Indítsd el az app-ot:
   ```bash
   streamlit run app.py
   ```

2. A böngészőben megnyílik a felület

3. A bal oldali sidebar-ban:
   - Kattints a "Válassz dokumentumokat" gombra
   - Válaszd ki a `model_3.pdf` fájlt
   - Kattints a "Dokumentumok Hozzáadása" gombra

4. Várj, amíg a dokumentum feldolgozásra kerül (pár másodperc)

5. Most már kérdezhetsz a Model 3-ról a chat mezőben!

**Példa kérdések:**
- "Hogyan lehet bekapcsolni a Model 3-at?"
- "Mik a főbb funkciók a touchscreen-en?"
- "Hogyan működik a töltés?"
- "Mi az Autopilot és hogyan működik?"
- "Milyen karbantartást igényel a Model 3?"

### 2. Teszt Script (Interaktív)

**Futtatás:**
```bash
python test_model3_manual.py
```

Ez a script:
- Automatikusan betölti a `model_3.pdf` fájlt
- Futtat néhány előre definiált teszt kérdést
- Ezután interaktív módba lép, ahol saját kérdéseket tehetsz fel

**Használat:**
- Írd be a kérdésedet és nyomj Enter-t
- Írj `kilépés` vagy `exit` a kilépéshez

### 3. Előre Betöltés (Ajánlott)

Ha gyakran használod a Model 3 kézikönyvet, érdemes előre betölteni:

```bash
python load_model3_manual.py
```

Ez betölti a dokumentumot a vektor adatbázisba, így:
- A Streamlit app indításakor már elérhető lesz
- Nem kell minden alkalommal feltölteni
- Gyorsabb válaszidő

## Példa Kérdések és Válaszok

### Kérdés: "Hogyan lehet bekapcsolni a Model 3-at?"

A rendszer a kézikönyv alapján válaszol, pl.:
- Kulcsok használata (key card, smartphone)
- Power on/off folyamat
- Stb.

### Kérdés: "Mik a biztonsági funkciók?"

A rendszer felsorolja:
- Airbag rendszer
- Ülés övek
- Gyermekbiztonsági ülések
- Ütközéselkerülő asszisztens
- Stb.

### Kérdés: "Hogyan működik a töltés?"

A rendszer elmagyarázza:
- Töltési utasítások
- Töltőállomások
- Akkumulátor információk
- Stb.

## Tippek

1. **Konkrét kérdések**: A pontosabb kérdések jobb válaszokat adnak
   - ❌ "Mi a Model 3?"
   - ✅ "Mik a főbb funkciók a Model 3 touchscreen-en?"

2. **Részletes válaszok**: Ha részletesebb információt szeretnél, kérdezz rá specifikusabban
   - ❌ "Töltés"
   - ✅ "Hogyan kell töltőállomáson tölteni a Model 3-at?"

3. **Többszöri kérdezés**: Ha nem kapsz megfelelő választ, próbáld meg másképp megfogalmazni a kérdést

## Hibaelhárítás

### "A PDF fájl nem található"
- Ellenőrizd, hogy a `model_3.pdf` a projekt gyökerében van-e
- A fájlnév pontosan `model_3.pdf` legyen (kis-nagybetű érzékeny)

### Lassú válaszidő
- Első futtatáskor a modellek letöltődnek (~10 GB)
- GPU használata jelentősen felgyorsítja a válaszidőt
- A dokumentum betöltése után a válaszok gyorsabbak lesznek

### Rossz válaszok
- Próbáld meg pontosabban megfogalmazni a kérdést
- Használj konkrét kifejezéseket a kézikönyvből
- Nézd meg a "Használt kontextus" részt, hogy lássad, milyen információt használt a rendszer

## További Információk

A Model 3 kézikönyv tartalmazza:
- Áttekintés (interior, exterior, touchscreen)
- Nyitás/zárás (kulcsok, ajtók, ablakok)
- Ülés és biztonsági övek
- Vezetés (kormány, tükrök, fények, stb.)
- Driver Assistance (Autopilot, stb.)
- Touchscreen használata
- Töltés
- Karbantartás
- Specifikációk

Minden ezekről kérdezhetsz a RAG rendszerben!


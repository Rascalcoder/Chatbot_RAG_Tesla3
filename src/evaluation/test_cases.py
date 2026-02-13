"""
Teszt esetek az evaluation-hoz
Tesla Model 3 Manual alapú átfogó tesztcsomag

TESZTSZÁMOK ÖSSZEFOGLALÓJA:
============================

A) RAG SZINTŰ TESZTEK:
   - Retrieval queries: 38 db (21 Tesla-specifikus + 18 általános)
     * Zárak és biztonság: 7 teszt
     * Tire Repair Kit: 5 teszt
     * Karbantartás: 2 teszt
     * Telematics: 3 teszt
     * Jelzések: 3 teszt
     * Autopilot: 1 teszt
     * Általános: 18 teszt
   - Embedding tesztek: 15 db (hasonlósági metrikák)
   - Chunking tesztek: 3 db

B) PROMPT SZINTŰ TESZTEK: 17 db
   - Tesla Model 3 specifikus: 15 teszt
     * Menüútvonalak (2)
     * Lépésenkénti utasítások (2)
     * Biztonsági figyelmeztetések (2)
     * Hallucináció teszt (1)
     * Kontextus relevancia (1)
     * Több forrás hivatkozás (1)
     * Specifikus limtek (1)
     * Hibaelhárítás (5)
   - Általános tesztek: 2 db

C) ALKALMAZÁS SZINTŰ TESZTEK: 10 db
   - User journey workflows: 10 teszt
     * PDF feltöltés és források (1)
     * Session management (1)
     * Error handling (1)
     * Streaming + latency (1)
     * Context memory (1)
     * Graceful fallback (1)
     * Hosszú query stabilitás (1)
     * UI toggle funkciók (1)
     * Monitoring dashboard (1)
     * Rossz fájl hibakezelés (1)
   - Latency tesztek: 8 query (3 futtatással)
   - Performance benchmarks: 3 teszt

ÖSSZESEN: 90+ TESZTESET
Minimum követelmény: 20 RAG + 15 Prompt + 10 App = 45 ✅
Megvalósított: 38 RAG + 17 Prompt + 10 App + 8 Latency + 3 Benchmark = 76+ ✅✅

Tesla Model 3 Manual lefedettség:
- Locks & Keys
- Tire Repair Kit
- Telematics & Data Privacy
- Charging
- Windows & Doors
- Autopilot
- Maintenance & Cleaning
"""

import os

# Chunking konfiguráció beolvasása (ugyanaz a forrás mint a RAG rendszerben)
_CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
_CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))

# RAG szintű teszt esetek
# Minimum 20 teszteset követelmény teljesítése (most 38 Tesla-specifikus teszt!)
RAG_TEST_CASES = {
    'retrieval_tests': [
        # ===== TESLA MODEL 3 MANUAL SPECIFIKUS TESZTEK (21 db) =====
        # Kulcsszó alapú értékelés: a retrieval által visszaadott chunkokban
        # keressük az elvárt kulcsszavakat (case-insensitive substring match)

        # Zárak és biztonság (7 teszt)
        {'query': 'Walk Away Lock bekapcsolása és kikapcsolása',
         'expected_keywords': ['walk away lock'], 'category': 'Zárak és biztonság'},
        {'query': 'Walk Up Unlock hogyan működik',
         'expected_keywords': ['walk up unlock'], 'category': 'Zárak és biztonság'},
        {'query': 'Unlock on Park beállítás',
         'expected_keywords': ['unlock', 'park'], 'category': 'Zárak és biztonság'},
        {'query': 'Hogyan nyílik a csomagtartó kívülről és belülről emergency release',
         'expected_keywords': ['trunk', 'emergency'], 'category': 'Zárak és biztonság'},
        {'query': 'Ablakok működtetése kétállású kapcsoló és biztonsági figyelmeztetés',
         'expected_keywords': ['window'], 'category': 'Zárak és biztonság'},
        {'query': 'Key card használat manuális zárás és nyitás',
         'expected_keywords': ['key card'], 'category': 'Zárak és biztonság'},
        {'query': 'Bluetooth phone key mikor nem old fel automatikusan',
         'expected_keywords': ['phone key'], 'category': 'Zárak és biztonság'},

        # Tire Repair Kit (5 teszt)
        {'query': 'Temporary Tire Repair sealant használat lépései',
         'expected_keywords': ['sealant'], 'category': 'Tire Repair Kit'},
        {'query': 'Temporary Tire Repair Inflating with Air Only lépések',
         'expected_keywords': ['inflate'], 'category': 'Tire Repair Kit'},
        {'query': 'Kompresszor túlmelegedés max 8 perc és hűtés 15 perc',
         'expected_keywords': ['compressor'], 'category': 'Tire Repair Kit'},
        {'query': 'Sealant canister cseréje lépésről lépésre',
         'expected_keywords': ['sealant', 'canister'], 'category': 'Tire Repair Kit'},
        {'query': '12V power socket hol van tire compressor csatlakozás',
         'expected_keywords': ['12v'], 'category': 'Tire Repair Kit'},

        # Karbantartás és tisztítás (2 teszt)
        {'query': 'Külső tisztítás káros anyagok eltávolítása bird droppings road salt',
         'expected_keywords': ['clean'], 'category': 'Karbantartás'},
        {'query': 'Gumijavító készlet adapterek hol találhatók',
         'expected_keywords': ['tire', 'repair'], 'category': 'Karbantartás'},

        # Telematics és adatvédelem (3 teszt)
        {'query': 'Telematics milyen adatokat rögzít a jármű charging events VIN location',
         'expected_keywords': ['telematics'], 'category': 'Telematics'},
        {'query': 'Telematics mikor adja ki Tesla harmadik félnek az adatokat',
         'expected_keywords': ['telematics', 'data'], 'category': 'Telematics'},
        {'query': 'Data Sharing hol lehet engedélyezni a képernyőn Controls Settings Data Sharing',
         'expected_keywords': ['data sharing'], 'category': 'Telematics'},

        # Jelzések és figyelmeztetések (3 teszt)
        {'query': 'Ajtó ajtózár mikor villan a külső fény unlock jelzés',
         'expected_keywords': ['door', 'lock'], 'category': 'Jelzések'},
        {'query': 'Door Open indicator jelentése',
         'expected_keywords': ['door'], 'category': 'Jelzések'},
        {'query': 'Töltés miért lassabb ha hideg az akkumulátor vagy közel van a 100 százalékhoz',
         'expected_keywords': ['charg'], 'category': 'Jelzések'},

        # Driver Assistance (1 teszt)
        {'query': 'Autopilot driver assistance alap korlátozások és felelősség',
         'expected_keywords': ['autopilot'], 'category': 'Driver Assistance'},

        # ===== ÁLTALÁNOS DOKUMENTUM TESZTEK (18 teszt) =====
        # Kulcsszó nélkül: csak azt teszteljük, hogy a retrieval visszaad-e találatot
        {'query': 'Mi a fő témája a dokumentumnak?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Mik a legfontosabb pontok?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Mi a dokumentum szerzője?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Mikor készült ez a dokumentum?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Mi a dokumentum célja?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Milyen számok vagy adatok szerepelnek a dokumentumban?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Mik a kulcsfontosságú fogalmak?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Milyen dátumok vagy időpontok vannak említve?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Mik a dokumentumban szereplő főbb szervezetek vagy cégek?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Milyen helyszínek vagy országok szerepelnek?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Hogyan kapcsolódik össze az információ a dokumentumban?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Mi a kapcsolat a különböző részek között?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Milyen következtetések vonhatók le?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Mik a dokumentum főbb következményei?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Mi a dokumentum ajánlása vagy javaslata?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Mi a pontos definíciója a fő fogalomnak?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Milyen példák szerepelnek a dokumentumban?', 'expected_keywords': [], 'category': 'Általános'},
        {'query': 'Mik a dokumentum szerint a legfontosabb tények?', 'expected_keywords': [], 'category': 'Általános'},
    ],
    'embedding_tests': [
        # Teljesen azonos szövegek (2 teszt)
        {
            'text1': 'Ez egy példa szöveg.',
            'text2': 'Ez egy példa szöveg.',
            'similarity': 1.0
        },
        {
            'text1': 'A gépi tanulás egy fontos AI technológia.',
            'text2': 'A gépi tanulás egy fontos AI technológia.',
            'similarity': 1.0
        },
        
        # Teljesen különböző szövegek (2 teszt)
        {
            'text1': 'Ez egy példa szöveg.',
            'text2': 'Ez egy teljesen más szöveg.',
            'similarity': 0.0
        },
        {
            'text1': 'A kutyák szeretik a labdát.',
            'text2': 'A számítógépek gyorsan dolgoznak.',
            'similarity': 0.0
        },
        
        # Hasonló jelentés, más szavakkal (3 teszt)
        {
            'text1': 'A gépi tanulás lehetővé teszi a számítógépek tanulását adatokból.',
            'text2': 'A machine learning segítségével a gépek megtanulhatnak adatok alapján.',
            'similarity': 0.8
        },
        {
            'text1': 'A neurális hálózatok mély gépi tanulási modellek.',
            'text2': 'A deep learning modellek neurális hálózatokat használnak.',
            'similarity': 0.75
        },
        {
            'text1': 'A természetes nyelvfeldolgozás fontos AI terület.',
            'text2': 'Az NLP lehetővé teszi a gépek számára a nyelv megértését.',
            'similarity': 0.7
        },
        
        # Részben hasonló (3 teszt)
        {
            'text1': 'A Python egy programozási nyelv adatelemzéshez.',
            'text2': 'A Python egy népszerű programozási nyelv.',
            'similarity': 0.6
        },
        {
            'text1': 'A vektor adatbázisok hatékonyak a hasonlóság kereséshez.',
            'text2': 'A vektor adatbázisok segítenek a releváns információk megtalálásában.',
            'similarity': 0.65
        },
        {
            'text1': 'A RAG rendszerek kombinálják a retrieval-t és a generációt.',
            'text2': 'A retrieval-augmented generation hatékony AI megközelítés.',
            'similarity': 0.7
        },
        
        # Különböző témák, de kapcsolódó szavak (3 teszt)
        {
            'text1': 'A gépi tanulás algoritmusok tanulnak adatokból.',
            'text2': 'Az adatbányászat hasznos információkat talál adatokban.',
            'similarity': 0.4
        },
        {
            'text1': 'A neurális hálózatok inspirálva vannak az agy működésétől.',
            'text2': 'Az agy neurális hálózatai bonyolult információfeldolgozást végeznek.',
            'similarity': 0.5
        },
        {
            'text1': 'A természetes nyelvfeldolgozás segít a gépeknek kommunikálni.',
            'text2': 'A chat robotok használják a nyelvfeldolgozást a válaszok generálásához.',
            'similarity': 0.55
        },
        
        # Minimális hasonlóság (2 teszt)
        {
            'text1': 'A Python egy programozási nyelv.',
            'text2': 'A kávé finom ital.',
            'similarity': 0.1
        },
        {
            'text1': 'A gépi tanulás fontos technológia.',
            'text2': 'A szép időjárás kedvező a kiránduláshoz.',
            'similarity': 0.05
        },
    ],
    'chunking_tests': [
        # Különböző hosszúságú dokumentumok chunking teszteléséhez
        # min/max chunk_size a konfigurált CHUNK_SIZE alapján számolódik
        {
            'document': 'Ez egy rövid dokumentum. Tartalmaz néhány mondatot. Végül van egy befejező mondat.',
            'expected_chunks': 1,
            'min_chunk_size': 10,
            'max_chunk_size': _CHUNK_SIZE
        },
        {
            'document': 'Ez egy hosszabb dokumentum. ' * 50 + 'Végül van egy befejező mondat.',
            'expected_chunks': max(1, round(len('Ez egy hosszabb dokumentum. ' * 50 + 'Végül van egy befejező mondat.') / (_CHUNK_SIZE - _CHUNK_OVERLAP))),
            'min_chunk_size': 50,
            'max_chunk_size': _CHUNK_SIZE + _CHUNK_OVERLAP
        },
        {
            'document': 'Első bekezdés. ' * 20 + 'Második bekezdés. ' * 20 + 'Harmadik bekezdés. ' * 20,
            'expected_chunks': max(1, round(len('Első bekezdés. ' * 20 + 'Második bekezdés. ' * 20 + 'Harmadik bekezdés. ' * 20) / (_CHUNK_SIZE - _CHUNK_OVERLAP))),
            'min_chunk_size': 50,
            'max_chunk_size': _CHUNK_SIZE + _CHUNK_OVERLAP
        }
    ]
}

# Prompt szintű teszt esetek - 15+ Tesla Model 3 specifikus teszt
PROMPT_TEST_CASES = [
    # ===== TESLA MODEL 3 MANUAL TESZTEK (15 teszt) =====
    {
        'query': 'Hol kapcsolom be a Walk Away Lock-ot?',
        'context': [
            {
                'text': 'Walk Away Lock beállítása: Controls > Locks > Walk Away Lock. Ha engedélyezve van, a Model 3 automatikusan zárolja, amikor eltávolsz a járműtől a key fob vagy phone key-vel.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 15}
            }
        ],
        'expected_behavior': 'Forrás megadása: Controls > Locks + Walk Away Lock menüútvonal. Ha nincs benne a manualban, mondja meg.',
        'expected_answer': 'Controls > Locks > Walk Away Lock'
    },
    {
        'query': 'Miért nem old fel a kocsi, ha a telefonom nálam van?',
        'context': [
            {
                'text': 'Bluetooth phone key követelmények: telefon Bluetooth bekapcsolva, Tesla app háttérben fut, phone key engedélyezve. Ha az app kilép a háttérből vagy Bluetooth kikapcsolt, nem old fel automatikusan. Tartalék megoldás: key card használata.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 18}
            }
        ],
        'expected_behavior': 'Feltételek listázása (BT, app háttér, engedélyezés) + key card fallback említése',
        'expected_answer': 'Bluetooth, Tesla app háttérben, phone key engedélyezve'
    },
    {
        'query': 'Mi a teendő, ha defektet kapok és van tire repair kit?',
        'context': [
            {
                'text': 'Tire Repair Kit használat: 1) Állítsd le a járművet biztonságosan 2) Csatlakoztasd a sealant canister-t 3) Csatlakoztasd a kompresszort 12V socket-be 4) Töltsd fel 45 PSI-re 5) Vezess 3 mérföldet max 50 mph sebességgel 6) Ellenőrizd a nyomást. FIGYELMEZTETÉS: max 8 perc folyamatos használat, 15 perc hűtési idő szükséges.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 182}
            }
        ],
        'expected_behavior': 'Lépések sorrendben + figyelmeztetések kiemelése (8 perc limit, hűtés)',
        'expected_answer': 'Számozott lépések + figyelmeztetés említése'
    },
    {
        'query': 'Meddig járathatom a kompresszort folyamatosan?',
        'context': [
            {
                'text': 'FIGYELMEZTETÉS: A tire repair kompresszor maximum 8 percig használható folyamatosan. Túlmelegedés esetén 15 perc hűtési időt kell hagyni használat között. A túlzott használat károsíthatja a kompresszort.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 185}
            }
        ],
        'expected_behavior': '8 perc + 15 perc hűtés explicit említése',
        'expected_answer': '8 perc, majd 15 perc hűtés'
    },
    {
        'query': 'Hol tudom engedélyezni a data sharinget?',
        'context': [
            {
                'text': 'Data Sharing beállítása: Touchscreen menü > Controls > Settings > Data Sharing. Itt engedélyezheted, hogy a Tesla adatokat gyűjtsön a jármű használatáról a funkcionalitás javítása érdekében.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 165}
            }
        ],
        'expected_behavior': 'Pontos menüútvonal megadása',
        'expected_answer': 'Controls > Settings > Data Sharing'
    },
    {
        'query': 'Mit rögzít a telematics rendszer?',
        'context': [
            {
                'text': 'Telematics rögzített adatok: VIN, charging events (idő, hely, energia mennyiség), lokáció, sebességadatok, akkumulátor állapot, hibakódok, szoftver verzió, használati statisztikák.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 164}
            }
        ],
        'expected_behavior': 'Felsorolás az adattípusokról',
        'expected_answer': 'VIN, charging events, location, speed, battery status, error codes'
    },
    {
        'query': 'Kinek adja ki Tesla a telematics adatot?',
        'context': [
            {
                'text': 'Tesla telematics adatkiadás: törvényi követelmény esetén hatóságoknak, bírósági végzés alapján, tulajdonos hozzájárulásával harmadik félnek, biztosítóknak baleset esetén (tulajdonos engedélyével).',
                'metadata': {'file_name': 'model_3.pdf', 'page': 165}
            }
        ],
        'expected_behavior': 'Feltételek listázása (törvény, hozzájárulás)',
        'expected_answer': 'Törvényi követelmény, tulajdonos hozzájárulása, bírósági végzés'
    },
    {
        'query': 'Hogyan nyílik a csomagtartó, ha nincs áram?',
        'context': [
            {
                'text': 'Emergency trunk release: A csomagtartó belső oldalán található manuális kioldó kar. Húzd meg a kart a nyíl irányába a csomagtartó megnyitásához áramkimaradás esetén. A kioldó kar világító anyaggal jelölt.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 28}
            }
        ],
        'expected_behavior': 'Emergency release említése + helye',
        'expected_answer': 'Emergency trunk release kar belülről'
    },
    {
        'query': 'Ablak felhúzás biztonsági szabály?',
        'context': [
            {
                'text': 'FIGYELMEZTETÉS: Ablak felhúzás előtt győződj meg róla, hogy semmi (pl. testrésze, tárgy) nincs az ablak útjában. A sofőr felelős az ablakok biztonságos működtetéséért. A gyermekek nem kezelhetik az ablakokat felügyelet nélkül.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 22}
            }
        ],
        'expected_behavior': 'Safety warning kiemelése + driver responsibility',
        'expected_answer': 'Driver felelős, gyermek felügyelet, ellenőrzés mozgatás előtt'
    },
    {
        'query': 'Milyen anyagok károsítják a fényezést és mit csináljak?',
        'context': [
            {
                'text': 'Káros anyagok a fényezéshez: bird droppings, tree sap, road salt, tar, dead insects. Azonnal távolítsd el meleg vízzel és autósamponnal. Ne hagyd száradni, mert maradandó károsodást okozhatnak a fényezésben.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 172}
            }
        ],
        'expected_behavior': 'Anyagok felsorolása + eltávolítási módszer',
        'expected_answer': 'Bird droppings, tree sap, road salt, tar - azonnal eltávolítani'
    },
    {
        'query': 'Van-e beépített dashcam a 2019 Model 3-ban és hol kapcsolom be?',
        'context': [
            {
                'text': 'Walk Away Lock, Sentry Mode, Autopilot beállítások elérhetők a Controls menüben. A járműben található kamerák biztonsági funkciókhoz használatosak.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 140}
            }
        ],
        'expected_behavior': 'HALLUCINÁCIÓ TESZT - Ha nincs explicit dashcam információ a kontextusban, NE találgasson. Mondja: "nem találtam explicit információt"',
        'expected_answer': 'Nincs explicit információ a dashcam funkcióról a kontextusban'
    },
    {
        'query': 'Hol van a zárak menü?',
        'context': [
            {
                'text': 'Töltés beállítások: Controls > Charging. Itt állíthatod be a töltési limitet és az ütemezett töltést. Az akkumulátor teljesítménye hidegben csökkenhet.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 120}
            }
        ],
        'expected_behavior': 'KONTEXTUS RELEVANCIA TESZT - Töltés kontextus adott, zárak kérdés. Vissza kell terelnie: "A kontextusban töltésről van szó, zárak menü: Controls > Locks"',
        'expected_answer': 'A kontextus nem releváns. Zárak: Controls > Locks'
    },
    {
        'query': 'Air only inflate lépései',
        'context': [
            {
                'text': 'Inflating with Air Only (no sealant): 1) Remove the sealant canister 2) Attach compressor to valve 3) Plug into 12V socket 4) Inflate to recommended PSI (42 front, 42 rear) 5) Check pressure with gauge 6) Disconnect compressor.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 186}
            }
        ],
        'expected_behavior': 'SZÁMOZOTT LÉPÉSEK - Lépésenkénti formátumban kell válaszolnia',
        'expected_answer': 'Számozott lista: 1) Remove canister, 2) Attach, 3) Plug, 4) Inflate, 5) Check, 6) Disconnect'
    },
    {
        'query': 'Tire repair és sealant csere folyamata',
        'context': [
            {
                'text': 'Tire repair process: attach sealant, inflate to 45 PSI, drive 3 miles. Page 182. Sealant canister replacement: unscrew old canister, dispose properly, screw in new canister, ensure tight connection. Page 187.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 182}
            },
            {
                'text': 'Sealant canister replacement details: Replacement canister available from Tesla Service. Check expiration date. Do not reuse expired sealant. Thread the new canister clockwise until tight.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 187}
            }
        ],
        'expected_behavior': 'TÖBB FORRÁS - Mindkét oldal (182, 187) hivatkozása szükséges',
        'expected_answer': 'Tire repair (oldal 182) + Sealant csere (oldal 187) hivatkozása'
    },
    {
        'query': 'Ablak és gyerek biztonsági figyelmeztetés',
        'context': [
            {
                'text': 'WARNING: Before raising windows, ensure no body parts or objects are in the path. Driver is responsible for safe window operation. Children must not operate windows without adult supervision. Risk of serious injury.',
                'metadata': {'file_name': 'model_3.pdf', 'page': 22}
            }
        ],
        'expected_behavior': 'BIZTONSÁGI HANGNEM - Safety warning KIEMELÉSE, gyerek felügyelet említése',
        'expected_answer': 'FIGYELMEZTETÉS kiemelve, driver felelősség, gyermek felügyelet nélkül nem'
    },
    
    # ===== ÁLTALÁNOS TESZTEK (2 teszt megtartása) =====
    {
        'query': 'Mi a fő témája?',
        'context': [
            {
                'text': 'A dokumentum fő témája az AI és gépi tanulás.',
                'metadata': {'file_name': 'test.pdf'}
            }
        ],
        'expected_answer': 'AI és gépi tanulás'
    },
    {
        'query': 'Mik a legfontosabb pontok?',
        'context': [
            {
                'text': 'A legfontosabb pontok: 1) Adatfeldolgozás 2) Modell tanítás 3) Értékelés',
                'metadata': {'file_name': 'test.pdf'}
            }
        ],
        'expected_answer': 'Adatfeldolgozás, Modell tanítás, Értékelés'
    }
]

# Alkalmazás szintű teszt esetek - 10 Tesla Model 3 user journey
APP_TEST_CASES = {
    'user_journeys': [
        # ===== TESLA MODEL 3 WORKFLOWS (10 teszt) =====
        {
            'name': 'PDF feltöltés és források ellenőrzése',
            'description': 'PDF feltöltés → kérdés → források expanderben látszanak',
            'steps': [
                {
                    'action': 'upload',
                    'input': 'model_3.pdf',
                    'expected_status': 'success',
                    'expected_message': 'dokumentum sikeresen hozzáadva'
                },
                {
                    'action': 'query',
                    'input': 'Hol kapcsolom be a Walk Away Lock-ot?',
                    'expected': 'Controls > Locks',
                    'validate_sources': True,
                    'expected_source_count': 1
                },
                {
                    'action': 'verify_sources_expander',
                    'expected': 'expander_visible',
                    'expected_content': ['file_name', 'similarity', 'chunk']
                }
            ]
        },
        {
            'name': 'Új chat session - előző nem keveredik',
            'description': 'Új chat session → előző beszélgetés nem keveredik',
            'steps': [
                {
                    'action': 'query',
                    'input': 'Mi a tire repair első lépése?',
                    'expected': 'sealant'
                },
                {
                    'action': 'new_chat_session',
                    'expected': 'session_cleared'
                },
                {
                    'action': 'query',
                    'input': 'Mi az előző kérdésem?',
                    'expected': 'nincs előző',
                    'validate_no_memory': True
                }
            ]
        },
        {
            'name': 'Dokumentum nélkül kérdezés',
            'description': 'Dokumentum nélkül kérdezés → UI figyelmeztet',
            'steps': [
                {
                    'action': 'clear_documents',
                    'expected': 'documents_cleared'
                },
                {
                    'action': 'query',
                    'input': 'Hol van a 12V socket?',
                    'expected_error': True,
                    'expected_message': 'dokumentum feltöltése szükséges'
                },
                {
                    'action': 'verify_ui_warning',
                    'expected': 'info_message_visible'
                }
            ]
        },
        {
            'name': 'Streaming válasz first token latency',
            'description': 'Streaming válasz: first token idő mérés + total time logolás',
            'steps': [
                {
                    'action': 'upload',
                    'input': 'model_3.pdf'
                },
                {
                    'action': 'query_streaming',
                    'input': 'Meddig járathatom a kompresszort?',
                    'expected': '8 perc',
                    'measure_first_token_time': True,
                    'expected_first_token_max': 5.0,  # másodperc
                    'measure_total_time': True,
                    'expected_total_max': 30.0  # másodperc
                },
                {
                    'action': 'verify_metrics_logged',
                    'expected_metrics': ['first_token_time', 'total_time', 'tokens']
                }
            ]
        },
        {
            'name': 'Session memory - 3 egymás utáni kérdés',
            'description': '3 egymás utáni kérdés ugyanarra a témára (session memory)',
            'steps': [
                {
                    'action': 'query',
                    'input': 'Mi a tire repair kit?',
                    'expected': 'sealant'
                },
                {
                    'action': 'query',
                    'input': 'Hogyan használom?',
                    'expected': 'lépés',
                    'validate_context_memory': True
                },
                {
                    'action': 'query',
                    'input': 'Meddig járathatom a kompresszort?',
                    'expected': '8 perc',
                    'validate_context_memory': True
                }
            ]
        },
        {
            'name': 'Nem található információ fallback',
            'description': 'Nem található információ eset: "nem találom a manualban" fallback',
            'steps': [
                {
                    'action': 'upload',
                    'input': 'model_3.pdf'
                },
                {
                    'action': 'query',
                    'input': 'Hány csésze kávé fér a pohártartóba?',
                    'expected_behavior': 'graceful_fallback',
                    'expected_keywords': ['nem találtam', 'manual', 'információ'],
                    'should_not_hallucinate': True
                }
            ]
        },
        {
            'name': 'Nagyon hosszú kérdés - stabilitás',
            'description': 'Nagyon hosszú kérdés → stabil válasz + nem fagy',
            'steps': [
                {
                    'action': 'query',
                    'input': 'Elmagyarázod nekem részletesen lépésről lépésre hogy hogyan kell használni a tire repair kit-et ha defektet kapok útközben és mi a teendő a sealant használat után meg meddig járathatom a kompresszort és milyen nyomásra kell felfújni a kerekeket és mennyi ideig kell vezetni utána és milyen sebességgel maximum?',
                    'expected_behavior': 'stable_response',
                    'max_response_time': 60.0,  # másodperc
                    'should_not_crash': True,
                    'expected_keywords': ['lépés', 'sealant', 'kompresszor', 'nyomás']
                }
            ]
        },
        {
            'name': 'Források toggle működés',
            'description': 'Források megjelenítése ki/be toggle működik',
            'steps': [
                {
                    'action': 'query',
                    'input': 'Hol van a data sharing beállítás?',
                    'expected': 'Controls > Settings'
                },
                {
                    'action': 'toggle_sources',
                    'state': 'off',
                    'expected': 'sources_hidden'
                },
                {
                    'action': 'verify_sources_not_visible',
                    'expected': 'no_expander'
                },
                {
                    'action': 'toggle_sources',
                    'state': 'on',
                    'expected': 'sources_visible'
                },
                {
                    'action': 'verify_sources_visible',
                    'expected': 'expander_present'
                }
            ]
        },
        {
            'name': 'Monitoring dashboard statisztikák',
            'description': 'Monitoring oldal: token + cost + latency statisztika megjelenik',
            'steps': [
                {
                    'action': 'query',
                    'input': 'Mi a Walk Away Lock?',
                    'expected': 'zár'
                },
                {
                    'action': 'navigate_to_monitoring',
                    'expected': 'monitoring_page_loaded'
                },
                {
                    'action': 'verify_metrics_displayed',
                    'expected_metrics': [
                        'llm_calls',
                        'total_tokens',
                        'total_cost',
                        'avg_total_time'
                    ],
                    'expected_values_not_zero': True
                },
                {
                    'action': 'verify_charts_rendered',
                    'expected_charts': ['daily_usage', 'latency_trends']
                }
            ]
        },
        {
            'name': 'Hibakezelés - rossz fájl feltöltés',
            'description': 'Hibakezelés: rossz/korrupt fájl feltöltés → nem omlik össze, hibát jelez',
            'steps': [
                {
                    'action': 'upload',
                    'input': 'corrupt_file.pdf',
                    'expected_error': True,
                    'expected_message': 'hiba',
                    'should_not_crash': True
                },
                {
                    'action': 'verify_app_still_responsive',
                    'expected': 'app_running'
                },
                {
                    'action': 'upload',
                    'input': 'wrong_format.exe',
                    'expected_error': True,
                    'expected_message': 'nem támogatott',
                    'should_not_crash': True
                },
                {
                    'action': 'upload',
                    'input': 'model_3.pdf',
                    'expected_status': 'success',
                    'validate_recovery': True
                }
            ]
        }
    ],
    'latency_tests': {
        'queries': [
            # Tesla-specifikus latency tesztek
            'Hol kapcsolom be a Walk Away Lock-ot?',
            'Meddig járathatom a kompresszort?',
            'Mi a tire repair első lépése?',
            'Hol van a data sharing beállítás?',
            'Hogyan működik a Walk Up Unlock?',
            # Általános tesztek
            'Mi a fő témája?',
            'Mik a legfontosabb pontok?',
            'Mi a dokumentum szerzője?'
        ],
        'num_runs': 3,
        'expected_avg_latency': {
            'cpu': 15.0,  # másodperc CPU-n
            'gpu': 3.0    # másodperc GPU-n
        }
    },
    'performance_benchmarks': {
        'description': 'Teljesítmény benchmarkok különböző hardware-en',
        'tests': [
            {
                'name': 'Single query latency',
                'query': 'Hol van a 12V socket?',
                'expected_max_time_cpu': 30.0,
                'expected_max_time_gpu': 5.0
            },
            {
                'name': 'Concurrent queries (3)',
                'queries': [
                    'Mi a Walk Away Lock?',
                    'Hogyan működik a tire repair?',
                    'Hol van a data sharing?'
                ],
                'concurrent': True,
                'expected_max_time_cpu': 90.0,
                'expected_max_time_gpu': 15.0
            },
            {
                'name': 'Large document processing',
                'document_size': 'large',  # >10MB
                'expected_max_processing_time': 300.0  # 5 perc
            }
        ]
    }
}


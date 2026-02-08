"""
Teszt script a Tesla Model 3 kézikönyv PDF-jének használatához
"""

import os
import sys
import logging
from pathlib import Path

# Logging beállítása
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# RAG rendszer import
from src.rag_system import RAGSystem

def test_model3_manual():
    """Tesztelés a Model 3 kézikönyvvel"""
    
    # PDF fájl elérési útja
    pdf_path = "model_3.pdf"
    
    if not Path(pdf_path).exists():
        logger.error(f"A PDF fájl nem található: {pdf_path}")
        logger.info("Kérlek, helyezd el a model_3.pdf fájlt a projekt gyökerében!")
        return
    
    logger.info("RAG rendszer inicializálása...")
    
    try:
        # RAG rendszer létrehozása
        rag_system = RAGSystem()
        
        logger.info("PDF dokumentum betöltése...")
        # Dokumentum hozzáadása
        rag_system.add_documents([pdf_path])
        
        logger.info("Dokumentum sikeresen betöltve!")
        
        # Teszt kérdések
        test_questions = [
            "Hogyan lehet bekapcsolni a Model 3-at?",
            "Mik a főbb funkciók a touchscreen-en?",
            "Hogyan működik a töltés?",
            "Mik a biztonsági funkciók?",
            "Hogyan lehet beállítani a klímát?",
            "Mi az Autopilot és hogyan működik?",
            "Milyen karbantartást igényel a Model 3?",
            "Hogyan lehet használni a navigációt?",
        ]
        
        print("\n" + "="*80)
        print("TESZT KÉRDÉSEK A MODEL 3 KÉZIKÖNYVVEL")
        print("="*80 + "\n")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{'='*80}")
            print(f"Kérdés {i}: {question}")
            print(f"{'='*80}")
            
            try:
                # Válasz generálása
                response = rag_system.query(question, stream=False)
                
                answer = response.get('answer', 'Nincs válasz')
                context_docs = response.get('context', [])
                
                print(f"\nVálasz:")
                print(f"{answer}\n")
                
                if context_docs:
                    print(f"Használt kontextus ({len(context_docs)} dokumentum):")
                    for j, doc in enumerate(context_docs[:3], 1):  # Csak első 3
                        metadata = doc.get('metadata', {})
                        file_name = metadata.get('file_name', 'Ismeretlen')
                        text_preview = doc.get('text', '')[:200] + "..."
                        print(f"  {j}. {file_name}: {text_preview}")
                
            except Exception as e:
                logger.error(f"Hiba a kérdés feldolgozásánál: {e}")
                print(f"Hiba: {e}\n")
        
        print("\n" + "="*80)
        print("TESZT BEFEJEZVE")
        print("="*80)
        
        # Interaktív mód
        print("\n" + "="*80)
        print("INTERAKTÍV MÓD")
        print("Írj 'kilépés' vagy 'exit' a kilépéshez")
        print("="*80 + "\n")
        
        while True:
            try:
                question = input("\nKérdés: ").strip()
                
                if question.lower() in ['kilépés', 'exit', 'quit', 'q']:
                    print("Kilépés...")
                    break
                
                if not question:
                    continue
                
                print("\nVálasz generálása...")
                response = rag_system.query(question, stream=False)
                answer = response.get('answer', 'Nincs válasz')
                
                print(f"\n{answer}\n")
                
            except KeyboardInterrupt:
                print("\n\nKilépés...")
                break
            except Exception as e:
                logger.error(f"Hiba: {e}")
                print(f"Hiba történt: {e}\n")
    
    except Exception as e:
        logger.error(f"Hiba a teszt során: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_model3_manual()


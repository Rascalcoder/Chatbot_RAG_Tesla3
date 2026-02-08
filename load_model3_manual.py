"""
Script a Model 3 kézikönyv PDF betöltéséhez a RAG rendszerbe
Használható a Streamlit app előtt, hogy a dokumentum előre legyen betöltve
"""

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.rag_system import RAGSystem


def load_model3_manual():
    """Model 3 kézikönyv betöltése"""
    
    pdf_path = "model_3.pdf"
    
    if not Path(pdf_path).exists():
        logger.error(f"A PDF fájl nem található: {pdf_path}")
        logger.info("Kérlek, helyezd el a model_3.pdf fájlt a projekt gyökerében!")
        return False
    
    logger.info("RAG rendszer inicializálása...")
    
    try:
        rag_system = RAGSystem()
        
        logger.info(f"PDF dokumentum betöltése: {pdf_path}")
        rag_system.add_documents([pdf_path])
        
        # Statisztikák
        stats = rag_system.get_stats()
        logger.info(f"Dokumentumok száma: {stats['vector_db'].get('document_count', 0)}")
        
        logger.info("✅ Model 3 kézikönyv sikeresen betöltve!")
        logger.info("Most már használhatod a Streamlit app-ot vagy a test scriptet.")
        
        return True
    
    except Exception as e:
        logger.error(f"Hiba a betöltés során: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = load_model3_manual()
    sys.exit(0 if success else 1)


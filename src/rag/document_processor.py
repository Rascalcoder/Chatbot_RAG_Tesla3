"""
Dokumentum feldolgozás modul
Képes PDF, TXT, DOCX fájlok feldolgozására
"""

import os
from typing import List, Dict, Any
from pathlib import Path
import logging

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Dokumentum feldolgozás osztály"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.txt', '.docx']
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Fájl feldolgozása és szöveg kinyerése
        
        Args:
            file_path: A fájl elérési útja
            
        Returns:
            Dict tartalmazza a szöveget és metaadatokat
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"A fájl nem található: {file_path}")
        
        file_ext = file_path.suffix.lower()
        
        if file_ext not in self.supported_formats:
            raise ValueError(f"Nem támogatott fájlformátum: {file_ext}")
        
        logger.info(f"Dokumentum feldolgozása: {file_path.name}")
        
        if file_ext == '.pdf':
            return self._process_pdf(file_path)
        elif file_ext == '.txt':
            return self._process_txt(file_path)
        elif file_ext == '.docx':
            return self._process_docx(file_path)
        else:
            raise ValueError(f"Ismeretlen fájlformátum: {file_ext}")
    
    def _process_pdf(self, file_path: Path) -> Dict[str, Any]:
        """PDF fájl feldolgozása"""
        if PdfReader is None:
            raise ImportError("pypdf nincs telepítve. Telepítsd: pip install pypdf")
        
        text_parts = []
        reader = PdfReader(str(file_path))
        
        for page_num, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)
            except Exception as e:
                logger.warning(f"Hiba a {page_num}. oldal feldolgozásánál: {e}")
        
        full_text = "\n\n".join(text_parts)
        
        return {
            'text': full_text,
            'metadata': {
                'file_name': file_path.name,
                'file_type': 'pdf',
                'num_pages': len(reader.pages),
                'file_size': file_path.stat().st_size
            }
        }
    
    def _process_txt(self, file_path: Path) -> Dict[str, Any]:
        """TXT fájl feldolgozása"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            # Próbáljuk meg latin-1 kódolással
            with open(file_path, 'r', encoding='latin-1') as f:
                text = f.read()
        
        return {
            'text': text,
            'metadata': {
                'file_name': file_path.name,
                'file_type': 'txt',
                'file_size': file_path.stat().st_size
            }
        }
    
    def _process_docx(self, file_path: Path) -> Dict[str, Any]:
        """DOCX fájl feldolgozása"""
        if DocxDocument is None:
            raise ImportError("python-docx nincs telepítve. Telepítsd: pip install python-docx")
        
        doc = DocxDocument(str(file_path))
        text_parts = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        full_text = "\n\n".join(text_parts)
        
        return {
            'text': full_text,
            'metadata': {
                'file_name': file_path.name,
                'file_type': 'docx',
                'file_size': file_path.stat().st_size
            }
        }
    
    def process_multiple_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Több fájl feldolgozása
        
        Args:
            file_paths: Fájl elérési utak listája
            
        Returns:
            Feldolgozott dokumentumok listája
        """
        results = []
        for file_path in file_paths:
            try:
                result = self.process_file(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Hiba a {file_path} feldolgozásánál: {e}")
                continue
        
        return results


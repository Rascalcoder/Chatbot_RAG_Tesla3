"""
Chunking stratégia implementáció
Különböző chunking módszerek támogatása
"""

from typing import List, Dict, Any
import logging
try:
    # LangChain újabb verziók (1.x+)
    from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
except ImportError:
    # Régi LangChain verziók (0.x)
    from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter

logger = logging.getLogger(__name__)


class ChunkingStrategy:
    """Chunking stratégia osztály"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        strategy: str = "recursive"
    ):
        """
        Args:
            chunk_size: Chunk méret karakterekben
            chunk_overlap: Chunk átfedés karakterekben
            strategy: Chunking stratégia ('recursive' vagy 'character')
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
        
        if strategy == "recursive":
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
        else:
            self.splitter = CharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len
            )
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Szöveg chunkokra bontása
        
        Args:
            text: Feldolgozandó szöveg
            metadata: Metaadatok, amelyek minden chunkhoz hozzáadódnak
            
        Returns:
            Chunkok listája metaadatokat tartalmazva
        """
        if not text or not text.strip():
            logger.warning("Üres szöveg chunkolása")
            return []
        
        chunks = self.splitter.split_text(text)
        
        chunk_docs = []
        last_page_number = None  # Track last seen page number
        
        for idx, chunk in enumerate(chunks):
            # Oldalszám detektálása a chunk szövegéből ([PAGE X] marker)
            page_number = self._extract_page_number(chunk)
            
            # Ha nem találunk page markert, használjuk az utolsó ismert oldalszámot
            if page_number:
                last_page_number = page_number
            elif last_page_number:
                page_number = last_page_number
            
            # Tisztított szöveg (PAGE marker eltávolítása)
            clean_text = self._remove_page_markers(chunk)
            
            chunk_doc = {
                'text': clean_text,
                'chunk_index': idx,
                'chunk_size': len(clean_text),
                'metadata': metadata.copy() if metadata else {}
            }
            chunk_doc['metadata']['chunk_index'] = idx
            
            # Oldalszám hozzáadása a metadatához
            if page_number:
                chunk_doc['metadata']['page_number'] = page_number
            
            chunk_docs.append(chunk_doc)
        
        logger.info(f"Szöveg {len(chunk_docs)} chunkra bontva")
        return chunk_docs
    
    def _extract_page_number(self, text: str) -> int | None:
        """Oldalszám kinyerése a [PAGE X] markerből"""
        import re
        match = re.search(r'\[PAGE (\d+)\]', text)
        if match:
            return int(match.group(1))
        return None
    
    def _remove_page_markers(self, text: str) -> str:
        """[PAGE X] markerek eltávolítása a szövegből"""
        import re
        return re.sub(r'\[PAGE \d+\]\s*', '', text)
    
    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Dokumentum chunkokra bontása
        
        Args:
            document: Dokumentum dict 'text' és 'metadata' kulcsokkal
            
        Returns:
            Chunkok listája
        """
        text = document.get('text', '')
        metadata = document.get('metadata', {})
        
        return self.chunk_text(text, metadata)
    
    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Több dokumentum chunkokra bontása
        
        Args:
            documents: Dokumentumok listája
            
        Returns:
            Összes chunk listája
        """
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def get_chunk_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Chunk statisztikák számítása
        
        Args:
            chunks: Chunkok listája
            
        Returns:
            Statisztikák dict
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'avg_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0,
                'total_characters': 0
            }
        
        chunk_sizes = [chunk['chunk_size'] for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'total_characters': sum(chunk_sizes)
        }


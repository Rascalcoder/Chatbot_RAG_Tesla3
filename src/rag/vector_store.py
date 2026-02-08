"""
Vektor adatbázis kezelés
ChromaDB használata vektor tároláshoz
"""

import os
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class VectorStore:
    """Vektor adatbázis osztály ChromaDB-vel"""
    
    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str = None
    ):
        """
        Args:
            collection_name: Collection neve
            persist_directory: Adatbázis mentési könyvtár
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or os.getenv(
            'VECTOR_DB_PATH',
            './data/vector_db'
        )
        
        # Könyvtár létrehozása ha nem létezik
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        self._client = None
        self._collection = None
        self._init_db()
    
    def _init_db(self):
        """ChromaDB inicializálása"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Collection létrehozása vagy betöltése
            try:
                self._collection = self._client.get_collection(name=self.collection_name)
                logger.info(f"Meglévő collection betöltve: {self.collection_name}")
            except Exception:
                self._collection = self._client.create_collection(name=self.collection_name)
                logger.info(f"Új collection létrehozva: {self.collection_name}")
        
        except ImportError:
            raise ImportError("chromadb nincs telepítve. Telepítsd: pip install chromadb")
        except Exception as e:
            logger.error(f"Hiba a ChromaDB inicializálásánál: {e}")
            raise
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]] = None,
        ids: List[str] = None
    ):
        """
        Dokumentumok hozzáadása a vektor adatbázishoz
        
        Args:
            texts: Szövegek listája
            embeddings: Embedding vektorok listája
            metadatas: Metaadatok listája
            ids: Dokumentum ID-k listája
        """
        if not texts or not embeddings:
            logger.warning("Üres lista hozzáadása a vektor adatbázishoz")
            return
        
        if len(texts) != len(embeddings):
            raise ValueError("A szövegek és embeddingek száma nem egyezik")
        
        # ID-k generálása ha nincsenek
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(texts))]
        
        # Metaadatok beállítása
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        try:
            self._collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"{len(texts)} dokumentum hozzáadva a vektor adatbázishoz")
        except Exception as e:
            logger.error(f"Hiba a dokumentumok hozzáadásánál: {e}")
            raise
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Keresés a vektor adatbázisban
        
        Args:
            query_embedding: Query embedding vektor
            top_k: Visszaadandó eredmények száma
            filter_dict: Szűrési feltételek
            
        Returns:
            Találatok listája
        """
        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_dict if filter_dict else None
            )
            
            # Eredmények formázása
            documents = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    doc = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    }
                    documents.append(doc)
            
            return documents
        
        except Exception as e:
            logger.error(f"Hiba a keresésnél: {e}")
            raise
    
    def delete_collection(self):
        """Collection törlése"""
        try:
            self._client.delete_collection(name=self.collection_name)
            logger.info(f"Collection törölve: {self.collection_name}")
            self._init_db()  # Új collection létrehozása
        except Exception as e:
            logger.error(f"Hiba a collection törlésénél: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Collection információk lekérdezése
        
        Returns:
            Collection információk
        """
        try:
            count = self._collection.count()
            return {
                'collection_name': self.collection_name,
                'document_count': count,
                'persist_directory': self.persist_directory
            }
        except Exception as e:
            logger.error(f"Hiba az információk lekérdezésénél: {e}")
            return {
                'collection_name': self.collection_name,
                'document_count': 0,
                'persist_directory': self.persist_directory
            }


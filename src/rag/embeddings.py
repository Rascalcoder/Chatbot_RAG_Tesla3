"""
Embedding modell kezelés
Támogatja az OpenAI embedding modelleket és lokális alternatívákat
"""

import os
from typing import List, Union
import logging
from dotenv import load_dotenv
from src.utils.hf_auth import ensure_hf_token_env

load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Embedding modell osztály"""
    
    def __init__(
        self,
        model_name: str = None,
        use_openai: bool = False
    ):
        """
        Args:
            model_name: Embedding modell neve (alapértelmezett: BGE-M3)
            use_openai: Használjon-e OpenAI API-t (True) vagy lokális modellt (False)
        """
        self.use_openai = use_openai
        self.model_name = model_name or os.getenv('EMBEDDING_MODEL', 'BAAI/bge-m3')
        self._model = None
        self._openai_client = None
        
        if use_openai:
            self._init_openai()
        else:
            self._init_local()
    
    def _init_openai(self):
        """OpenAI embedding inicializálása"""
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY nincs beállítva a .env fájlban")
            
            self._openai_client = OpenAI(api_key=api_key)
            logger.info(f"OpenAI embedding modell inicializálva: {self.model_name}")
        except ImportError:
            raise ImportError("openai nincs telepítve. Telepítsd: pip install openai")
        except Exception as e:
            logger.error(f"Hiba az OpenAI inicializálásánál: {e}")
            raise
    
    def _init_local(self):
        """Lokális embedding modell inicializálása (BGE-M3)"""
        try:
            hf_token = ensure_hf_token_env()
            
            # BGE-M3 modell használata FlagEmbedding vagy sentence-transformers-szel
            if 'bge-m3' in self.model_name.lower() or 'BAAI/bge-m3' in self.model_name:
                try:
                    # Próbáljuk meg a FlagEmbedding-et (ajánlott BGE-M3-höz)
                    from FlagEmbedding import FlagModel
                    self._model = FlagModel(self.model_name, use_fp16=False)
                    logger.info(f"BGE-M3 embedding modell inicializálva FlagEmbedding-gel: {self.model_name}")
                except ImportError:
                    # Fallback sentence-transformers-re
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(self.model_name, token=hf_token)
                    logger.info(f"BGE-M3 embedding modell inicializálva sentence-transformers-szel: {self.model_name}")
            else:
                # Egyéb modellek sentence-transformers-szel
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, token=hf_token)
                logger.info(f"Lokális embedding modell inicializálva: {self.model_name}")
        except ImportError:
            raise ImportError("sentence-transformers vagy FlagEmbedding nincs telepítve. Telepítsd: pip install sentence-transformers FlagEmbedding")
        except Exception as e:
            logger.error(f"Hiba a lokális modell inicializálásánál: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Egyetlen szöveg embedding generálása
        
        Args:
            text: Szöveg
            
        Returns:
            Embedding vektor
        """
        return self.embed_texts([text])[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Több szöveg embedding generálása
        
        Args:
            texts: Szövegek listája
            
        Returns:
            Embedding vektorok listája
        """
        if not texts:
            return []
        
        if self.use_openai:
            return self._embed_openai(texts)
        else:
            return self._embed_local(texts)
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """OpenAI API használata embedding generáláshoz"""
        try:
            response = self._openai_client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            embeddings = [item.embedding for item in response.data]
            return embeddings
        except Exception as e:
            logger.error(f"Hiba az OpenAI embedding generálásánál: {e}")
            raise
    
    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Lokális modell használata embedding generáláshoz"""
        try:
            # BGE-M3 esetén külön kezelés
            if hasattr(self._model, 'encode_queries') and 'bge-m3' in self.model_name.lower():
                # BGE-M3 query encoding (dokumentumokhoz is használjuk)
                embeddings = self._model.encode_queries(texts)
            else:
                # Általános encode
                embeddings = self._model.encode(texts, show_progress_bar=False)
            
            # Numpy array konverzió listára
            if hasattr(embeddings, 'tolist'):
                return embeddings.tolist()
            return embeddings
        except Exception as e:
            logger.error(f"Hiba a lokális embedding generálásánál: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """
        Embedding dimenzió számának lekérdezése
        
        Returns:
            Embedding dimenzió száma
        """
        if self.use_openai:
            # OpenAI embedding dimenziók
            dim_map = {
                'text-embedding-3-small': 1536,
                'text-embedding-3-large': 3072,
                'text-embedding-ada-002': 1536
            }
            return dim_map.get(self.model_name, 1536)
        else:
            # Lokális modell dimenziója
            if self._model is None:
                self._init_local()
            
            # BGE-M3 dimenzió: 1024
            if 'bge-m3' in self.model_name.lower():
                return 1024
            
            # Egyéb modellek
            if hasattr(self._model, 'get_sentence_embedding_dimension'):
                return self._model.get_sentence_embedding_dimension()
            elif hasattr(self._model, 'dim'):
                return self._model.dim
            else:
                # Alapértelmezett BGE-M3 dimenzió
                return 1024


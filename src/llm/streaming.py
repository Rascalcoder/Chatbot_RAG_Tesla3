"""
Streaming válaszgenerálás modul
"""

import os
from typing import List, Dict, Any, Optional, Iterator
import logging
from dotenv import load_dotenv
from src.utils.hf_auth import ensure_hf_token_env

load_dotenv()

logger = logging.getLogger(__name__)


class StreamingGenerator:
    """Streaming LLM válaszgeneráló osztály (Qwen-4B lokális modell)"""
    
    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        use_openai: bool = False
    ):
        """
        Args:
            model_name: LLM modell neve (alapértelmezett: Qwen-4B)
            temperature: Temperature paraméter
            max_tokens: Maximális token szám
            use_openai: Használjon-e OpenAI API-t (False = lokális Qwen)
        """
        self.use_openai = use_openai
        self.model_name = model_name or os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None
        self._pipeline = None
        self._tokenizer = None
        self._init_model()
    
    def _init_model(self):
        """LLM modell inicializálása (Qwen-4B vagy OpenAI)"""
        if self.use_openai:
            self._init_openai()
        else:
            self._init_local()
    
    def _init_openai(self):
        """OpenAI client inicializálása"""
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY nincs beállítva a .env fájlban")
            
            self._client = OpenAI(api_key=api_key)
            logger.info(f"OpenAI Streaming LLM inicializálva: {self.model_name}")
        except ImportError:
            raise ImportError("openai nincs telepítve. Telepítsd: pip install openai")
        except Exception as e:
            logger.error(f"Hiba az OpenAI inicializálásánál: {e}")
            raise
    
    def _init_local(self):
        """Lokális LLM modell inicializálása"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            # Get HF token (silent mode if using public models)
            hf_token = ensure_hf_token_env(silent=False)
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Qwen-4B streaming modell betöltése: {self.model_name} (device: {device})")
            
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                token=hf_token
            )
            
            self._pipeline = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None,
                trust_remote_code=True,
                token=hf_token
            )
            
            if device == "cpu":
                self._pipeline = self._pipeline.to(device)
            
            logger.info(f"Qwen-4B Streaming LLM inicializálva: {self.model_name}")
        except ImportError:
            raise ImportError("transformers nincs telepítve. Telepítsd: pip install transformers torch")
        except Exception as e:
            logger.error(f"Hiba a Qwen streaming modell inicializálásánál: {e}")
            raise
    
    def generate_stream(
        self,
        prompt: str,
        context: Optional[List[Dict[str, Any]]] = None,
        system_message: str = None
    ) -> Iterator[str]:
        """
        Streaming válasz generálása
        
        Args:
            prompt: Felhasználói prompt
            context: Kontextus dokumentumok listája
            system_message: Rendszerüzenet
            
        Yields:
            Válasz chunkok
        """
        if self.use_openai:
            yield from self._generate_stream_openai(prompt, context, system_message)
        else:
            yield from self._generate_stream_local(prompt, context, system_message)
    
    def _generate_stream_openai(self, prompt: str, context: Optional[List[Dict[str, Any]]], system_message: Optional[str]) -> Iterator[str]:
        """OpenAI streaming generálás"""
        messages = self._build_messages(prompt, context, system_message)
        
        try:
            stream = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error(f"Hiba a streaming válasz generálásánál: {e}")
            raise
    
    def _generate_stream_local(self, prompt: str, context: Optional[List[Dict[str, Any]]], system_message: Optional[str]) -> Iterator[str]:
        """Lokális Qwen streaming generálás"""
        try:
            from transformers import TextIteratorStreamer
            import torch
            from threading import Thread
            
            # Prompt formázása
            if context:
                context_text = self._format_context(context)
                full_prompt = f"{system_message or ''}\n\nKontextus:\n{context_text}\n\nKérdés: {prompt}\n\nVálasz:"
            else:
                full_prompt = f"{system_message or ''}\n\nKérdés: {prompt}\n\nVálasz:"
            
            # Tokenizálás
            inputs = self._tokenizer(full_prompt, return_tensors="pt")
            if self._pipeline.device.type == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            # Streamer létrehozása
            streamer = TextIteratorStreamer(
                self._tokenizer,
                skip_prompt=True,
                skip_special_tokens=True
            )
            
            # Generálás külön szálon
            generation_kwargs = {
                **inputs,
                "max_new_tokens": self.max_tokens,
                "temperature": self.temperature,
                "do_sample": True if self.temperature > 0 else False,
                "pad_token_id": self._tokenizer.eos_token_id,
                "streamer": streamer
            }
            
            thread = Thread(target=self._pipeline.generate, kwargs=generation_kwargs)
            thread.start()
            
            # Tokenek streamelése
            for token in streamer:
                yield token
            
            thread.join()
            
        except Exception as e:
            logger.error(f"Hiba a Qwen streaming generálásánál: {e}")
            # Fallback: egyszerű generálás
            try:
                answer = self._generate_simple_local(prompt, context, system_message)
                for char in answer:
                    yield char
            except:
                raise
    
    def _generate_simple_local(self, prompt: str, context: Optional[List[Dict[str, Any]]], system_message: Optional[str]) -> str:
        """Egyszerű lokális generálás (fallback)"""
        import torch
        
        if context:
            context_text = self._format_context(context)
            full_prompt = f"{system_message or ''}\n\nKontextus:\n{context_text}\n\nKérdés: {prompt}\n\nVálasz:"
        else:
            full_prompt = f"{system_message or ''}\n\nKérdés: {prompt}\n\nVálasz:"
        
        inputs = self._tokenizer(full_prompt, return_tensors="pt")
        if self._pipeline.device.type == "cuda":
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self._pipeline.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                do_sample=True if self.temperature > 0 else False,
                pad_token_id=self._tokenizer.eos_token_id
            )
        
        generated_text = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        answer = generated_text[len(full_prompt):].strip()
        return answer
    
    def _build_messages(
        self,
        prompt: str,
        context: Optional[List[Dict[str, Any]]],
        system_message: Optional[str]
    ) -> List[Dict[str, str]]:
        """Üzenetek listájának összeállítása"""
        messages = []
        
        # Rendszerüzenet
        if system_message is None:
            system_message = """Te egy segítőkész AI asszisztens vagy, aki a megadott dokumentumok alapján válaszol.
Használd a kontextust, hogy pontos és releváns válaszokat adj. Ha az információ nincs a kontextusban,
mondd el, hogy nem tudod megválaszolni a kérdést a rendelkezésre álló információk alapján."""
        
        messages.append({"role": "system", "content": system_message})
        
        # Kontextus hozzáadása
        if context:
            context_text = self._format_context(context)
            messages.append({
                "role": "user",
                "content": f"Kontextus:\n{context_text}\n\nKérdés: {prompt}"
            })
        else:
            messages.append({"role": "user", "content": prompt})
        
        return messages
    
    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Kontextus formázása oldalszámmal"""
        context_parts = []
        for i, doc in enumerate(context, 1):
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            file_name = metadata.get('file_name', 'Ismeretlen')
            page_number = metadata.get('page_number')
            
            # Forrás információ oldalszámmal
            source_info = f"[{i}] {file_name}"
            if page_number:
                source_info += f" (Oldal: {page_number})"
            
            context_parts.append(f"{source_info}:\n{text}\n")
        
        return "\n---\n".join(context_parts)
    
    def generate_stream_with_metadata(
        self,
        prompt: str,
        context: Optional[List[Dict[str, Any]]] = None,
        system_message: str = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Streaming válasz generálása metadata-val
        
        Yields:
            Dict-ek tartalmazva a chunk-ot és metadata-t
        """
        messages = self._build_messages(prompt, context, system_message)
        
        try:
            import time
            start_time = time.time()
            full_response = ""
            first_token_time = None
            
            if self.use_openai:
                messages = self._build_messages(prompt, context, system_message)
                stream = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        
                        if first_token_time is None:
                            first_token_time = time.time() - start_time
                        
                        yield {
                            'chunk': content,
                            'full_response': full_response,
                            'first_token_time': first_token_time,
                            'timestamp': time.time()
                        }
            else:
                # Lokális streaming
                for chunk in self._generate_stream_local(prompt, context, system_message):
                    full_response += chunk
                    
                    if first_token_time is None:
                        first_token_time = time.time() - start_time
                    
                    yield {
                        'chunk': chunk,
                        'full_response': full_response,
                        'first_token_time': first_token_time,
                        'timestamp': time.time()
                    }
            
            # Végleges metadata
            end_time = time.time()
            total_time = end_time - start_time
            
            yield {
                'chunk': None,  # Végjel
                'full_response': full_response,
                'first_token_time': first_token_time,
                'total_time': total_time,
                'metadata': {
                    'model': self.model_name,
                    'total_chars': len(full_response)
                }
            }
        
        except Exception as e:
            logger.error(f"Hiba a streaming válasz generálásánál: {e}")
            raise


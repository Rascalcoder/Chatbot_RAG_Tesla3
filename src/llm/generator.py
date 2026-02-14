"""
LLM válaszgenerálás modul
"""

import os
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv
from src.utils.hf_auth import ensure_hf_token_env
import torch

load_dotenv()

logger = logging.getLogger(__name__)


class LLMGenerator:
    """LLM válaszgeneráló osztály (Qwen-4B lokális modell)"""
    
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
            logger.info(f"OpenAI LLM inicializálva: {self.model_name}")
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
            logger.info(f"Qwen-4B modell betöltése: {self.model_name} (device: {device})")
            
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
            
            logger.info(f"Qwen-4B LLM inicializálva: {self.model_name}")
        except ImportError:
            raise ImportError("transformers nincs telepítve. Telepítsd: pip install transformers torch")
        except Exception as e:
            logger.error(f"Hiba a Qwen modell inicializálásánál: {e}")
            raise
    
    def generate(
        self,
        prompt: str,
        context: Optional[List[Dict[str, Any]]] = None,
        system_message: str = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Válasz generálása

        Args:
            prompt: Felhasználói prompt
            context: Kontextus dokumentumok listája
            system_message: Rendszerüzenet
            conversation_history: Korábbi üzenetek [{'role': 'user'|'assistant', 'content': str}]

        Returns:
            Generált válasz
        """
        if self.use_openai:
            return self._generate_openai(prompt, context, system_message, conversation_history)
        else:
            return self._generate_local(prompt, context, system_message, conversation_history)
    
    def _generate_openai(self, prompt: str, context: Optional[List[Dict[str, Any]]], system_message: Optional[str], conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """OpenAI API-val generálás"""
        messages = self._build_messages(prompt, context, system_message, conversation_history)
        
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            answer = response.choices[0].message.content
            logger.info(f"Válasz generálva: {len(answer)} karakter")
            
            return answer
        
        except Exception as e:
            logger.error(f"Hiba a válasz generálásánál: {e}")
            raise
    
    def _generate_local(self, prompt: str, context: Optional[List[Dict[str, Any]]], system_message: Optional[str], conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Lokális Qwen modelllel generálás"""
        try:
            # Conversation history formázása
            history_text = ""
            if conversation_history:
                for msg in conversation_history[-6:]:  # Utolsó 3 pár (6 üzenet)
                    role_label = "Felhasználó" if msg['role'] == 'user' else "Asszisztens"
                    history_text += f"{role_label}: {msg['content']}\n\n"

            # Prompt formázása Qwen formátumhoz
            if context:
                context_text = self._format_context(context)
                full_prompt = f"{system_message or ''}\n\n{history_text}Kontextus:\n{context_text}\n\nKérdés: {prompt}\n\nVálasz:"
            else:
                full_prompt = f"{system_message or ''}\n\n{history_text}Kérdés: {prompt}\n\nVálasz:"
            
            # Tokenizálás
            inputs = self._tokenizer(full_prompt, return_tensors="pt")
            if self._pipeline.device.type == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            # Generálás
            with torch.no_grad():
                outputs = self._pipeline.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    do_sample=True if self.temperature > 0 else False,
                    pad_token_id=self._tokenizer.eos_token_id
                )
            
            # Dekódolás
            generated_text = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Csak a válasz részt kinyerni (az eredeti prompt után)
            answer = generated_text[len(full_prompt):].strip()
            
            logger.info(f"Qwen válasz generálva: {len(answer)} karakter")
            
            return answer
        
        except Exception as e:
            logger.error(f"Hiba a Qwen válasz generálásánál: {e}")
            raise
    
    def _build_messages(
        self,
        prompt: str,
        context: Optional[List[Dict[str, Any]]],
        system_message: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """Üzenetek listájának összeállítása conversation history-val"""
        messages = []

        # Rendszerüzenet
        if system_message is None:
            system_message = """Te egy segítőkész AI asszisztens vagy, aki a megadott dokumentumok alapján válaszol.
Használd a kontextust, hogy pontos és releváns válaszokat adj. Ha az információ nincs a kontextusban,
mondd el, hogy nem tudod megválaszolni a kérdést a rendelkezésre álló információk alapján."""

        messages.append({"role": "system", "content": system_message})

        # Korábbi üzenetek beszúrása (utolsó 3 pár = 6 üzenet max)
        if conversation_history:
            for msg in conversation_history[-6:]:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })

        # Aktuális kérdés kontextussal
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
    
    def generate_with_metadata(
        self,
        prompt: str,
        context: Optional[List[Dict[str, Any]]] = None,
        system_message: str = None
    ) -> Dict[str, Any]:
        """
        Válasz generálása metadata-val
        
        Returns:
            Dict tartalmazza a választ és metadata-t
        """
        try:
            if self.use_openai:
                from openai import OpenAI
                messages = self._build_messages(prompt, context, system_message)
                
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                answer = response.choices[0].message.content
                usage = response.usage
                
                return {
                    'answer': answer,
                    'metadata': {
                        'model': self.model_name,
                        'prompt_tokens': usage.prompt_tokens,
                        'completion_tokens': usage.completion_tokens,
                        'total_tokens': usage.total_tokens,
                        'temperature': self.temperature
                    }
                }
            else:
                # Lokális modell
                answer = self._generate_local(prompt, context, system_message)
                
                # Token szám becslés
                prompt_tokens = len(self._tokenizer.encode(prompt))
                completion_tokens = len(self._tokenizer.encode(answer))
                
                return {
                    'answer': answer,
                    'metadata': {
                        'model': self.model_name,
                        'prompt_tokens': prompt_tokens,
                        'completion_tokens': completion_tokens,
                        'total_tokens': prompt_tokens + completion_tokens,
                        'temperature': self.temperature
                    }
                }
        
        except Exception as e:
            logger.error(f"Hiba a válasz generálásánál: {e}")
            raise


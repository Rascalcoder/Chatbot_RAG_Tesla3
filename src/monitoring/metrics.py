"""
Metrikák gyűjtése modul
Token használat, latency, költség tracking
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Metrikák gyűjtő osztály"""
    
    def __init__(self, metrics_file: str = "./data/metrics.json"):
        """
        Args:
            metrics_file: Metrikák mentési fájlja
        """
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.metrics: List[Dict[str, Any]] = []
        self._load_metrics()
    
    def _load_metrics(self):
        """Metrikák betöltése fájlból"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    self.metrics = json.load(f)
                logger.info(f"{len(self.metrics)} metrika betöltve")
            except Exception as e:
                logger.warning(f"Hiba a metrikák betöltésénél: {e}")
                self.metrics = []
        else:
            self.metrics = []
    
    def _save_metrics(self):
        """Metrikák mentése fájlba"""
        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Hiba a metrikák mentésénél: {e}")
    
    def record_llm_call(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        first_token_time: Optional[float] = None,
        total_time: Optional[float] = None,
        cost: Optional[float] = None
    ):
        """
        LLM hívás rögzítése
        
        Args:
            prompt_tokens: Prompt tokenek száma
            completion_tokens: Completion tokenek száma
            model: Modell neve
            first_token_time: Első token ideje másodpercben
            total_time: Teljes válaszidő másodpercben
            cost: Költség USD-ben
        """
        metric = {
            'timestamp': datetime.now().isoformat(),
            'type': 'llm_call',
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': prompt_tokens + completion_tokens,
            'model': model,
            'first_token_time': first_token_time,
            'total_time': total_time,
            'cost': cost
        }
        
        self.metrics.append(metric)
        self._save_metrics()
        logger.debug(f"LLM metrika rögzítve: {metric}")
    
    def record_embedding_call(
        self,
        input_tokens: int,
        model: str,
        cost: Optional[float] = None
    ):
        """
        Embedding hívás rögzítése
        
        Args:
            input_tokens: Input tokenek száma
            model: Modell neve
            cost: Költség USD-ben
        """
        metric = {
            'timestamp': datetime.now().isoformat(),
            'type': 'embedding_call',
            'input_tokens': input_tokens,
            'model': model,
            'cost': cost
        }
        
        self.metrics.append(metric)
        self._save_metrics()
        logger.debug(f"Embedding metrika rögzítve: {metric}")
    
    def record_retrieval(
        self,
        query: str,
        num_results: int,
        retrieval_time: float
    ):
        """
        Retrieval rögzítése

        Args:
            query: Query szöveg
            num_results: Találatok száma
            retrieval_time: Retrieval idő másodpercben
        """
        metric = {
            'timestamp': datetime.now().isoformat(),
            'type': 'retrieval',
            'query': query[:100],  # Első 100 karakter
            'num_results': num_results,
            'retrieval_time': retrieval_time
        }

        self.metrics.append(metric)
        self._save_metrics()
        logger.debug(f"Retrieval metrika rögzítve")

    def record_pipeline_event(
        self,
        event_type: str,
        data: Dict[str, Any] = None
    ):
        """
        Pipeline event rögzítése (observability).
        Pl. translation, retrieval_detail, rerank_detail.

        Args:
            event_type: Event típusa (pl. 'translation', 'retrieval_detail')
            data: Event adatai
        """
        metric = {
            'timestamp': datetime.now().isoformat(),
            'type': f'pipeline_{event_type}',
            **(data or {})
        }

        self.metrics.append(metric)
        self._save_metrics()
        logger.debug(f"Pipeline event rögzítve: {event_type}")

    def record_user_feedback(
        self,
        message_id: str,
        rating: str,
        comment: Optional[str] = None,
        query: Optional[str] = None,
        response: Optional[str] = None
    ):
        """
        Felhasználói feedback rögzítése

        Args:
            message_id: Üzenet azonosító
            rating: Értékelés ("positive" / "negative" / "neutral")
            comment: Opcionális szöveges visszajelzés
            query: Az eredeti kérdés (opcionális)
            response: A válasz (opcionális)
        """
        metric = {
            'timestamp': datetime.now().isoformat(),
            'type': 'user_feedback',
            'message_id': message_id,
            'rating': rating,
            'comment': comment,
            'query': query[:100] if query else None,
            'response': response[:200] if response else None
        }

        self.metrics.append(metric)
        self._save_metrics()
        logger.info(f"Felhasználói feedback rögzítve: {rating}")

    def get_feedback_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Feedback statisztikák lekérdezése

        Args:
            days: Hány napra visszamenőleg

        Returns:
            Feedback statisztikák dict
        """
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        feedbacks = [
            m for m in self.metrics
            if m['type'] == 'user_feedback' and datetime.fromisoformat(m['timestamp']) >= cutoff_date
        ]

        if not feedbacks:
            return {
                'total_feedbacks': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'satisfaction_score': 0.0,
                'recent_comments': []
            }

        positive = sum(1 for f in feedbacks if f.get('rating') == 'positive')
        negative = sum(1 for f in feedbacks if f.get('rating') == 'negative')
        neutral = sum(1 for f in feedbacks if f.get('rating') == 'neutral')

        # Satisfaction score: (positive - negative) / total
        total = len(feedbacks)
        satisfaction_score = ((positive - negative) / total) * 100 if total > 0 else 0

        # Legutóbbi kommentek (max 5)
        recent_comments = [
            {
                'timestamp': f.get('timestamp'),
                'rating': f.get('rating'),
                'comment': f.get('comment'),
                'query': f.get('query')
            }
            for f in sorted(feedbacks, key=lambda x: x.get('timestamp', ''), reverse=True)[:5]
            if f.get('comment')
        ]

        return {
            'total_feedbacks': total,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'satisfaction_score': satisfaction_score,
            'recent_comments': recent_comments
        }
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Statisztikák lekérdezése
        
        Args:
            days: Hány napra visszamenőleg
            
        Returns:
            Statisztikák dict
        """
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_metrics = [
            m for m in self.metrics
            if datetime.fromisoformat(m['timestamp']) >= cutoff_date
        ]
        
        llm_calls = [m for m in recent_metrics if m['type'] == 'llm_call']
        embedding_calls = [m for m in recent_metrics if m['type'] == 'embedding_call']
        retrievals = [m for m in recent_metrics if m['type'] == 'retrieval']
        
        total_prompt_tokens = sum(m.get('prompt_tokens', 0) for m in llm_calls)
        total_completion_tokens = sum(m.get('completion_tokens', 0) for m in llm_calls)
        total_tokens = total_prompt_tokens + total_completion_tokens
        total_cost = sum(m.get('cost', 0) or 0 for m in recent_metrics)
        
        avg_first_token_time = None
        if llm_calls:
            first_token_times = [m.get('first_token_time') for m in llm_calls if m.get('first_token_time')]
            if first_token_times:
                avg_first_token_time = sum(first_token_times) / len(first_token_times)
        
        avg_total_time = None
        if llm_calls:
            total_times = [m.get('total_time') for m in llm_calls if m.get('total_time')]
            if total_times:
                avg_total_time = sum(total_times) / len(total_times)
        
        # Feedback statisztikák
        feedback_stats = self.get_feedback_statistics(days=days)

        return {
            'period_days': days,
            'total_llm_calls': len(llm_calls),
            'total_embedding_calls': len(embedding_calls),
            'total_retrievals': len(retrievals),
            'total_prompt_tokens': total_prompt_tokens,
            'total_completion_tokens': total_completion_tokens,
            'total_tokens': total_tokens,
            'total_cost_usd': total_cost,
            'avg_first_token_time_sec': avg_first_token_time,
            'avg_total_time_sec': avg_total_time,
            'feedback': feedback_stats
        }
    
    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int = 0) -> float:
        """
        Költség számítása modell és tokenek alapján
        
        Args:
            model: Modell neve
            prompt_tokens: Prompt tokenek
            completion_tokens: Completion tokenek
            
        Returns:
            Költség USD-ben
        """
        # OpenAI árazás (2024)
        pricing = {
            'gpt-4o': {'prompt': 0.0025 / 1000, 'completion': 0.01 / 1000},
            'gpt-4o-mini': {'prompt': 0.00015 / 1000, 'completion': 0.0006 / 1000},
            'gpt-4': {'prompt': 0.03 / 1000, 'completion': 0.06 / 1000},
            'gpt-3.5-turbo': {'prompt': 0.0005 / 1000, 'completion': 0.0015 / 1000},
            'text-embedding-3-small': {'prompt': 0.02 / 1000, 'completion': 0},
            'text-embedding-3-large': {'prompt': 0.13 / 1000, 'completion': 0},
        }
        
        model_pricing = pricing.get(model, {'prompt': 0.001 / 1000, 'completion': 0.002 / 1000})
        
        cost = (prompt_tokens * model_pricing['prompt']) + (completion_tokens * model_pricing['completion'])
        return cost


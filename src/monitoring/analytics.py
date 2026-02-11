"""
Analitika modul
Vizualizációk és jelentések generálása
"""

from typing import Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class Analytics:
    """Analitika osztály"""
    
    def __init__(self, metrics_collector):
        """
        Args:
            metrics_collector: MetricsCollector példány
        """
        self.metrics_collector = metrics_collector
    
    def get_daily_usage(self, days: int = 30) -> pd.DataFrame:
        """
        Napi használati statisztikák
        
        Args:
            days: Hány napra visszamenőleg
            
        Returns:
            DataFrame napi statisztikákkal
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_metrics = [
            m for m in self.metrics_collector.metrics
            if m['type'] == 'llm_call' and datetime.fromisoformat(m['timestamp']) >= cutoff_date
        ]

        if not recent_metrics:
            return pd.DataFrame(columns=['date', 'total_tokens', 'cost'])

        try:
            df = pd.DataFrame(recent_metrics)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date

            # Fill missing values with 0
            if 'total_tokens' not in df.columns:
                df['total_tokens'] = 0
            else:
                df['total_tokens'] = df['total_tokens'].fillna(0)

            if 'cost' not in df.columns:
                df['cost'] = 0
            else:
                df['cost'] = df['cost'].fillna(0)

            daily_stats = df.groupby('date').agg({
                'total_tokens': 'sum',
                'cost': 'sum'
            }).reset_index()

            return daily_stats
        except Exception as e:
            logger.error(f"Hiba a napi használat lekérdezésénél: {e}")
            return pd.DataFrame(columns=['date', 'total_tokens', 'cost'])
    
    def get_model_usage(self) -> Dict[str, Any]:
        """
        Modell használati statisztikák
        
        Returns:
            Dict modell statisztikákkal
        """
        llm_calls = [m for m in self.metrics_collector.metrics if m['type'] == 'llm_call']

        if not llm_calls:
            return {}

        try:
            df = pd.DataFrame(llm_calls)

            # Fill missing values with 0
            if 'total_tokens' not in df.columns:
                df['total_tokens'] = 0
            else:
                df['total_tokens'] = df['total_tokens'].fillna(0)

            if 'cost' not in df.columns:
                df['cost'] = 0
            else:
                df['cost'] = df['cost'].fillna(0)

            model_stats = df.groupby('model').agg({
                'total_tokens': 'sum',
                'cost': 'sum',
                'model': 'count'
            }).rename(columns={'model': 'count'}).to_dict('index')

            return model_stats
        except Exception as e:
            logger.error(f"Hiba a modell használat lekérdezésénél: {e}")
            return {}
    
    def get_latency_trends(self, days: int = 7) -> pd.DataFrame:
        """
        Latency trendek
        
        Args:
            days: Hány napra visszamenőleg
            
        Returns:
            DataFrame latency trendekkel
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_metrics = [
            m for m in self.metrics_collector.metrics
            if m['type'] == 'llm_call' and datetime.fromisoformat(m['timestamp']) >= cutoff_date
        ]
        
        if not recent_metrics:
            return pd.DataFrame()
        
        df = pd.DataFrame(recent_metrics)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        latency_stats = df.groupby('date').agg({
            'first_token_time': 'mean',
            'total_time': 'mean'
        }).reset_index()
        
        return latency_stats
    
    def get_feedback_trends(self, days: int = 30) -> pd.DataFrame:
        """
        Feedback trendek időben

        Args:
            days: Hány napra visszamenőleg

        Returns:
            DataFrame feedback trendekkel
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        feedbacks = [
            m for m in self.metrics_collector.metrics
            if m['type'] == 'user_feedback' and datetime.fromisoformat(m['timestamp']) >= cutoff_date
        ]

        if not feedbacks:
            return pd.DataFrame()

        df = pd.DataFrame(feedbacks)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date

        # Napi feedback aggregálás
        daily_feedback = df.groupby(['date', 'rating']).size().unstack(fill_value=0).reset_index()

        return daily_feedback

    def get_feedback_distribution(self) -> Dict[str, int]:
        """
        Feedback eloszlás (positive/negative/neutral)

        Returns:
            Dict feedback eloszlással
        """
        feedbacks = [m for m in self.metrics_collector.metrics if m['type'] == 'user_feedback']

        if not feedbacks:
            return {'positive': 0, 'negative': 0, 'neutral': 0}

        df = pd.DataFrame(feedbacks)
        distribution = df['rating'].value_counts().to_dict()

        # Ensure all categories exist
        for rating in ['positive', 'negative', 'neutral']:
            if rating not in distribution:
                distribution[rating] = 0

        return distribution

    def generate_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Összesített jelentés generálása

        Args:
            days: Hány napra visszamenőleg

        Returns:
            Jelentés dict
        """
        stats = self.metrics_collector.get_statistics(days=days)
        daily_usage = self.get_daily_usage(days=days)
        model_usage = self.get_model_usage()
        latency_trends = self.get_latency_trends(days=min(days, 7))
        feedback_trends = self.get_feedback_trends(days=days)
        feedback_distribution = self.get_feedback_distribution()

        return {
            'summary': stats,
            'daily_usage': daily_usage.to_dict('records') if not daily_usage.empty else [],
            'model_usage': model_usage,
            'latency_trends': latency_trends.to_dict('records') if not latency_trends.empty else [],
            'feedback_trends': feedback_trends.to_dict('records') if not feedback_trends.empty else [],
            'feedback_distribution': feedback_distribution
        }


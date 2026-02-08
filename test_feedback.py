"""
Feedback rendszer teszt
"""

import sys
from pathlib import Path

# Add project to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from src.monitoring.metrics import MetricsCollector
from src.monitoring.analytics import Analytics

def test_feedback_system():
    """Feedback rendszer tesztelése"""
    print("=== Feedback rendszer teszt ===\n")

    # Metrics collector létrehozása
    metrics_collector = MetricsCollector(metrics_file="./data/test_metrics.json")

    # Test feedbackek hozzáadása
    print("[1] Feedback-ek rogzitese...")
    metrics_collector.record_user_feedback(
        message_id="msg_001",
        rating="positive",
        query="Hogyan működik az Autopilot?",
        response="Az Autopilot egy fejlett vezetéstámogató rendszer...",
        comment="Nagyon részletes válasz, köszönöm!"
    )

    metrics_collector.record_user_feedback(
        message_id="msg_002",
        rating="positive",
        query="Hol van a töltőkábel?",
        response="A töltőkábel a csomagtartóban található..."
    )

    metrics_collector.record_user_feedback(
        message_id="msg_003",
        rating="negative",
        query="Mi a hatótáv?",
        response="A hatótáv körülbelül 500 km.",
        comment="Túl rövid válasz, több részlet kellene."
    )

    print("OK 3 feedback rögzítve\n")

    # Feedback statisztikák lekérdezése
    print("[2] Feedback statisztikak...")
    feedback_stats = metrics_collector.get_feedback_statistics(days=30)

    print(f"Osszes feedback: {feedback_stats['total_feedbacks']}")
    print(f"Pozitiv: {feedback_stats['positive']}")
    print(f"Negativ: {feedback_stats['negative']}")
    print(f"Semleges: {feedback_stats['neutral']}")
    print(f"Elegedettseg: {feedback_stats['satisfaction_score']:.1f}%\n")

    # Analytics tesztelése
    print("[3] Analytics vizualizacio...")
    analytics = Analytics(metrics_collector)

    feedback_dist = analytics.get_feedback_distribution()
    print(f"Feedback eloszlas: {feedback_dist}\n")

    # Teljes statisztikák
    print("[4] Teljes statisztikak (feedback-del)...")
    stats = metrics_collector.get_statistics(days=30)

    if 'feedback' in stats:
        fb = stats['feedback']
        print(f"OK Feedback integrálva a statisztikákba!")
        print(f"   - Total: {fb['total_feedbacks']}")
        print(f"   - Satisfaction: {fb['satisfaction_score']:.1f}%\n")
    else:
        print("ERROR Feedback nincs a statisztikákban!\n")

    print("OK Minden teszt sikeres!")
    print("\n[INFO] Most probalj ki a Streamlit app-ban:")
    print("   streamlit run app.py")
    print("   Adj valaszokat es hasznald a feedback gombokat!")

if __name__ == "__main__":
    test_feedback_system()

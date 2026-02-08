"""
Session kezelés modul
"""

from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Session kezelő osztály"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Új session létrehozása
        
        Args:
            user_id: Felhasználó ID (opcionális)
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'messages': [],
            'documents': []
        }
        
        logger.info(f"Új session létrehozva: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Session lekérdezése"""
        return self.sessions.get(session_id)
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Üzenet hozzáadása a sessionhez
        
        Args:
            session_id: Session ID
            role: Üzenet szerepe ('user' vagy 'assistant')
            content: Üzenet tartalma
            metadata: További metadata
        """
        if session_id not in self.sessions:
            logger.warning(f"Session nem található: {session_id}")
            return
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.sessions[session_id]['messages'].append(message)
        logger.debug(f"Üzenet hozzáadva a {session_id} sessionhez")
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Session üzeneteinek lekérdezése"""
        session = self.get_session(session_id)
        if session:
            return session.get('messages', [])
        return []
    
    def add_document(
        self,
        session_id: str,
        document_id: str,
        document_metadata: Dict[str, Any]
    ):
        """Dokumentum hozzáadása a sessionhez"""
        if session_id not in self.sessions:
            logger.warning(f"Session nem található: {session_id}")
            return
        
        self.sessions[session_id]['documents'].append({
            'document_id': document_id,
            'metadata': document_metadata,
            'added_at': datetime.now().isoformat()
        })
    
    def delete_session(self, session_id: str):
        """Session törlése"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session törölve: {session_id}")
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Session statisztikák"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        messages = session.get('messages', [])
        user_messages = [m for m in messages if m['role'] == 'user']
        assistant_messages = [m for m in messages if m['role'] == 'assistant']
        
        return {
            'session_id': session_id,
            'created_at': session.get('created_at'),
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'documents_count': len(session.get('documents', []))
        }


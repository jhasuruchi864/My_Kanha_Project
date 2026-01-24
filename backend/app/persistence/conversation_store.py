"""
Conversation Store
Simple JSON-based persistence for chat history (MVP).
Easy to migrate to SQLite/Postgres later.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import uuid

from app.logger import logger


# Storage configuration
CONVERSATIONS_DIR = Path("./data/conversations")
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ChatMessage:
    """Single chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str  # ISO format
    sources: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ConversationSession:
    """Represents a complete conversation session."""
    session_id: str
    user_id: str
    created_at: str  # ISO format
    last_updated: str  # ISO format
    language: str = "english"
    messages: Optional[List[ChatMessage]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        messages_list = self.messages if self.messages is not None else []
        data['messages'] = [msg.to_dict() if isinstance(msg, ChatMessage) else msg for msg in messages_list]
        return data
    
    def add_message(self, role: str, content: str, sources: Optional[List] = None) -> ChatMessage:
        """Add a message to the conversation."""
        if self.messages is None:
            self.messages = []
        
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            sources=sources
        )
        self.messages.append(message)
        self.last_updated = datetime.utcnow().isoformat()
        return message
    
    def get_messages_for_context(self, max_messages: int = 5) -> List[Dict]:
        """Get last N messages for LLM context."""
        if not self.messages:
            return []
        
        messages = []
        for msg in self.messages[-max_messages:]:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        return messages


class ConversationStore:
    """JSON-based conversation storage (MVP implementation)."""
    
    @staticmethod
    def _get_user_dir(user_id: str) -> Path:
        """Get directory for user conversations."""
        user_dir = CONVERSATIONS_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    @staticmethod
    def _get_session_file(user_id: str, session_id: str) -> Path:
        """Get file path for a conversation session."""
        user_dir = ConversationStore._get_user_dir(user_id)
        return user_dir / f"{session_id}.json"
    
    @staticmethod
    def create_session(user_id: str, language: str = "english") -> ConversationSession:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_updated=now,
            language=language
        )
        
        # Save immediately
        ConversationStore.save_session(session)
        logger.info(f"Created new session {session_id} for user {user_id}")
        
        return session
    
    @staticmethod
    def save_session(session: ConversationSession) -> None:
        """Save conversation session to JSON file."""
        file_path = ConversationStore._get_session_file(session.user_id, session.session_id)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved session {session.session_id}")
        except Exception as e:
            logger.error(f"Error saving session {session.session_id}: {e}")
            raise
    
    @staticmethod
    def load_session(user_id: str, session_id: str) -> Optional[ConversationSession]:
        """Load conversation session from JSON file."""
        file_path = ConversationStore._get_session_file(user_id, session_id)
        
        if not file_path.exists():
            logger.warning(f"Session file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct ChatMessage objects
            messages = []
            for msg_data in data.get('messages', []):
                messages.append(ChatMessage(
                    role=msg_data['role'],
                    content=msg_data['content'],
                    timestamp=msg_data['timestamp'],
                    sources=msg_data.get('sources')
                ))
            
            session = ConversationSession(
                session_id=data['session_id'],
                user_id=data['user_id'],
                created_at=data['created_at'],
                last_updated=data['last_updated'],
                language=data.get('language', 'english'),
                messages=messages,
                metadata=data.get('metadata', {})
            )
            
            logger.debug(f"Loaded session {session_id}")
            return session
        
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    @staticmethod
    def list_sessions(user_id: str) -> List[Dict[str, Any]]:
        """List all sessions for a user."""
        user_dir = ConversationStore._get_user_dir(user_id)
        sessions_list = []
        
        try:
            for file_path in sorted(user_dir.glob("*.json"), reverse=True):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                sessions_list.append({
                    "session_id": data['session_id'],
                    "created_at": data['created_at'],
                    "last_updated": data['last_updated'],
                    "language": data.get('language', 'english'),
                    "message_count": len(data.get('messages', []))
                })
            
            logger.debug(f"Listed {len(sessions_list)} sessions for user {user_id}")
            return sessions_list
        
        except Exception as e:
            logger.error(f"Error listing sessions for user {user_id}: {e}")
            return []
    
    @staticmethod
    def delete_session(user_id: str, session_id: str) -> bool:
        """Delete a conversation session."""
        file_path = ConversationStore._get_session_file(user_id, session_id)
        
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted session {session_id}")
                return True
            else:
                logger.warning(f"Session file not found: {file_path}")
                return False
        
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    @staticmethod
    def get_or_create_session(user_id: str, session_id: Optional[str] = None) -> ConversationSession:
        """Get existing session or create new one."""
        if session_id:
            session = ConversationStore.load_session(user_id, session_id)
            if session:
                return session
        
        # Create new session
        return ConversationStore.create_session(user_id)
    
    @staticmethod
    def get_user_stats(user_id: str) -> Dict[str, Any]:
        """Get statistics for a user."""
        sessions = ConversationStore.list_sessions(user_id)
        total_messages = 0
        
        for session_info in sessions:
            total_messages += session_info['message_count']
        
        return {
            "user_id": user_id,
            "total_sessions": len(sessions),
            "total_messages": total_messages,
            "storage_location": str(ConversationStore._get_user_dir(user_id))
        }
    
    @staticmethod
    def clear_old_sessions(user_id: str, max_sessions: int = 50) -> int:
        """Keep only the N most recent sessions."""
        sessions = ConversationStore.list_sessions(user_id)
        
        if len(sessions) <= max_sessions:
            return 0
        
        # Sort by created_at and delete old ones
        sessions_to_delete = sessions[max_sessions:]
        deleted_count = 0
        
        for session_info in sessions_to_delete:
            if ConversationStore.delete_session(user_id, session_info['session_id']):
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old sessions for user {user_id}")
        return deleted_count


# Convenience functions

def create_conversation(user_id: str, language: str = "english") -> ConversationSession:
    """Create a new conversation."""
    return ConversationStore.create_session(user_id, language)


def save_conversation(session: ConversationSession) -> None:
    """Save a conversation."""
    ConversationStore.save_session(session)


def load_conversation(user_id: str, session_id: str) -> Optional[ConversationSession]:
    """Load a conversation."""
    return ConversationStore.load_session(user_id, session_id)


def list_conversations(user_id: str) -> List[Dict]:
    """List all conversations for a user."""
    return ConversationStore.list_sessions(user_id)


def delete_conversation(user_id: str, session_id: str) -> bool:
    """Delete a conversation."""
    return ConversationStore.delete_session(user_id, session_id)

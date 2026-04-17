"""
Phase 4: Multi-Thread Chat (Conversational Context Management)
Manages multi-turn conversations with persistent context, session isolation, and context-aware follow-ups.
"""

import os
import json
import hashlib
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path


# =============================================================================
# 4.1 Session Management & Thread Isolation
# =============================================================================

@dataclass
class Message:
    """Message schema for conversation history."""
    message_id: str
    timestamp: str
    role: str  # "user" | "assistant" | "system"
    content: str
    intent: Optional[str] = None
    sources: List[str] = field(default_factory=list)
    retrieved_chunks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(**data)


@dataclass
class SessionMetadata:
    """Session metadata for tracking."""
    session_id: str
    created_at: str
    last_active: str
    message_count: int = 0
    discussed_funds: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SessionManager:
    """Phase 4.1: Session Management & Thread Isolation"""
    
    SESSIONS_DIR = Path("sessions")
    SESSION_EXPIRY_DAYS = 7
    
    def __init__(self):
        self.SESSIONS_DIR.mkdir(exist_ok=True)
        self._cleanup_expired_sessions()
    
    def _get_session_path(self, session_id: str) -> Path:
        """Get path for a specific session directory."""
        return self.SESSIONS_DIR / session_id
    
    def _cleanup_expired_sessions(self):
        """Remove sessions older than SESSION_EXPIRY_DAYS."""
        cutoff = datetime.now() - timedelta(days=self.SESSION_EXPIRY_DAYS)
        for session_dir in self.SESSIONS_DIR.iterdir():
            if session_dir.is_dir():
                meta_file = session_dir / "metadata.json"
                if meta_file.exists():
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        last_active = datetime.fromisoformat(meta.get("last_active", "1970-01-01"))
                        if last_active < cutoff:
                            # Delete expired session
                            for file in session_dir.iterdir():
                                file.unlink()
                            session_dir.rmdir()
                            print(f"Cleaned up expired session: {session_dir.name}")
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session with unique ID."""
        sid = session_id or str(uuid.uuid4())
        session_path = self._get_session_path(sid)
        session_path.mkdir(exist_ok=True)
        
        now = datetime.now().isoformat()
        metadata = SessionMetadata(
            session_id=sid,
            created_at=now,
            last_active=now,
            message_count=0
        )
        
        self._save_metadata(sid, metadata)
        
        # Initialize empty messages file
        messages_file = session_path / "messages.jsonl"
        messages_file.touch()
        
        return sid
    
    def _save_metadata(self, session_id: str, metadata: SessionMetadata):
        """Save session metadata to file."""
        session_path = self._get_session_path(session_id)
        session_path.mkdir(parents=True, exist_ok=True)
        
        meta_file = session_path / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, indent=2)
    
    def get_metadata(self, session_id: str) -> Optional[SessionMetadata]:
        """Get session metadata."""
        meta_file = self._get_session_path(session_id) / "metadata.json"
        if not meta_file.exists():
            return None
        
        with open(meta_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return SessionMetadata(**data)
    
    def add_message(self, session_id: str, message: Message):
        """Add a message to the session history."""
        session_path = self._get_session_path(session_id)
        session_path.mkdir(parents=True, exist_ok=True)
        
        # Append to messages.jsonl
        messages_file = session_path / "messages.jsonl"
        with open(messages_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(message.to_dict()) + "\n")
        
        # Update metadata
        metadata = self.get_metadata(session_id)
        if metadata:
            metadata.message_count += 1
            metadata.last_active = datetime.now().isoformat()
            
            # Track discussed funds from retrieved chunks
            for chunk_id in message.retrieved_chunks:
                # Extract fund name from chunk_id (format: "{scheme_name}_{section_type}")
                fund_name = chunk_id.split("_")[0] if "_" in chunk_id else chunk_id
                if fund_name and fund_name not in metadata.discussed_funds:
                    metadata.discussed_funds.append(fund_name)
            
            self._save_metadata(session_id, metadata)
    
    def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get all messages for a session, optionally limited to last N."""
        messages_file = self._get_session_path(session_id) / "messages.jsonl"
        if not messages_file.exists():
            return []
        
        messages = []
        with open(messages_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    messages.append(Message.from_dict(json.loads(line)))
        
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def clear_session(self, session_id: str) -> str:
        """Clear all messages but keep session ID (creates new session with same ID)."""
        session_path = self._get_session_path(session_id)
        
        # Delete old messages
        messages_file = session_path / "messages.jsonl"
        if messages_file.exists():
            messages_file.unlink()
        
        # Reset metadata
        now = datetime.now().isoformat()
        metadata = SessionMetadata(
            session_id=session_id,
            created_at=now,
            last_active=now,
            message_count=0,
            discussed_funds=[]
        )
        self._save_metadata(session_id, metadata)
        
        # Create new empty messages file
        messages_file.touch()
        
        return session_id
    
    def delete_session(self, session_id: str):
        """Permanently delete a session."""
        session_path = self._get_session_path(session_id)
        if session_path.exists():
            for file in session_path.iterdir():
                file.unlink()
            session_path.rmdir()


# =============================================================================
# 4.2 Context Window Management
# =============================================================================

class ContextWindowManager:
    """Phase 4.2: Manages conversation context within LLM token limits."""
    
    # Token budgets (approximate)
    TOKEN_BUDGETS = {
        "system_prompt": 200,
        "retrieved_context": 1000,
        "recent_messages": 1000,
        "context_summary": 300,
        "response_buffer": 1500,
    }
    MAX_CONTEXT_TOKENS = 3000
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.llm = None  # Will be initialized if summarization needed
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters for English)."""
        return len(text) // 4
    
    def build_context(
        self,
        session_id: str,
        system_prompt: str,
        retrieved_context: str,
        current_query: str
    ) -> str:
        """
        Build conversation context respecting token limits.
        Returns assembled context string.
        """
        messages = self.session_manager.get_messages(session_id)
        
        if not messages:
            # No history, just use current context
            return f"{system_prompt}\n\nContext:\n{retrieved_context}\n\nUser: {current_query}"
        
        # Calculate current token usage
        system_tokens = self._estimate_tokens(system_prompt)
        retrieved_tokens = self._estimate_tokens(retrieved_context)
        query_tokens = self._estimate_tokens(current_query)
        
        # Available tokens for conversation history
        available_tokens = self.MAX_CONTEXT_TOKENS - system_tokens - retrieved_tokens - query_tokens
        
        # Build recent messages context
        recent_messages_text = ""
        total_msg_tokens = 0
        
        # Include messages from newest to oldest until we hit the limit
        for msg in reversed(messages):
            msg_text = f"{msg.role.capitalize()}: {msg.content}\n"
            msg_tokens = self._estimate_tokens(msg_text)
            
            if total_msg_tokens + msg_tokens > self.TOKEN_BUDGETS["recent_messages"]:
                break
            
            recent_messages_text = msg_text + recent_messages_text
            total_msg_tokens += msg_tokens
        
        # Check if we need summarization (total context too large)
        total_tokens = system_tokens + retrieved_tokens + total_msg_tokens + query_tokens
        
        if total_tokens > self.MAX_CONTEXT_TOKENS and len(messages) > 5:
            # Trigger summarization for older messages
            summary = self._summarize_old_messages(messages[:-5])
            
            # Rebuild with summary instead of full old messages
            context_parts = [
                system_prompt,
                f"\nPrevious Conversation Summary: {summary}",
                f"\nRecent Messages:\n{recent_messages_text}",
                f"\nContext:\n{retrieved_context}",
                f"\nUser: {current_query}"
            ]
        else:
            context_parts = [
                system_prompt,
                f"\nConversation History:\n{recent_messages_text}",
                f"\nContext:\n{retrieved_context}",
                f"\nUser: {current_query}"
            ]
        
        return "\n".join(context_parts)
    
    def _summarize_old_messages(self, old_messages: List[Message]) -> str:
        """Summarize older messages to preserve key facts."""
        # Simple extraction-based summarization (can be enhanced with LLM)
        funds_mentioned = set()
        key_facts = []
        
        for msg in old_messages:
            if msg.role == "user":
                # Extract fund names mentioned
                for chunk in msg.retrieved_chunks:
                    fund = chunk.split("_")[0] if "_" in chunk else None
                    if fund:
                        funds_mentioned.add(fund)
            elif msg.role == "assistant":
                # Look for key factual statements (short ones)
                if len(msg.content) < 200 and any(x in msg.content for x in ["NAV", "AUM", "expense", "manager"]):
                    key_facts.append(msg.content[:100])
        
        summary_parts = []
        if funds_mentioned:
            summary_parts.append(f"Previously discussed: {', '.join(funds_mentioned)}.")
        if key_facts:
            summary_parts.append(f"Key facts mentioned: {'; '.join(key_facts[:3])}")
        
        return " ".join(summary_parts) if summary_parts else "Previous discussion about HDFC mutual funds."


# =============================================================================
# 4.3 Context-Aware Query Enhancement
# =============================================================================

class QueryEnhancer:
    """Phase 4.3: Enhances queries using conversation context."""
    
    # Pronouns and references to resolve
    COREFERENCE_PATTERNS = [
        (r"\bit\b", "last_fund"),
        (r"\bthat\s+fund\b", "last_fund"),
        (r"\bthis\s+(?:fund|one)\b", "last_fund"),
        (r"\bthe\s+(?:fund|scheme)\b", "last_fund"),
        (r"\bits\b", "last_fund_possessive"),
    ]
    
    # Partial fund name patterns
    FUND_TYPE_PATTERNS = {
        "small cap": "HDFC Small Cap Fund",
        "mid cap": "HDFC Mid Cap Fund",
        "multi cap": "HDFC Multi Cap Fund",
        "defence": "HDFC Defence Fund",
        "balanced": "HDFC Balanced Advantage Fund",
        "nifty": "HDFC Nifty 50 Index Fund",
        "gold": "HDFC Gold ETF Fund of Fund",
        "silver": "HDFC Silver ETF FoF",
        "equity": "HDFC Equity Fund",
        "short term": "HDFC Short Term Opportunities Fund",
    }
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    def _get_last_discussed_fund(self, session_id: str) -> Optional[str]:
        """Get the most recently discussed fund in the session."""
        metadata = self.session_manager.get_metadata(session_id)
        if metadata and metadata.discussed_funds:
            return metadata.discussed_funds[-1]
        
        # Fallback: scan recent messages
        messages = self.session_manager.get_messages(session_id, limit=5)
        for msg in reversed(messages):
            for chunk in msg.retrieved_chunks:
                fund = chunk.split("_")[0] if "_" in chunk else None
                if fund:
                    return fund
        
        return None
    
    def enhance_query(self, query: str, session_id: str) -> Tuple[str, bool]:
        """
        Enhance query with context. Returns (enhanced_query, was_modified).
        """
        original_query = query
        last_fund = self._get_last_discussed_fund(session_id)
        
        if not last_fund:
            return query, False
        
        query_lower = query.lower()
        
        # Check for coreference patterns
        for pattern, ref_type in self.COREFERENCE_PATTERNS:
            import re
            if re.search(pattern, query_lower):
                # Replace pronoun with fund name
                if ref_type == "last_fund_possessive":
                    query = re.sub(pattern, f"{last_fund}'s", query, flags=re.IGNORECASE)
                else:
                    query = re.sub(pattern, last_fund, query, flags=re.IGNORECASE)
                break
        
        # Check for partial fund references
        for partial, full_name in self.FUND_TYPE_PATTERNS.items():
            # Only replace if query contains partial but not full name
            if partial in query_lower and full_name.lower() not in query_lower:
                # Check if it's a standalone reference (preceded by "the" or at start)
                pattern = rf"(?:the\s+)?{partial}(?:\s+fund|scheme)?"
                if re.search(pattern, query_lower):
                    query = re.sub(pattern, full_name, query, flags=re.IGNORECASE)
                    break
        
        # Handle ambiguous follow-ups like "what about..."
        ambiguous_starters = ["what about", "how about", "tell me about", "what is"]
        if any(query_lower.strip().startswith(s) for s in ambiguous_starters):
            # If query doesn't mention any fund, assume it's about last fund
            has_fund = any(full.lower() in query_lower for full in self.FUND_TYPE_PATTERNS.values())
            has_fund = has_fund or "hdfc" in query_lower
            
            if not has_fund and last_fund:
                # Prepend the fund name
                query = f"{query} of {last_fund}"
        
        was_modified = query != original_query
        if was_modified:
            print(f"  -> Query enhanced: '{original_query}' -> '{query}'")
        
        return query, was_modified
    
    def needs_disambiguation(self, query: str, session_id: str) -> bool:
        """Check if query is too ambiguous to answer."""
        metadata = self.session_manager.get_metadata(session_id)
        
        # If multiple funds discussed and query has no clear reference
        if metadata and len(metadata.discussed_funds) >= 2:
            query_lower = query.lower()
            has_specific_ref = any(
                fund.lower() in query_lower 
                for fund in metadata.discussed_funds
            )
            
            # Check for pronouns that could be ambiguous
            ambiguous_refs = ["it", "that", "this"]
            has_ambiguous = any(r in query_lower.split() for r in ambiguous_refs)
            
            if has_ambiguous and not has_specific_ref:
                return True
        
        return False


# =============================================================================
# 4.4 Multi-Turn RAG Strategy
# =============================================================================

class MultiTurnRAGStrategy:
    """Phase 4.4: Adapts retrieval based on conversation flow."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    def get_retrieval_strategy(
        self,
        query: str,
        session_id: str,
        intent: str
    ) -> Dict[str, Any]:
        """
        Determine retrieval strategy based on conversation context.
        Returns dict with strategy parameters.
        """
        metadata = self.session_manager.get_metadata(session_id)
        messages = self.session_manager.get_messages(session_id)
        
        strategy = {
            "mode": "fresh",  # default
            "fund_filter": None,
            "force_refresh": False,
            "block_retrieval": False,
            "block_reason": None,
        }
        
        # Block comparison queries after individual fund discussions
        if intent == "ADVISORY" and metadata and len(metadata.discussed_funds) >= 2:
            if any(kw in query.lower() for kw in ["compare", "better", "which"]):
                strategy["block_retrieval"] = True
                strategy["block_reason"] = "Comparison after individual fund queries - advisory blocked"
                return strategy
        
        # Check for temporal awareness queries
        temporal_keywords = ["changed", "latest", "updated", "now", "current"]
        if any(kw in query.lower() for kw in temporal_keywords):
            strategy["force_refresh"] = True
        
        # If this is a follow-up (previous messages exist)
        if messages and intent == "FACTUAL":
            last_message = messages[-1]
            
            # Check if query is about same fund as last turn
            if metadata and metadata.discussed_funds:
                last_fund = metadata.discussed_funds[-1]
                
                # If query doesn't mention other funds, narrow to last fund
                query_lower = query.lower()
                other_funds = [f for f in metadata.discussed_funds[:-1] if f.lower() in query_lower]
                
                if not other_funds:
                    strategy["mode"] = "follow_up"
                    strategy["fund_filter"] = last_fund
        
        return strategy
    
    def get_previous_chunk_ids(self, session_id: str) -> List[str]:
        """Get list of chunk IDs already used in this session (for deduplication)."""
        messages = self.session_manager.get_messages(session_id)
        chunk_ids = []
        for msg in messages:
            chunk_ids.extend(msg.retrieved_chunks)
        return list(set(chunk_ids))  # Remove duplicates


# =============================================================================
# 4.5 Persistent Storage & Recovery (with export functionality)
# =============================================================================

class ConversationExporter:
    """Phase 4.5: Export and backup conversation history."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.exports_dir = Path("exports")
        self.exports_dir.mkdir(exist_ok=True)
    
    def export_to_json(self, session_id: str) -> str:
        """Export session to JSON file. Returns file path."""
        messages = self.session_manager.get_messages(session_id)
        metadata = self.session_manager.get_metadata(session_id)
        
        export_data = {
            "session_id": session_id,
            "exported_at": datetime.now().isoformat(),
            "metadata": metadata.to_dict() if metadata else {},
            "messages": [msg.to_dict() for msg in messages]
        }
        
        filename = f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.exports_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def export_to_markdown(self, session_id: str) -> str:
        """Export session to Markdown file. Returns file path."""
        messages = self.session_manager.get_messages(session_id)
        metadata = self.session_manager.get_metadata(session_id)
        
        lines = [
            f"# Chat Session: {session_id}",
            f"",
            f"**Created:** {metadata.created_at if metadata else 'Unknown'}",
            f"**Messages:** {len(messages)}",
            f"**Discussed Funds:** {', '.join(metadata.discussed_funds) if metadata and metadata.discussed_funds else 'None'}",
            f"",
            f"---",
            f"",
        ]
        
        for msg in messages:
            timestamp = datetime.fromisoformat(msg.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"**{msg.role.capitalize()}** ({timestamp}):")
            lines.append(f"{msg.content}")
            if msg.sources:
                lines.append(f"*Sources: {', '.join(msg.sources)}*")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("*Generated by HDFC Mutual Fund RAG Assistant*")
        
        filename = f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.exports_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        return str(filepath)


# =============================================================================
# Unified Conversation Manager Interface
# =============================================================================

class ConversationManager:
    """
    Unified interface for all Phase 4 components.
    Provides: Session Management, Context Windows, Query Enhancement, RAG Strategy, Export
    """
    
    def __init__(self):
        self.sessions = SessionManager()
        self.context = ContextWindowManager(self.sessions)
        self.enhancer = QueryEnhancer(self.sessions)
        self.rag_strategy = MultiTurnRAGStrategy(self.sessions)
        self.exporter = ConversationExporter(self.sessions)
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new conversation session."""
        return self.sessions.create_session(session_id)
    
    def enhance_query(self, query: str, session_id: str) -> Tuple[str, bool]:
        """Enhance query with conversation context."""
        return self.enhancer.enhance_query(query, session_id)
    
    def needs_disambiguation(self, query: str, session_id: str) -> bool:
        """Check if query needs disambiguation."""
        return self.enhancer.needs_disambiguation(query, session_id)
    
    def get_retrieval_strategy(self, query: str, session_id: str, intent: str) -> Dict[str, Any]:
        """Get retrieval strategy for this turn."""
        return self.rag_strategy.get_retrieval_strategy(query, session_id, intent)
    
    def log_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: Optional[str] = None,
        sources: List[str] = None,
        retrieved_chunks: List[str] = None
    ):
        """Log a message to the conversation history."""
        message = Message(
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            role=role,
            content=content,
            intent=intent,
            sources=sources or [],
            retrieved_chunks=retrieved_chunks or []
        )
        self.sessions.add_message(session_id, message)
    
    def get_session_history(self, session_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get conversation history."""
        return self.sessions.get_messages(session_id, limit)
    
    def build_context(
        self,
        session_id: str,
        system_prompt: str,
        retrieved_context: str,
        current_query: str
    ) -> str:
        """Build full context for LLM generation."""
        return self.context.build_context(session_id, system_prompt, retrieved_context, current_query)
    
    def clear_session(self, session_id: str) -> str:
        """Clear session history but keep session ID."""
        return self.sessions.clear_session(session_id)
    
    def delete_session(self, session_id: str):
        """Permanently delete a session."""
        self.sessions.delete_session(session_id)
    
    def export_session(self, session_id: str, format: str = "json") -> str:
        """Export session to file. Returns file path."""
        if format == "json":
            return self.exporter.export_to_json(session_id)
        elif format == "markdown":
            return self.exporter.export_to_markdown(session_id)
        else:
            raise ValueError(f"Unsupported export format: {format}")


if __name__ == "__main__":
    # Test Phase 4 implementation
    print("Testing Phase 4: Multi-Thread Chat\n")
    
    cm = ConversationManager()
    
    # Create session
    session_id = cm.create_session()
    print(f"Created session: {session_id}")
    
    # Simulate conversation
    queries = [
        ("user", "What is the NAV of HDFC Small Cap Fund?", "FACTUAL"),
        ("assistant", "The NAV of HDFC Small Cap Fund is ₹120.50 as of today.", "FACTUAL"),
        ("user", "What about its exit load?", "FACTUAL"),  # Ambiguous - should be enhanced
        ("assistant", "The exit load is 1% if redeemed within 1 year.", "FACTUAL"),
    ]
    
    for role, content, intent in queries:
        if role == "user":
            # Test query enhancement
            enhanced, modified = cm.enhance_query(content, session_id)
            if modified:
                print(f"Enhanced query: '{content}' -> '{enhanced}'")
            content = enhanced
        
        # Log message
        cm.log_message(
            session_id=session_id,
            role=role,
            content=content,
            intent=intent,
            retrieved_chunks=["HDFC Small Cap Fund_key_metrics"] if role == "assistant" else []
        )
        print(f"Logged {role}: {content[:50]}...")
    
    # Get history
    history = cm.get_session_history(session_id)
    print(f"\nSession has {len(history)} messages")
    
    # Export
    json_path = cm.export_session(session_id, "json")
    md_path = cm.export_session(session_id, "markdown")
    print(f"\nExported to:\n  - {json_path}\n  - {md_path}")
    
    # Cleanup
    cm.delete_session(session_id)
    print(f"\nDeleted session: {session_id}")

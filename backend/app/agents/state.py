"""
AgentState definition for the LangGraph orchestration.
Represents the shared state that flows through all agents.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class AgentState:
    # Identity
    user_id: str

    # User preferences
    explicit_categories: List[str] = field(default_factory=list)
    keywords_topics: List[str] = field(default_factory=list)
    preferred_sources: List[str] = field(default_factory=list)
    blocked_sources: List[str] = field(default_factory=list)
    tracked_entities: List[Dict[str, Any]] = field(default_factory=list)
    user_feedback: List[Dict[str, Any]] = field(default_factory=list)
    implicit_preferences: Dict[str, float] = field(default_factory=dict)

    # Reading history
    reading_history: List[Dict[str, Any]] = field(default_factory=list)

    # Agent outputs
    discovered_articles: List[Dict[str, Any]] = field(default_factory=list)
    synthesized_articles: List[Dict[str, Any]] = field(default_factory=list)
    article_analysis: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Orchestration
    current_node: str = "start"
    current_query: Optional[str] = None
    selected_articles_for_digest: List[Dict[str, Any]] = field(default_factory=list)
    agent_outputs: Dict[str, Any] = field(default_factory=dict)

    # Error handling
    error_message: Optional[str] = None

    # Timestamps
    last_run_times: Dict[str, datetime] = field(default_factory=dict)

"""
Devil's Advocate Agent: Analyzes articles for bias, missing perspectives,
and provides source bias indicators. Uses LLM for nuanced analysis.
"""
import json
import logging
from typing import Any, Dict

from app.agents.state import AgentState
from app.db.session import SessionLocal
from app.db.crud import get_all_source_biases
from app.core.llm import get_llm

logger = logging.getLogger(__name__)

# Default bias map (used when DB is empty or unavailable)
DEFAULT_BIAS_MAP = {
    "foxnews.com": "conservative",
    "breitbart.com": "conservative",
    "nytimes.com": "liberal",
    "washingtonpost.com": "liberal",
    "cnn.com": "liberal",
    "bbc.com": "neutral",
    "reuters.com": "neutral",
    "apnews.com": "neutral",
    "npr.org": "neutral",
    "wsj.com": "conservative",
    "theguardian.com": "liberal",
    "bloomberg.com": "neutral",
    "economist.com": "neutral",
}


def _load_bias_map() -> Dict[str, str]:
    """Load bias map from database, falling back to defaults."""
    try:
        db = SessionLocal()
        db_biases = get_all_source_biases(db)
        if db_biases:
            merged = {**DEFAULT_BIAS_MAP, **db_biases}
            return merged
    except Exception as e:
        logger.warning(f"Could not load biases from DB: {e}")
    finally:
        if 'db' in locals():
            db.close()
    return dict(DEFAULT_BIAS_MAP)


def _detect_bias(source_url: str, bias_map: Dict[str, str]) -> str:
    """Detect source bias based on domain."""
    for domain, bias in bias_map.items():
        if domain in source_url.lower():
            return bias
    return "unknown"


async def _llm_analyze_perspectives(title: str, content: str) -> Dict[str, Any]:
    """Use LLM to identify present and missing perspectives."""
    llm = get_llm()
    prompt = (
        f"Article title: {title}\n"
        f"Article content (first 3000 chars): {(content or '')[:3000]}\n\n"
        "Analyze this article for perspectives and bias. Respond in JSON format:\n"
        "{\n"
        '  "present_perspectives": ["economic", "social", ...],\n'
        '  "missing_perspectives": ["perspectives not covered"],\n'
        '  "bias_warning": "brief note about any framing bias or null"\n'
        "}\n\n"
        "Choose from: economic, social, political, environmental, technological, health, cultural, legal"
    )
    result = await llm.generate(prompt, max_tokens=300, temperature=0.3)

    # Fallback
    if result.startswith("[LLM unavailable"):
        return {"present_perspectives": [], "missing_perspectives": [], "bias_warning": None}

    try:
        # Extract JSON from response (handle markdown-wrapped JSON)
        json_str = result.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        analysis = json.loads(json_str)
        return {
            "present_perspectives": analysis.get("present_perspectives", []),
            "missing_perspectives": analysis.get("missing_perspectives", []),
            "bias_warning": analysis.get("bias_warning"),
        }
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse LLM perspective analysis: {e}")
        return {"present_perspectives": [], "missing_perspectives": [], "bias_warning": None}


async def perspective_agent(state: AgentState) -> Dict[str, Any]:
    """Analyze articles for bias and provide multi-perspective insights."""
    logger.info(f"Perspective agent analyzing {len(state.synthesized_articles)} articles")

    bias_map = _load_bias_map()
    analysis = {}

    for article in state.synthesized_articles:
        article_id = article.get("id", "")
        source_url = article.get("source_url", "")
        title = article.get("title", "")
        content = article.get("content", "")

        # Source-based bias detection
        article["bias_rating"] = _detect_bias(source_url, bias_map)

        # LLM-powered perspective analysis
        llm_analysis = await _llm_analyze_perspectives(title, content)

        analysis[article_id] = {
            "bias": article["bias_rating"],
            "present_perspectives": llm_analysis["present_perspectives"],
            "missing_perspectives": llm_analysis["missing_perspectives"],
            "bias_warning": llm_analysis["bias_warning"],
        }

        logger.debug(f"Article {article_id}: bias={article['bias_rating']}, "
                     f"perspectives={llm_analysis['present_perspectives']}")

    return {
        "article_analysis": analysis,
        "current_node": "connection_agent",
    }
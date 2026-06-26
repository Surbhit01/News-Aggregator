"""
Synthesizer Agent: Condenses articles into digestible summaries.
Uses LLM for high-quality TL;DR, key takeaways, and reading time estimates.
"""
import logging
import re
from typing import Any, Dict

from app.agents.state import AgentState
from app.core.llm import get_llm

logger = logging.getLogger(__name__)


def _estimate_read_time(text: str) -> int:
    """Estimate reading time in minutes (avg 200 wpm)."""
    word_count = len(re.findall(r'\w+', text or ""))
    return max(1, round(word_count / 200))


async def _generate_tldr_llm(title: str, content: str) -> str:
    """Generate a single-sentence TL;DR using LLM."""
    if not content:
        return f"Article about {title}"

    llm = get_llm()
    prompt = (
        f"Article title: {title}\n"
        f"Article content (first 2000 chars): {content[:2000]}\n\n"
        "Write a single concise sentence (max 30 words) summarizing the key point of this article."
    )
    result = await llm.generate(prompt, max_tokens=80, temperature=0.3)
    # Fallback if LLM fails
    if result.startswith("[LLM unavailable"):
        sentences = content.replace("\n", " ").split(".")
        for s in sentences:
            s = s.strip()
            if len(s) > 20:
                return s[:150] + ("..." if len(s) > 150 else "")
        return f"Summary of: {title}"
    return result.strip()


async def _generate_key_takeaways_llm(title: str, content: str) -> list:
    """Generate 3 key bullet-point takeaways using LLM."""
    if not content:
        return [f"Article discusses {title}"]

    llm = get_llm()
    prompt = (
        f"Article title: {title}\n"
        f"Article content (first 2500 chars): {content[:2500]}\n\n"
        "Extract exactly 3 key takeaways from this article. "
        "Format as a bullet list with each point on a new line starting with '- '."
    )
    result = await llm.generate(prompt, max_tokens=250, temperature=0.3)

    # Fallback if LLM fails — extractive from content
    if result.startswith("[LLM unavailable"):
        sentences = [s.strip() for s in content.replace("\n", " ").split(".") if len(s.strip()) > 40]
        takeaways = [s[:120] for s in sentences[:3]]
        # If not enough sentences, use distinct parts of the content
        if len(takeaways) < 3:
            words = content.split()
            chunk_size = max(len(words) // 3, 10)
            for i in range(3 - len(takeaways)):
                chunk = " ".join(words[i * chunk_size:(i + 1) * chunk_size])
                if chunk and len(chunk) > 20:
                    takeaways.append(chunk[:120])
                else:
                    takeaways.append(f"Key point {i + 1}: {title}")
        return takeaways

    # Parse bullet points from LLM response
    takeaways = []
    for line in result.split("\n"):
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            takeaways.append(line[2:].strip())
        elif line.startswith("-") or line.startswith("*"):
            takeaways.append(line[1:].strip())

    # Ensure exactly 3 takeaways
    while len(takeaways) < 3:
        takeaways.append(f"Key insight about {title}")
    return takeaways[:3]


async def synthesizer_agent(state: AgentState) -> Dict[str, Any]:
    """Synthesize articles: add AI-generated summaries, TL;DR, takeaways, reading time."""
    logger.info(f"Synthesizer agent processing {len(state.discovered_articles)} articles")

    synthesized = []
    for article in state.discovered_articles:
        title = article.get("title", "Untitled")
        content = article.get("content") or article.get("summary", "")

        # Generate LLM-enhanced summaries
        article["tl_dr"] = await _generate_tldr_llm(title, content)
        article["key_takeaways"] = await _generate_key_takeaways_llm(title, content)
        article["estimated_read_time_minutes"] = _estimate_read_time(content)
        synthesized.append(article)

    logger.info(f"Synthesized {len(synthesized)} articles with LLM summaries")
    return {
        "synthesized_articles": synthesized,
        "current_node": "perspective_agent",
    }
"""
Safety Rules
Guardrails to keep conversations within appropriate bounds.
"""

import re
from dataclasses import dataclass
from typing import List, Set

from app.logger import logger


@dataclass
class SafetyResult:
    """Result of safety check."""
    is_safe: bool
    reason: str = ""
    safe_response: str = ""


# Topics that should be redirected to Gita wisdom
OFF_TOPIC_KEYWORDS: Set[str] = {
    # Violence/harm
    "kill", "murder", "suicide", "harm", "hurt", "attack", "weapon",
    # Inappropriate content
    "sex", "porn", "nude", "explicit",
    # Other religions (redirect respectfully)
    "bible", "quran", "jesus", "allah", "buddha",
    # Political
    "politics", "election", "vote", "party", "government",
    # Technical/unrelated
    "code", "programming", "software", "computer", "algorithm",
    # Financial advice
    "stock", "invest", "crypto", "bitcoin", "trading",
}

# Patterns that might indicate harmful intent
HARMFUL_PATTERNS: List[str] = [
    r"how\s+to\s+(kill|harm|hurt)",
    r"ways\s+to\s+(die|end\s+life)",
    r"tell\s+me\s+about\s+(other\s+religions?|politics)",
]

# Safe redirect responses
REDIRECT_RESPONSES = {
    "harmful": (
        "Dear seeker, I sense pain in your words. Know that every soul is precious "
        "and eternal. As I told Arjuna, 'The soul is neither born, nor does it die.' "
        "Let us talk about finding peace and purpose. What troubles your heart?"
    ),
    "off_topic": (
        "Dear seeker, while that is beyond my realm of guidance, I am here to help "
        "you navigate life's challenges through the wisdom of the Gita. What aspects "
        "of dharma, purpose, or inner peace may I help you explore?"
    ),
    "other_religion": (
        "All paths that lead to truth are worthy of respect. However, my guidance "
        "flows from the Bhagavad Gita. I am happy to share this wisdom with you. "
        "What questions about life, duty, or spiritual growth do you have?"
    ),
    "technical": (
        "My wisdom lies in the realm of dharma and spiritual guidance, not technical "
        "matters. Perhaps I can help you find balance and peace amidst your work? "
        "The Gita teaches how to act with dedication yet remain unattached to results."
    ),
}


def check_safety(message: str) -> SafetyResult:
    """
    Check if a message is safe and appropriate for the Krishna chatbot.

    Args:
        message: User's input message

    Returns:
        SafetyResult with safety status and any redirect response
    """
    message_lower = message.lower()

    # Check for harmful patterns
    for pattern in HARMFUL_PATTERNS:
        if re.search(pattern, message_lower):
            logger.warning(f"Harmful pattern detected: {pattern}")
            return SafetyResult(
                is_safe=False,
                reason="harmful_content",
                safe_response=REDIRECT_RESPONSES["harmful"],
            )

    # Check for off-topic keywords
    words = set(re.findall(r'\b\w+\b', message_lower))
    off_topic_found = words.intersection(OFF_TOPIC_KEYWORDS)

    if off_topic_found:
        # Determine the type of off-topic content
        if any(word in off_topic_found for word in ["bible", "quran", "jesus", "allah", "buddha"]):
            return SafetyResult(
                is_safe=False,
                reason="other_religion",
                safe_response=REDIRECT_RESPONSES["other_religion"],
            )
        elif any(word in off_topic_found for word in ["code", "programming", "software", "computer", "algorithm"]):
            return SafetyResult(
                is_safe=False,
                reason="technical",
                safe_response=REDIRECT_RESPONSES["technical"],
            )
        elif any(word in off_topic_found for word in ["kill", "murder", "suicide", "harm", "hurt"]):
            return SafetyResult(
                is_safe=False,
                reason="harmful_content",
                safe_response=REDIRECT_RESPONSES["harmful"],
            )
        else:
            logger.info(f"Off-topic keywords found: {off_topic_found}")
            return SafetyResult(
                is_safe=False,
                reason="off_topic",
                safe_response=REDIRECT_RESPONSES["off_topic"],
            )

    return SafetyResult(is_safe=True)


def sanitize_input(message: str) -> str:
    """
    Sanitize user input by removing potentially harmful characters.

    Args:
        message: Raw user input

    Returns:
        Sanitized message
    """
    # Remove any HTML/script tags
    message = re.sub(r'<[^>]+>', '', message)

    # Remove excessive whitespace
    message = ' '.join(message.split())

    # Limit length
    max_length = 2000
    if len(message) > max_length:
        message = message[:max_length]

    return message.strip()

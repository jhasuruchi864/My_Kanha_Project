"""
Safety Rules
Guardrails to keep conversations within appropriate bounds.
"""

import re
from dataclasses import dataclass
from typing import List, Set, Dict, Tuple
from enum import Enum

from app.logger import logger


class ContentSeverity(Enum):
    """Severity levels for content."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ContentCategory(Enum):
    """Categories of content issues."""
    SAFE = "safe"
    HARMFUL = "harmful"
    OFF_TOPIC = "off_topic"
    OTHER_RELIGION = "other_religion"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    POLITICAL = "political"
    INAPPROPRIATE = "inappropriate"


@dataclass
class SafetyResult:
    """Result of safety check."""
    is_safe: bool
    reason: str = ""
    safe_response: str = ""
    severity: ContentSeverity = ContentSeverity.SAFE
    category: ContentCategory = ContentCategory.SAFE
    confidence: float = 1.0  # 0.0 to 1.0
    detected_keywords: List[str] = None
    sentiment_score: float = 0.0  # -1.0 to 1.0, negative = harmful

    def __post_init__(self):
        if self.detected_keywords is None:
            self.detected_keywords = []



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

# Nuanced keyword scoring for better context awareness
KEYWORD_SEVERITY: Dict[str, Tuple[ContentSeverity, ContentCategory]] = {
    # High severity - harmful
    "kill": (ContentSeverity.HIGH, ContentCategory.HARMFUL),
    "murder": (ContentSeverity.HIGH, ContentCategory.HARMFUL),
    "suicide": (ContentSeverity.HIGH, ContentCategory.HARMFUL),
    "poison": (ContentSeverity.HIGH, ContentCategory.HARMFUL),
    "weapon": (ContentSeverity.HIGH, ContentCategory.HARMFUL),
    "bomb": (ContentSeverity.HIGH, ContentCategory.HARMFUL),
    "attack": (ContentSeverity.MEDIUM, ContentCategory.HARMFUL),
    "hurt": (ContentSeverity.MEDIUM, ContentCategory.HARMFUL),
    "harm": (ContentSeverity.MEDIUM, ContentCategory.HARMFUL),
    
    # Inappropriate
    "sex": (ContentSeverity.MEDIUM, ContentCategory.INAPPROPRIATE),
    "porn": (ContentSeverity.HIGH, ContentCategory.INAPPROPRIATE),
    "nude": (ContentSeverity.MEDIUM, ContentCategory.INAPPROPRIATE),
    "explicit": (ContentSeverity.MEDIUM, ContentCategory.INAPPROPRIATE),
    
    # Other religions
    "bible": (ContentSeverity.LOW, ContentCategory.OTHER_RELIGION),
    "quran": (ContentSeverity.LOW, ContentCategory.OTHER_RELIGION),
    "jesus": (ContentSeverity.LOW, ContentCategory.OTHER_RELIGION),
    "allah": (ContentSeverity.LOW, ContentCategory.OTHER_RELIGION),
    "buddha": (ContentSeverity.LOW, ContentCategory.OTHER_RELIGION),
    
    # Technical
    "code": (ContentSeverity.LOW, ContentCategory.TECHNICAL),
    "programming": (ContentSeverity.LOW, ContentCategory.TECHNICAL),
    "software": (ContentSeverity.LOW, ContentCategory.TECHNICAL),
    "algorithm": (ContentSeverity.LOW, ContentCategory.TECHNICAL),
    
    # Financial
    "stock": (ContentSeverity.LOW, ContentCategory.FINANCIAL),
    "invest": (ContentSeverity.LOW, ContentCategory.FINANCIAL),
    "crypto": (ContentSeverity.LOW, ContentCategory.FINANCIAL),
    "bitcoin": (ContentSeverity.LOW, ContentCategory.FINANCIAL),
    "trading": (ContentSeverity.LOW, ContentCategory.FINANCIAL),
    
    # Political
    "politics": (ContentSeverity.LOW, ContentCategory.POLITICAL),
    "election": (ContentSeverity.LOW, ContentCategory.POLITICAL),
    "vote": (ContentSeverity.LOW, ContentCategory.POLITICAL),
    "party": (ContentSeverity.LOW, ContentCategory.POLITICAL),
    "government": (ContentSeverity.LOW, ContentCategory.POLITICAL),
}

# Positive sentiment indicators (for context-aware filtering)
POSITIVE_INDICATORS: Set[str] = {
    "help", "understand", "learn", "wisdom", "peace", "dharma", "duty",
    "purpose", "meaning", "spiritual", "growth", "enlightenment",
}

# Safe redirect responses - warm and friendly tone
REDIRECT_RESPONSES = {
    "harmful": (
        "Hey, I can sense something heavy in your words, and I want you to know - "
        "you matter. Every soul is precious and eternal. If you're going through "
        "a tough time, I'm here to listen. What's really on your mind, my friend?"
    ),
    "off_topic": (
        "Ah, that's a bit outside my wheelhouse! I'm better at the life stuff - "
        "finding peace, dealing with stress, figuring out your path. "
        "Is there something on your mind I could actually help with?"
    ),
    "other_religion": (
        "I have deep respect for all paths to truth! My expertise is the Gita's wisdom, "
        "but the core of all spiritual teachings often overlaps. What life question "
        "or challenge can I help you think through?"
    ),
    "technical": (
        "Ha! Code and algorithms aren't really my thing - I'm more of a 'meaning of life' "
        "kind of guide. But if work stress is getting to you, or you're struggling with "
        "motivation - now THAT I can help with. What's going on?"
    ),
}


def analyze_sentiment(message: str) -> float:
    """
    Analyze sentiment of a message.
    Returns score from -1.0 (very negative) to 1.0 (very positive).
    """
    message_lower = message.lower()
    
    # Negative sentiment words
    negative_words = {
        "hate", "despise", "angry", "furious", "destroy", "pain", "suffering",
        "depressed", "hopeless", "worthless", "pathetic", "disgusting",
        "kill", "murder", "suicide", "harm", "hurt", "attack"
    }
    
    # Positive sentiment words
    positive_words = {
        "love", "joy", "peace", "happy", "blessed", "grateful", "wisdom",
        "enlightened", "grateful", "beautiful", "wonderful", "amazing",
        "help", "guide", "understand", "learn", "grow", "spiritual"
    }
    
    # Count sentiment indicators
    words_in_message = set(re.findall(r'\b\w+\b', message_lower))
    
    negative_count = len(words_in_message.intersection(negative_words))
    positive_count = len(words_in_message.intersection(positive_words))
    
    total = negative_count + positive_count
    
    if total == 0:
        return 0.0
    
    # Calculate sentiment score
    sentiment = (positive_count - negative_count) / total
    return max(-1.0, min(1.0, sentiment))  # Clamp between -1 and 1


def calculate_confidence(detected_keywords: List[str], severity: ContentSeverity) -> float:
    """
    Calculate confidence score for the safety assessment.
    """
    base_confidence = 0.6
    
    # More keywords = higher confidence
    keyword_boost = min(0.3, len(detected_keywords) * 0.05)
    
    # Higher severity = higher confidence
    severity_boost = {
        ContentSeverity.SAFE: 0.0,
        ContentSeverity.LOW: 0.05,
        ContentSeverity.MEDIUM: 0.15,
        ContentSeverity.HIGH: 0.25,
    }.get(severity, 0.0)
    
    return min(1.0, base_confidence + keyword_boost + severity_boost)


def is_context_safe(message: str, detected_keywords: List[str]) -> bool:
    """
    Determine if the context makes the message safe despite containing flagged keywords.
    For example: "How to kill negative thoughts?" is safe.
    """
    message_lower = message.lower()
    
    # Safe contexts for otherwise flagged words
    safe_contexts = [
        r"how\s+to\s+(?:kill|destroy)\s+(?:negative|fear|doubt|anger|ego|bad)",
        r"(?:kill|destroy)\s+(?:my\s+)?(?:pain|suffering|fear)",
        r"end\s+(?:my\s+)?(?:suffering|pain|cycle)",
        r"(?:help|support|guidance)\s+(?:coding|programming|software)",
    ]
    
    for context_pattern in safe_contexts:
        if re.search(context_pattern, message_lower):
            return True
    
    # Check if message contains positive indicators
    positive_count = len(set(re.findall(r'\b\w+\b', message_lower)).intersection(POSITIVE_INDICATORS))
    
    return positive_count > 0 and len(detected_keywords) < 3


def check_safety(message: str) -> SafetyResult:
    """
    Check if a message is safe and appropriate for the Krishna chatbot.
    Now includes nuanced context-aware filtering and sentiment analysis.

    Args:
        message: User's input message

    Returns:
        SafetyResult with safety status and any redirect response
    """
    message_lower = message.lower()
    
    # Analyze sentiment first
    sentiment_score = analyze_sentiment(message)
    
    # Extract words and check for flagged keywords
    words = set(re.findall(r'\b\w+\b', message_lower))
    
    # Find detected keywords with severity levels
    detected_keywords = []
    highest_severity = ContentSeverity.SAFE
    primary_category = ContentCategory.SAFE
    
    for word in words:
        if word in KEYWORD_SEVERITY:
            severity, category = KEYWORD_SEVERITY[word]
            detected_keywords.append(word)
            
            # Track highest severity
            if severity.value > highest_severity.value:
                highest_severity = severity
            
            # Track primary category
            if category != ContentCategory.SAFE:
                primary_category = category
    
    # If HIGH severity harmful content detected, flag immediately
    if highest_severity == ContentSeverity.HIGH:
        # Check context to see if it's actually safe
        if is_context_safe(message, detected_keywords):
            return SafetyResult(
                is_safe=True,
                category=ContentCategory.SAFE,
                severity=ContentSeverity.SAFE,
                confidence=0.95,
                detected_keywords=detected_keywords,
                sentiment_score=sentiment_score,
            )
        
        logger.warning(f"High severity content detected: {detected_keywords}")
        return SafetyResult(
            is_safe=False,
            reason="harmful_content",
            safe_response=REDIRECT_RESPONSES["harmful"],
            severity=ContentSeverity.HIGH,
            category=ContentCategory.HARMFUL,
            confidence=calculate_confidence(detected_keywords, ContentSeverity.HIGH),
            detected_keywords=detected_keywords,
            sentiment_score=sentiment_score,
        )
    
    # Medium/Low severity - apply context-aware filtering
    if detected_keywords:
        # Check context
        if is_context_safe(message, detected_keywords):
            return SafetyResult(
                is_safe=True,
                category=ContentCategory.SAFE,
                severity=ContentSeverity.SAFE,
                confidence=0.9,
                detected_keywords=detected_keywords,
                sentiment_score=sentiment_score,
            )
        
        # Very negative sentiment + harmful keywords = unsafe
        if sentiment_score < -0.5 and highest_severity in [ContentSeverity.MEDIUM, ContentSeverity.HIGH]:
            category_to_respond = primary_category
            response_key = {
                ContentCategory.HARMFUL: "harmful",
                ContentCategory.OTHER_RELIGION: "other_religion",
                ContentCategory.TECHNICAL: "technical",
                ContentCategory.FINANCIAL: "off_topic",
                ContentCategory.POLITICAL: "off_topic",
            }.get(category_to_respond, "off_topic")
            
            logger.warning(f"Unsafe content with negative sentiment: {detected_keywords}")
            return SafetyResult(
                is_safe=False,
                reason=response_key,
                safe_response=REDIRECT_RESPONSES[response_key],
                severity=highest_severity,
                category=primary_category,
                confidence=calculate_confidence(detected_keywords, highest_severity),
                detected_keywords=detected_keywords,
                sentiment_score=sentiment_score,
            )
        
        # Medium severity - category-specific handling
        if highest_severity == ContentSeverity.MEDIUM:
            if primary_category == ContentCategory.HARMFUL:
                return SafetyResult(
                    is_safe=False,
                    reason="harmful_content",
                    safe_response=REDIRECT_RESPONSES["harmful"],
                    severity=ContentSeverity.MEDIUM,
                    category=ContentCategory.HARMFUL,
                    confidence=calculate_confidence(detected_keywords, ContentSeverity.MEDIUM),
                    detected_keywords=detected_keywords,
                    sentiment_score=sentiment_score,
                )
            elif primary_category == ContentCategory.OTHER_RELIGION:
                return SafetyResult(
                    is_safe=False,
                    reason="other_religion",
                    safe_response=REDIRECT_RESPONSES["other_religion"],
                    severity=ContentSeverity.MEDIUM,
                    category=ContentCategory.OTHER_RELIGION,
                    confidence=calculate_confidence(detected_keywords, ContentSeverity.MEDIUM),
                    detected_keywords=detected_keywords,
                    sentiment_score=sentiment_score,
                )
            elif primary_category == ContentCategory.TECHNICAL:
                return SafetyResult(
                    is_safe=False,
                    reason="technical",
                    safe_response=REDIRECT_RESPONSES["technical"],
                    severity=ContentSeverity.MEDIUM,
                    category=ContentCategory.TECHNICAL,
                    confidence=calculate_confidence(detected_keywords, ContentSeverity.MEDIUM),
                    detected_keywords=detected_keywords,
                    sentiment_score=sentiment_score,
                )
        
        # Low severity - allow with logging
        if highest_severity == ContentSeverity.LOW:
            logger.info(f"Low severity off-topic content detected: {detected_keywords}")
            return SafetyResult(
                is_safe=True,
                category=ContentCategory.SAFE,
                severity=ContentSeverity.LOW,
                confidence=0.85,
                detected_keywords=detected_keywords,
                sentiment_score=sentiment_score,
            )
    
    # No flagged keywords - safe message
    return SafetyResult(
        is_safe=True,
        category=ContentCategory.SAFE,
        severity=ContentSeverity.SAFE,
        confidence=1.0,
        detected_keywords=[],
        sentiment_score=sentiment_score,
    )


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

def get_contextual_response(severity: ContentSeverity, category: ContentCategory, user_context: str = "") -> str:
    """
    Get a contextual redirect response based on severity and category.
    
    Args:
        severity: Severity level of the flagged content
        category: Category of the flagged content
        user_context: Additional context for more personalized responses
    
    Returns:
        Appropriate redirect response
    """
    if category == ContentCategory.HARMFUL:
        return REDIRECT_RESPONSES["harmful"]
    elif category == ContentCategory.OTHER_RELIGION:
        return REDIRECT_RESPONSES["other_religion"]
    elif category == ContentCategory.TECHNICAL:
        return REDIRECT_RESPONSES["technical"]
    elif category == ContentCategory.FINANCIAL or category == ContentCategory.POLITICAL:
        return REDIRECT_RESPONSES["off_topic"]
    else:
        return REDIRECT_RESPONSES["off_topic"]


def generate_safety_report(result: SafetyResult) -> dict:
    """
    Generate a detailed safety analysis report.
    Useful for logging and debugging.
    
    Args:
        result: SafetyResult object
    
    Returns:
        Dictionary with detailed safety information
    """
    return {
        "is_safe": result.is_safe,
        "reason": result.reason,
        "severity": result.severity.value,
        "category": result.category.value,
        "confidence": round(result.confidence, 3),
        "sentiment_score": round(result.sentiment_score, 3),
        "detected_keywords": result.detected_keywords,
        "safe_response_preview": result.safe_response[:100] + "..." if len(result.safe_response) > 100 else result.safe_response,
    }
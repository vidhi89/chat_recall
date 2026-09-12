import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class QueryAnalysis:
    query: str
    intent: str
    person: Optional[str] = None
    time_expression: Optional[str] = None
    is_decision_query: bool = False
    topic: Optional[str] = None


PARTICIPANTS = [
    "Aarav",
    "Priya",
    "Rahul",
    "Simran",
    "Karan",
    "Neha",
    "Aditya",
    "Mehak",
]


DECISION_TERMS = [
    "decide",
    "decided",
    "decision",
    "final",
    "finally",
    "fixed",
    "fix",
    "locked",
    "settle",
    "settled",
    "choose",
    "chosen",
    "agree",
    "agreed",
    "agreement",
    "selected",
    "picked",
]


TIME_PATTERNS = [
    r"\blast month\b",
    r"\bthis month\b",
    r"\blast week\b",
    r"\bthis week\b",
    r"\byesterday\b",
    r"\btoday\b",
    r"\btomorrow\b",
    r"\bJanuary\b",
    r"\bFebruary\b",
    r"\bMarch\b",
    r"\bApril\b",
    r"\bMay\b",
    r"\bJune\b",
    r"\bJuly\b",
    r"\bAugust\b",
    r"\bSeptember\b",
    r"\bOctober\b",
    r"\bNovember\b",
    r"\bDecember\b",
]


def detect_person(query: str) -> Optional[str]:
    """
    Detect a participant name mentioned in the query.
    """

    query_lower = query.lower()

    for person in PARTICIPANTS:
        if person.lower() in query_lower:
            return person

    return None


def detect_time_expression(
    query: str,
) -> Optional[str]:
    """
    Detect simple natural-language time expressions.
    """

    query_lower = query.lower()

    for pattern in TIME_PATTERNS:
        match = re.search(
            pattern,
            query_lower,
        )

        if match:
            return match.group(0)

    return None


def detect_decision_query(
    query: str,
) -> bool:
    """
    Determine whether the user is asking about a
    decision or final outcome.
    """

    query_lower = query.lower()

    return any(
        term in query_lower
        for term in DECISION_TERMS
    )


def detect_intent(
    query: str,
    person: Optional[str],
    time_expression: Optional[str],
    is_decision_query: bool,
) -> str:
    """
    Determine the primary query type.
    """

    if person:
        return "person"

    if time_expression:
        return "time"

    if is_decision_query:
        return "decision"

    return "semantic"


def detect_topic(
    query: str,
) -> Optional[str]:
    """
    Extract simple topic hints.

    This is intentionally lightweight. We will improve
    topic handling after the basic query router works.
    """

    query_lower = query.lower()

    topic_keywords = {
        "budget": [
            "budget",
            "cost",
            "price",
            "expensive",
            "cheap",
            "money",
        ],
        "trip": [
            "trip",
            "travel",
            "journey",
            "vacation",
            "go",
            "destination",
        ],
        "venue": [
            "venue",
            "place",
            "hall",
            "room",
            "auditorium",
            "event",
        ],
        "technology": [
            "technology",
            "tech",
            "stack",
            "backend",
            "frontend",
            "framework",
        ],
    }

    for topic, keywords in topic_keywords.items():

        if any(
            keyword in query_lower
            for keyword in keywords
        ):
            return topic

    return None


def analyze_query(
    query: str,
) -> QueryAnalysis:
    """
    Analyze a user's search query.
    """

    person = detect_person(query)

    time_expression = detect_time_expression(
        query
    )

    is_decision_query = detect_decision_query(
        query
    )

    intent = detect_intent(
        query=query,
        person=person,
        time_expression=time_expression,
        is_decision_query=is_decision_query,
    )

    topic = detect_topic(query)

    return QueryAnalysis(
        query=query,
        intent=intent,
        person=person,
        time_expression=time_expression,
        is_decision_query=is_decision_query,
        topic=topic,
    )
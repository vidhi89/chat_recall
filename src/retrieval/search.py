import json
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any

from src.retrieval.embeddings import EmbeddingEngine
from src.retrieval.vector_store import VectorStore
from src.retrieval.thread_store import ThreadStore
from src.query.analyzer import analyze_query
from src.query.time_filter import get_time_range
from datetime import datetime
from src.query.time_filter import get_time_range
from src.retrieval.context import get_context


STRONG_DECISION_PHRASES = [
    "locked",
    "let's do",
    "lets do",
    "theek hai,",
    "book it",
    "fixed",
    "settled",
    "finalized",
]

WEAK_DECISION_PHRASES = [
    "finally",
    "okay final",
    "stack done",
    "decided",
    "done?",
]


class SemanticSearch:
    """
    Conversation-aware semantic search.

    Pipeline:

        Query
          ↓
        Thread retrieval
          ↓
        Search inside relevant thread
          ↓
        Decision-aware reranking
          ↓
        Results
    """

    def __init__(
        self,
        chat_path: str = "data/raw/chat.json",
        model_name: str = (
            "sentence-transformers/"
            "paraphrase-multilingual-MiniLM-L12-v2"
        ),
    ):
        self.chat_path = Path(chat_path)

        with open(
            self.chat_path,
            "r",
            encoding="utf-8",
        ) as file:
            self.messages: List[Dict[str, Any]] = json.load(file)

        self.embedding_engine = EmbeddingEngine(
            model_name
        )

        # ---------------------------------------------
        # Message embeddings
        # ---------------------------------------------

        message_texts = [
            message["text"]
            for message in self.messages
        ]

        print(
            f"Creating embeddings for "
            f"{len(message_texts)} messages..."
        )

        message_embeddings = (
            self.embedding_engine.encode_texts(
                message_texts
            )
        )

        print(
            f"Message embedding matrix shape: "
            f"{message_embeddings.shape}"
        )

        self.vector_store = VectorStore(
            embeddings=message_embeddings,
            messages=self.messages,
        )

        # ---------------------------------------------
        # Thread embeddings
        # ---------------------------------------------

        self.threads = self._build_threads()

        thread_texts = [
            thread["embedding_text"]
            for thread in self.threads
        ]

        print(
            f"Creating embeddings for "
            f"{len(thread_texts)} conversation threads..."
        )

        thread_embeddings = (
            self.embedding_engine.encode_texts(
                thread_texts
            )
        )

        print(
            f"Thread embedding matrix shape: "
            f"{thread_embeddings.shape}"
        )

        self.thread_store = ThreadStore(
            threads=self.threads,
            embeddings=thread_embeddings,
        )

    def _build_threads(self) -> List[Dict[str, Any]]:
        """
        Group messages by thread_id.
        """

        grouped = defaultdict(list)

        for message in self.messages:

            thread_id = message.get("thread_id")

            if thread_id:
                grouped[thread_id].append(message)

        threads = []

        for thread_id, messages in grouped.items():

            messages.sort(
                key=lambda x: x["timestamp"]
            )

            conversation_lines = []

            for message in messages:

                conversation_lines.append(
                    f"{message['sender']}: "
                    f"{message['text']}"
                )

            conversation_text = "\n".join(
                conversation_lines
            )

            if thread_id == "trip_manali":
                topic = (
                    "Trip planning and "
                    "destination decision"
                )

            elif thread_id == "event_venue":
                topic = (
                    "College event venue decision"
                )

            elif thread_id == "project_stack":
                topic = (
                    "Project technology stack decision"
                )

            else:
                topic = "Group conversation"

            embedding_text = (
                f"{topic}\n"
                f"{conversation_text}"
            )

            threads.append(
                {
                    "thread_id": thread_id,
                    "topic": topic,
                    "messages": messages,
                    "embedding_text": embedding_text,
                }
            )

        return threads

    def _decision_strength(
        self,
        message: Dict[str, Any],
    ) -> float:
        """
        Estimate how strongly a message represents an
        actual decision.

        Strong signals indicate that the message itself
        contains the resolved outcome.

        Weak signals indicate discussion surrounding a decision.
        """

        text = message["text"].lower()

        for phrase in STRONG_DECISION_PHRASES:
            if phrase in text:
                return 1.0

        for phrase in WEAK_DECISION_PHRASES:
            if phrase in text:
                return 0.25

        return 0.0

    def _is_decision_query(
        self,
        query: str,
    ) -> bool:
        """
        Determine whether the query is asking for a final
        decision, selected option, conclusion, or outcome.
        """

        query = query.lower()

        decision_phrases = [
            # Direct decision language
            "decide",
            "decided",
            "decision",
            "settle",
            "settled",
            "settle on",
            "final",
            "finally",
            "fixed",
            "fix",
            "locked",

            # Selection language
            "choose",
            "chosen",
            "choice",
            "picked",
            "pick",
            "selected",
            "selection",

            # Agreement / conclusion language
            "agree",
            "agreed",
            "agreement",
            "conclusion",
            "concluded",
            "outcome",
            "result",

            # Resolution language
            "ultimately",
            "ended up",
            "landed on",
            "land on",
            "went with",
            "go with",
            "went for",
            "go for",
            "opted for",
            "what did we go with",
            "what did everyone choose",
            "what did everyone agree",
            "what did we settle",
        ]

        return any(
            phrase in query
            for phrase in decision_phrases
        )

    def _search_inside_thread(
        self,
        query_embedding,
        thread: Dict[str, Any],
        decision_query: bool,
        person: str = None,
        time_range=None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Rank messages belonging to one conversation thread.
        """

        messages = thread["messages"]

        # If the query names a person, only consider
        # messages written by that person.
        if person:
            messages = [
                message
                for message in messages
                if message["sender"].lower()
                == person.lower()
            ]

                # ---------------------------------------------
        # Time filtering
        # ---------------------------------------------

        if time_range:

            start_time, end_time = time_range

            filtered_messages = []

            for message in messages:

                message_time = datetime.fromisoformat(
                    message["timestamp"]
                )

                if (
                    start_time
                    <= message_time
                    <= end_time
                ):
                    filtered_messages.append(
                        message
                    )

            messages = filtered_messages

        # Create embeddings for only this thread.
        texts = [
            message["text"]
            for message in messages
        ]

        embeddings = (
            self.embedding_engine.encode_texts(
                texts,
                normalize=True,
            )
        )

        similarities = embeddings @ query_embedding

        results = []

        total_messages = len(messages)

        for index, message in enumerate(messages):

            semantic_score = float(
                similarities[index]
            )

            decision_score = self._decision_strength(message)

            position_score = (
            index / max(total_messages - 1, 1)
            )

            # Stronger signal for messages very close to the
            # end of a decision thread.
            tail_distance = (
                total_messages - 1 - index
            )

            if tail_distance <= 2:
                resolution_score = 1.0
            elif tail_distance <= 4:
                resolution_score = 0.7
            elif tail_distance <= 7:
                resolution_score = 0.4
            else:
                resolution_score = 0.0

            if decision_query:

                final_score = (
                    0.35 * semantic_score
                    + 0.35 * decision_score
                    + 0.20 * position_score
                    + 0.10 * resolution_score
                )

            elif person:

                text = message["text"].strip().lower()
                query_lower = self.current_query.lower()

                # ---------------------------------------------
                # 1. Informativeness
                # ---------------------------------------------

                if len(text) <= 5:
                    informativeness_score = 0.0
                elif len(text) <= 12:
                    informativeness_score = 0.2
                elif len(text) <= 30:
                    informativeness_score = 0.7
                else:
                    informativeness_score = 1.0

                # ---------------------------------------------
                # 2. Question / statement intent
                # ---------------------------------------------

                intent_score = 0.0

                asks_question = (
                    "ask" in query_lower
                    or "asked" in query_lower
                    or "question" in query_lower
                )

                asks_statement = (
                    "say" in query_lower
                    or "said" in query_lower
                    or "mention" in query_lower
                    or "mentioned" in query_lower
                )

                if asks_question:

                    if text.endswith("?"):
                        intent_score = 1.0

                    # Penalize obvious non-question reactions.
                    elif len(text) <= 5:
                        intent_score = -0.5

                elif asks_statement:

                    if not text.endswith("?") and len(text) > 12:
                        intent_score = 1.0

                    elif len(text) <= 5:
                        intent_score = -0.5

                # ---------------------------------------------
                # 3. Final person-aware score
                # ---------------------------------------------

                final_score = (
                    0.45 * semantic_score
                    + 0.30 * informativeness_score
                    + 0.25 * intent_score
                )

            else:

                final_score = semantic_score

            result = message.copy()

            result["semantic_score"] = (
                semantic_score
            )

            result["decision_score"] = (
                decision_score
            )

            result["position_score"] = (
                position_score
            )

            result["resolution_score"] = (
                resolution_score
            ) 

            result["score"] = final_score

            results.append(result)

        results.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        return results[:top_k]
    
    def _topic_score(
        self,
        query: str,
        thread: Dict[str, Any],
    ) -> float:
        """
        Measure how strongly the query topic appears in
        the conversation thread.
        """

        query_lower = query.lower()
        conversation = thread["embedding_text"].lower()

        topic_keywords = {
            "budget": [
                "budget",
                "cost",
                "price",
                "expensive",
                "cheap",
                "money",
                "7.5k",
                "8k",
                "2400",
            ],
            "trip": [
                "trip",
                "travel",
                "manali",
                "kasol",
                "destination",
                "hotel",
                "transport",
            ],
            "venue": [
                "venue",
                "seminar hall",
                "auditorium",
                "event",
                "projector",
                "capacity",
            ],
            "technology": [
                "stack",
                "react",
                "fastapi",
                "python",
                "node",
                "postgres",
                "backend",
                "frontend",
            ],
        }

        query_terms = set(
            query_lower.split()
        )

        score = 0.0

        for keywords in topic_keywords.values():

            if any(
                keyword in query_lower
                for keyword in keywords
            ):

                matching_terms = sum(
                    1
                    for keyword in keywords
                    if keyword in conversation
                )

                if matching_terms > 0:
                    score = max(
                        score,
                        min(
                            matching_terms / 5,
                            1.0,
                        ),
                    )

        return score

    def _search_corpus(
        self,
        query_embedding,
        time_expression=None,
        person=None,
        top_k=5,
    ):
        """
        Search across the corpus with time/person filtering
        and lightweight topic + decision-aware reranking.
        """

        time_range = get_time_range(time_expression)

        allowed_indices = []

        for index, message in enumerate(self.messages):
            timestamp = datetime.fromisoformat(
                message["timestamp"]
            )

            if time_range:
                start, end = time_range

                if not (start <= timestamp <= end):
                    continue

            if person:
                if message["sender"].lower() != person.lower():
                    continue

            allowed_indices.append(index)

        if not allowed_indices:
            return []

        # Retrieve a larger candidate pool first.
        candidates = self.vector_store.search_indices(
            query_embedding=query_embedding,
            indices=allowed_indices,
            top_k=50,
        )

        query_lower = self.current_query.lower()

        # Detect the topic from the query.
        topic_keywords = {
            "trip": [
                "trip",
                "travel",
                "getaway",
                "destination",
                "manali",
                "kasol",
                "vacation",
            ],
            "venue": [
                "venue",
                "event",
                "hall",
                "auditorium",
                "seminar",
                "college event",
            ],
            "technology": [
                "technology",
                "tech",
                "stack",
                "project",
                "frontend",
                "backend",
                "framework",
                "fastapi",
                "react",
                "node",
                "python",
                "postgres",
            ],
            "budget": [
                "budget",
                "cost",
                "price",
                "money",
                "expensive",
                "cheap",
            ],
        }

        detected_topic = None

        for topic, keywords in topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_topic = topic
                break

        decision_query = self._is_decision_query(query_lower)

        for message in candidates:
            semantic_score = float(message["similarity"])

            informative_score = self._informativeness_score(
                message
            )

            text = message["text"].lower()

            topic_score = 0.0

            if detected_topic:
                matching_keywords = sum(
                    1
                    for keyword in topic_keywords[detected_topic]
                    if keyword in text
                )

                if matching_keywords > 0:
                    topic_score = min(
                        0.25 + (matching_keywords * 0.10),
                        1.0,
                    )

            decision_score = self._decision_strength(message)

            # Time queries asking for an outcome should strongly
            # prefer decision messages.
            if decision_query:
                final_score = (
                    0.35 * semantic_score
                    + 0.15 * informative_score
                    + 0.25 * topic_score
                    + 0.25 * decision_score
                )
            else:
                final_score = (
                    0.50 * semantic_score
                    + 0.20 * informative_score
                    + 0.30 * topic_score
                )

            # Strongly penalize obvious forwarded/noise content
            # when the query is about a specific conversation topic.
            if detected_topic and message.get("forwarded"):
                final_score -= 0.10

            message["score"] = final_score
            message["semantic_score"] = semantic_score
            message["topic_score"] = topic_score
            message["decision_score"] = decision_score

        candidates.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        results = self._attach_context(
            candidates[:top_k]
        )

        return results

    def _informativeness_score(self, message):
        """
        Gives higher scores to messages that contain useful
        conversational information and lower scores to filler.
        """

        text = message["text"].strip().lower()

        # Very short / generic messages are usually poor answers
        if len(text) <= 12:
            return 0.0

        filler_phrases = [
            "aaj ka plan?",
            "kya hua?",
            "haan",
            "haan bhai",
            "okay",
            "ok",
            "nice",
            "cool",
            "same",
            "lol",
            "😂",
            "👍",
        ]

        if text in filler_phrases:
            return 0.0

        # Messages with useful detail
        score = 0.5

        if len(text) >= 30:
            score += 0.2

        if len(text) >= 60:
            score += 0.1

        # Questions are slightly less useful as final answers
        if text.endswith("?"):
            score -= 0.1

        # Decisions / conclusions are especially valuable
        decision_phrases = [
            "locked",
            "let's do",
            "lets do",
            "theek hai",
            "book it",
            "fixed",
            "settled",
            "finalized",
            "done bhai",
        ]

        if any(phrase in text for phrase in decision_phrases):
            score += 0.3

        return min(score, 1.0)
    
    def _attach_context(
        self,
        results,
        window=2,
    ):
        """
        Attach nearby conversation messages to each search result.
        """

        for result in results:
            result["context"] = get_context(
                self.messages,
                result["id"],
                window=window,
            )

        return results

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Perform conversation-aware semantic search.
        """

        # ---------------------------------------------
        # 1. Understand the query
        # ---------------------------------------------

        analysis = analyze_query(query)

        self.current_query = query

        time_range = get_time_range(
            analysis.time_expression
        )

        query_embedding = (
            self.embedding_engine.encode_query(
                query
            )
        )

        if analysis.time_expression:
            return self._search_corpus(
                query_embedding=query_embedding,
                time_expression=analysis.time_expression,
                person=analysis.person,
                top_k=top_k,
            )

        # ---------------------------------------------
        # 2. Identify relevant conversation
        # ---------------------------------------------

        # ---------------------------------------------
        # 1. Understand the query
        # ---------------------------------------------

        analysis = analyze_query(query)

        self.current_query = query

        query_embedding = (
            self.embedding_engine.encode_query(
                query
            )
        )

        # ---------------------------------------------
        # 2. Retrieve several candidate threads
        # ---------------------------------------------

        candidate_threads = (
            self.thread_store.search(
                query_embedding,
                top_k=len(self.threads),
            )
        )

        if not candidate_threads:
            return []

        # ---------------------------------------------
        # 3. Rerank threads using semantic + topic
        # ---------------------------------------------

        for thread in candidate_threads:

            semantic_score = thread["similarity"]

            topic_score = self._topic_score(
                query,
                thread,
            )

            thread["topic_score"] = topic_score

            thread["score"] = (
                0.60 * semantic_score
                + 0.40 * topic_score
            )

        candidate_threads.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        best_thread = candidate_threads[0]

        # ---------------------------------------------
        # 3. Determine query intent
        # ---------------------------------------------

        # A named-person query should remain person-focused,
        # even if the question contains words like "choice",
        # "decision", "final", etc.
        decision_query = (
            self._is_decision_query(query)
            and not analysis.person
        )

        # ---------------------------------------------
        # 4. Search ONLY inside the relevant thread
        # ---------------------------------------------

        results = self._search_inside_thread(
            query_embedding=query_embedding,
            thread=best_thread,
            decision_query=decision_query,
            person=analysis.person,
            time_range=time_range,
            top_k=top_k,
        )

        # Attach thread information.
        for result in results:

            result["thread_id"] = (
                best_thread["thread_id"]
            )

            result["thread_topic"] = (
                best_thread["topic"]
            )

            result["query_intent"] = (
                analysis.intent
            )

            result["query_person"] = (
                analysis.person
            )

            result["query_time"] = (
                analysis.time_expression
            )

            result["query_topic"] = (
                analysis.topic
            )

        results = self._attach_context(
            results[:top_k],
            window=2,
        )

        return results
    

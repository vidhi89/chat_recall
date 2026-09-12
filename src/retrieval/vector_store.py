from typing import List, Dict, Any

import numpy as np


class VectorStore:
    """
    Simple in-memory vector store using cosine similarity.

    For 5,000 messages, a NumPy-based implementation is
    more than sufficient and keeps the project simple.
    """

    def __init__(
        self,
        embeddings: np.ndarray,
        messages: List[Dict[str, Any]],
    ):
        self.embeddings = embeddings
        self.messages = messages

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Return the top-k most semantically similar messages.
        """

        scores = self.embeddings @ query_embedding

        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []

        for index in top_indices:
            message = self.messages[index].copy()
            message["similarity"] = float(scores[index])
            results.append(message)

        return results
    
    def search_indices(
        self,
        query_embedding: np.ndarray,
        indices: List[int],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search only within the specified message indices.
        """

        if not indices:
            return []

        candidate_embeddings = self.embeddings[indices]

        scores = candidate_embeddings @ query_embedding

        top_positions = np.argsort(scores)[::-1][:top_k]

        results = []

        for position in top_positions:
            original_index = indices[position]

            message = self.messages[original_index].copy()
            message["similarity"] = float(scores[position])

            results.append(message)

        return results
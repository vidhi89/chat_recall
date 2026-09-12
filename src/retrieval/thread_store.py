from collections import defaultdict
from typing import List, Dict, Any

import numpy as np


class ThreadStore:
    """
    Stores conversation threads and searches them using
    semantic similarity.
    """

    def __init__(
        self,
        threads: List[Dict[str, Any]],
        embeddings: np.ndarray,
    ):
        self.threads = threads
        self.embeddings = embeddings

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Return the most relevant conversation threads.
        """

        scores = self.embeddings @ query_embedding

        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []

        for index in top_indices:
            thread = self.threads[index].copy()
            thread["similarity"] = float(scores[index])
            results.append(thread)

        return results
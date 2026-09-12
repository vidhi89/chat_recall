from pathlib import Path
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingEngine:
    """
    Creates semantic embeddings for chat messages and queries.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode_texts(
        self,
        texts: List[str],
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Convert a list of texts into embedding vectors.
        """

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        if normalize:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.maximum(norms, 1e-12)

        return embeddings

    def encode_query(self, query: str) -> np.ndarray:
        """
        Convert a single search query into an embedding vector.
        """

        embedding = self.model.encode(
            query,
            convert_to_numpy=True,
        )

        norm = np.linalg.norm(embedding)

        if norm > 0:
            embedding = embedding / norm

        return embedding
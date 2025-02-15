import numpy as np
from openai import OpenAI


class VectorRetrieval:
    def __init__(self, api_key, base_url, model, dimensions) -> None:
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model
        self.dimensions = dimensions

    def get_emb(self, sentences, model=None, dimensions=None):
        model = model or self.model
        dimensions = dimensions or self.dimensions
        response = self.client.embeddings.create(model=model, input=sentences)
        em = np.array(response.data[0].embedding)
        return em / np.linalg.norm(em)

    def is_semantic_dup(
        self,
        query: str,
        src_embeddings: np.ndarray,
        accept_threshold=0.78,
        reject_threshold=0.6,
    ):
        tgt_emb = self.get_emb(query)
        cos = np.dot(src_embeddings, tgt_emb)
        is_dup = "No"
        cos_max = cos.max()
        if cos_max >= accept_threshold:
            is_dup = "Yes"
        elif reject_threshold < cos_max < accept_threshold:
            is_dup = "Unknown"
        return is_dup, tgt_emb, cos

    def find_simi(self, query: str, src_embeddings: np.ndarray, k=5, threshold=0.78):
        tgt_emb = self.get_emb(query)
        cos = np.dot(src_embeddings, tgt_emb)
        scores, indices = self.topk(cos, k)
        index = []
        for i, score in enumerate(scores):
            if i == 5 or score < threshold:
                break
            index.append(indices[i])
        return index

    @staticmethod
    def topk(vector: np.ndarray, k: int, axis=-1):
        """
        Returns the k largest elements along a given axis.

        Parameters:
        - vector: ndarray
            Input array
        - k: int
            Number of largest elements to return
        - axis: int (optional)
            Axis along which to find the k largest elements (default: -1)

        Returns:
        - values: ndarray
            k largest elements
        - indices: ndarray
            Indices of the k largest elements
        """
        if axis < 0:
            axis += vector.ndim
        indices = np.argsort(vector, axis=axis)[..., -k:]
        values = np.take_along_axis(vector, indices, axis=axis)
        return values, indices


if __name__ == "__main__":
    ...

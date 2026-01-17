# File: backend/chatbot/faiss_agent.py

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os

class FAISSAgent:
    """
    Semantic search via FAISS vectorstore

    Uses existing FAISS implementation
    Provides semantic similarity search as complement to tag search
    """

    def __init__(self):
        self.vectorstore = self._load_vectorstore()

    def _load_vectorstore(self):
        """Load existing FAISS index"""
        faiss_index_path = os.path.join(
            os.path.dirname(__file__),
            "faiss_index"
        )

        if not os.path.exists(faiss_index_path):
            print(f"Warning: FAISS index not found at {faiss_index_path}")
            return None

        openai_key = os.environ.get("OPENAI_API_KEY")
        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)

        try:
            vectorstore = FAISS.load_local(
                faiss_index_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
            print("FAISSAgent: Successfully loaded FAISS index")
            return vectorstore
        except Exception as e:
            print(f"Warning: Could not load FAISS index: {e}")
            return None

    def search(self, question: str, k: int = 10, score_threshold: float = 0.3) -> list:
        """
        Semantic search for relevant chunks

        Args:
            question: User's question
            k: Number of results to return
            score_threshold: Minimum similarity score (lower for ensemble)

        Returns:
            [
                {
                    "content": str,
                    "source": str,
                    "score": float,
                    "metadata": dict,
                    "retrieval_source": "faiss"
                },
                ...
            ]
        """

        if self.vectorstore is None:
            print("Warning: FAISS vectorstore not loaded, returning empty results")
            return []

        # Similarity search with scores
        try:
            results = self.vectorstore.similarity_search_with_score(
                question,
                k=k
            )
        except Exception as e:
            print(f"Warning: FAISS search failed: {e}")
            return []

        # Filter by threshold and format
        formatted_results = []
        for doc, score in results:
            if score >= score_threshold:
                formatted_results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", ""),
                    "score": float(score),
                    "metadata": doc.metadata,
                    "retrieval_source": "faiss"
                })

        return formatted_results

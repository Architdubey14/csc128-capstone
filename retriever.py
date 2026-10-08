"""
CSC-128 Capstone: TF-IDF retrieval over the knowledge base
Archit Dubey

Imports from knowledge.py only. Nothing here imports Streamlit or groq, so the
tests run with no API key.
"""
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from knowledge import DOCUMENTS

STOP_WORDS = {
    "a", "an", "the", "i", "me", "my", "we", "us", "our", "you", "your",
    "is", "am", "are", "was", "were", "be", "been", "do", "does", "did",
    "have", "has", "had", "can", "could", "will", "would", "should",
    "to", "for", "of", "in", "on", "at", "with", "about", "from", "by",
    "and", "or", "but", "it", "its", "this", "that", "there", "here",
    "if", "so", "as", "up", "out", "any", "some", "please", "hi", "hello",
    "what", "when", "where", "who", "which", "why", "how",
    "get", "got", "getting", "need", "want", "like", "much", "many",
    "also", "just", "make", "take", "come", "go",
}

# Threshold set from the scores printed by test_capstone.py, not guessed.
# Lowest score among questions that should retrieve: 0.141.
# Highest among questions that should be refused: 0.000.
# 0.10 sits inside that gap.
DEFAULT_THRESHOLD = 0.10
DEFAULT_TOP_K = 3

# Longest first, so "ations" is tried before "ation" and "s".
SUFFIXES = ["ations", "ation", "ings", "ing", "ies", "ers", "er", "ed", "es", "s"]


def stem(word):
    """
    Strip common suffixes so that class and classes, or cancel and cancelling,
    collapse to the same token. Not a real Porter stemmer.
    """
    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            word = word[: -len(suffix)]
            break

    if word.endswith("i"):
        word = word[:-1] + "y"
    return word


def analyze(text):
    """Normalize, tokenize, stem, and add bigrams."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    tokens = []
    for word in text.split():
        if word in STOP_WORDS:
            continue
        tokens.append(stem(word))

    # Bigrams let a two word idea like "day pass" or "front desk" score as one
    # feature instead of two loose words.
    bigrams = []
    for i in range(len(tokens) - 1):
        bigrams.append(tokens[i] + "_" + tokens[i + 1])

    return tokens + bigrams


class Retriever:
    def __init__(self, documents=None, threshold=DEFAULT_THRESHOLD):
        """Fit the vectorizer once, here, rather than on every search."""
        if documents is None:
            documents = DOCUMENTS

        self.documents = documents
        self.threshold = threshold

        texts = [document["text"] for document in documents]
        self.vectorizer = TfidfVectorizer(analyzer=analyze)
        self.matrix = self.vectorizer.fit_transform(texts)

    def search(self, question, top_k=DEFAULT_TOP_K):
        """
        Return a list of (document, score), best first, dropping anything
        below the threshold.

        An empty list is correct and important. It is what tells the bot to
        refuse instead of answering from nothing.
        """
        vector = self.vectorizer.transform([question])
        scores = cosine_similarity(vector, self.matrix)[0]

        hits = []
        for document, score in zip(self.documents, scores):
            if score >= self.threshold:
                hits.append((document, float(score)))

        hits.sort(key=lambda pair: pair[1], reverse=True)
        return hits[:top_k]

    def best_score(self, question):
        """Highest score for a question, ignoring the threshold. Used by tests."""
        vector = self.vectorizer.transform([question])
        scores = cosine_similarity(vector, self.matrix)[0]
        return float(max(scores))

    def build_context(self, hits):
        """Format retrieved documents for the prompt, with their sources."""
        parts = []
        for document, score in hits:
            parts.append("[" + document["source"] + "]\n" + document["text"])
        return "\n\n".join(parts)

"""
Lightweight Hybrid BM25 Retriever
Implements BM25 with text length normalization, domain stop-words filtering,
and field boost (Title, Tags, SKU).
"""

import math
import re
from typing import List, Dict, Any, Tuple, Optional
from core.loader import CorpusLoader, CorpusChunk

EN_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "and", "in", "for", "on", "with", "at", "by", "from",
    "up", "about", "into", "over", "after", "it", "this", "that", "these",
    "those", "i", "we", "you", "they", "he", "she", "my", "your", "our",
    "their", "please", "dear", "hello", "hi", "hey", "sir", "madam",
    "can", "could", "would", "will", "do", "does", "did", "have", "has",
    "had", "thanks", "thank", "regards", "me", "us", "him", "her", "them"
}

ZH_STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
    "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会",
    "着", "没有", "没", "看", "好", "自己", "这", "请", "您", "你好", "我们",
    "你们", "他们", "么", "吗", "呢", "吧", "啊"
}


class HybridRetriever:
    def __init__(self, loader: CorpusLoader, k1: float = 1.5, b: float = 0.75):
        self.loader = loader
        self.k1 = k1
        self.b = b
        self.chunks: List[CorpusChunk] = []
        self.doc_lengths: List[int] = []
        self.avgdl: float = 1.0
        self.df: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.build_index()

    @staticmethod
    def tokenize(text: str, remove_stopwords: bool = True) -> List[str]:
        raw_tokens = re.findall(r"[a-zA-Z0-9_\-\.\$]+|[\u4e00-\u9fff]", text.lower())
        tokens = []
        for t in raw_tokens:
            cleaned = t.strip(".,;:!?*()[]{}\"'`~<>-")
            if cleaned:
                tokens.append(cleaned)

        if remove_stopwords:
            tokens = [
                t for t in tokens
                if t not in EN_STOP_WORDS and t not in ZH_STOP_WORDS and len(t) > 0
            ]
        return tokens

    def build_index(self):
        self.chunks = self.loader.get_all_chunks()
        N = len(self.chunks)
        if N == 0:
            self.doc_lengths = []
            self.avgdl = 1.0
            self.df = {}
            self.idf = {}
            return

        self.doc_lengths = []
        self.df = {}

        for chunk in self.chunks:
            tokens = self.tokenize(chunk.content + " " + chunk.title + " " + chunk.section_title)
            self.doc_lengths.append(len(tokens))
            seen = set(tokens)
            for t in seen:
                self.df[t] = self.df.get(t, 0) + 1

        total_length = sum(self.doc_lengths)
        self.avgdl = (total_length / N) if N > 0 else 1.0

        self.idf = {}
        for t, freq in self.df.items():
            self.idf[t] = math.log(1.0 + (N - freq + 0.5) / (freq + 0.5))

    def retrieve(self, query: str, top_k: int = 3, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        query_tokens = self.tokenize(query)
        if not query_tokens or not self.chunks:
            return []

        scores: List[Tuple[float, CorpusChunk]] = []

        for idx, chunk in enumerate(self.chunks):
            if category_filter and chunk.category != category_filter:
                continue

            content_tokens = self.tokenize(chunk.content)
            title_tokens = self.tokenize(chunk.title + " " + chunk.section_title)
            tag_tokens = [t.lower() for t in chunk.tags]
            sku_token = chunk.sku.lower() if chunk.sku else ""

            freq_map: Dict[str, int] = {}
            for t in content_tokens:
                freq_map[t] = freq_map.get(t, 0) + 1

            # Field boosts
            for t in title_tokens:
                freq_map[t] = freq_map.get(t, 0) + 2
            for t in tag_tokens:
                freq_map[t] = freq_map.get(t, 0) + 3
            if sku_token:
                freq_map[sku_token] = freq_map.get(sku_token, 0) + 5

            doc_len = self.doc_lengths[idx] if idx < len(self.doc_lengths) else len(content_tokens)
            score = 0.0

            for q in query_tokens:
                if q in freq_map:
                    tf = freq_map[q]
                    idf = self.idf.get(q, 0.5)
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
                    score += idf * (numerator / max(denominator, 1e-6))

            if score > 0:
                scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        for s, chunk in scores[:top_k]:
            results.append({
                "score": round(s, 3),
                "chunk_id": chunk.chunk_id,
                "title": chunk.title,
                "section": chunk.section_title,
                "category": chunk.category,
                "sku": chunk.sku,
                "moq": chunk.moq,
                "cbm": chunk.cbm,
                "content": chunk.content,
            })
        return results

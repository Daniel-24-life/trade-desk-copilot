import pytest
from pathlib import Path
from core.loader import CorpusLoader
from core.retriever import HybridRetriever


def test_corpus_loader():
    loader = CorpusLoader()
    assert len(loader.documents) >= 4
    chunks = loader.get_all_chunks()
    assert len(chunks) >= 8

    # Verify metadata inheritance
    downlight_chunks = [c for c in chunks if "downlight" in c.doc_id]
    assert len(downlight_chunks) > 0
    assert any(c.sku == "LT-DL01-SERIES" for c in downlight_chunks)


def test_hybrid_retriever():
    loader = CorpusLoader()
    retriever = HybridRetriever(loader)

    # Search for DALI downlight
    results = retriever.retrieve("architectural downlight UGR 19 DALI dimming", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert "downlight" in top["title"].lower() or "downlight" in top["chunk_id"].lower()
    assert top["score"] > 0

    # Search for fan light
    fan_results = retriever.retrieve("socket ceiling fan e27 remote control", top_k=2)
    assert len(fan_results) > 0
    assert "fan" in fan_results[0]["title"].lower()

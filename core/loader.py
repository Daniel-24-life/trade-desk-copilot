"""
Corpus Loader & Structured Chunking Engine
Loads markdown product catalogs and company profiles, extracts YAML frontmatter,
and breaks documents into searchable semantic sections.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


class CorpusChunk:
    """A semantic chunk of a corpus document with inherited metadata."""
    def __init__(
        self,
        chunk_id: str,
        doc_id: str,
        title: str,
        section_title: str,
        category: str,
        tags: List[str],
        metadata: Dict[str, Any],
        content: str,
        file_path: Path,
        chunk_index: int = 0
    ):
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.title = title
        self.section_title = section_title
        self.category = category
        self.tags = tags
        self.metadata = metadata
        self.content = content.strip()
        self.file_path = file_path
        self.chunk_index = chunk_index

    @property
    def sku(self) -> Optional[str]:
        return self.metadata.get("sku")

    @property
    def moq(self) -> Optional[Any]:
        return self.metadata.get("moq")

    @property
    def cbm(self) -> Optional[Any]:
        return self.metadata.get("carton_spec") or self.metadata.get("cbm")

    @property
    def voltage(self) -> Optional[str]:
        return self.metadata.get("voltage")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "title": self.title,
            "section_title": self.section_title,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
            "content": self.content,
            "file_path": str(self.file_path),
            "chunk_index": self.chunk_index,
        }

    def __repr__(self):
        return f"<CorpusChunk id={self.chunk_id} section='{self.section_title[:20]}' doc='{self.doc_id}'>"


class CorpusDocument:
    """Full corpus document containing raw text and chunk collection."""
    def __init__(self, file_path: Path, metadata: Dict[str, Any], content: str):
        self.file_path = file_path
        self.metadata = metadata
        self.content = content.strip()
        self.doc_id = str(metadata.get("id", file_path.stem))
        self.title = str(metadata.get("title", file_path.stem))
        self.category = str(metadata.get("category", file_path.parent.name))
        
        tags = metadata.get("tags", [])
        if isinstance(tags, str):
            self.tags = [tags]
        elif isinstance(tags, list):
            self.tags = [str(t) for t in tags]
        else:
            self.tags = []

        self.chunks: List[CorpusChunk] = []


class CorpusLoader:
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            # Default to ../corpus relative to this file
            self.base_dir = Path(__file__).resolve().parent.parent / "corpus"
        else:
            self.base_dir = Path(base_dir)

        self.documents: List[CorpusDocument] = []
        self._doc_map: Dict[str, CorpusDocument] = {}
        self.load()

    def load(self):
        self.documents.clear()
        self._doc_map.clear()

        if not self.base_dir.exists():
            return

        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith(".md"):
                    file_path = Path(root) / file
                    doc = self._parse_file(file_path)
                    if doc:
                        self.documents.append(doc)
                        self._doc_map[doc.doc_id] = doc

    def _parse_frontmatter(self, raw_text: str) -> tuple[Dict[str, Any], str]:
        """Simple YAML frontmatter parser fallback if PyYAML is not installed."""
        pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(pattern, raw_text, re.DOTALL)
        if not match:
            return {}, raw_text

        front_str = match.group(1)
        body = raw_text[match.end():]

        if yaml is not None:
            try:
                data = yaml.safe_load(front_str)
                return data or {}, body
            except Exception:
                pass

        # Manual key-value regex parser fallback
        meta: Dict[str, Any] = {}
        for line in front_str.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip()
                # Array handling [a, b, c]
                if v.startswith("[") and v.endswith("]"):
                    items = [it.strip().strip("'\"") for it in v[1:-1].split(",") if it.strip()]
                    meta[k] = items
                else:
                    meta[k] = v.strip("'\"")
        return meta, body

    def _parse_file(self, file_path: Path) -> Optional[CorpusDocument]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
        except Exception:
            return None

        metadata, body = self._parse_frontmatter(raw_text)
        doc = CorpusDocument(file_path, metadata, body)

        # Chunk by H2 headers (## Section)
        section_pattern = r"(^|\n)##\s+(.*?)\n"
        splits = list(re.finditer(section_pattern, body))

        if not splits:
            chunk = CorpusChunk(
                chunk_id=f"{doc.doc_id}_0",
                doc_id=doc.doc_id,
                title=doc.title,
                section_title="Full Document",
                category=doc.category,
                tags=doc.tags,
                metadata=doc.metadata,
                content=body,
                file_path=doc.file_path,
                chunk_index=0
            )
            doc.chunks.append(chunk)
            return doc

        # Intro chunk before first ##
        first_start = splits[0].start()
        intro_text = body[:first_start].strip()
        if intro_text:
            chunk = CorpusChunk(
                chunk_id=f"{doc.doc_id}_intro",
                doc_id=doc.doc_id,
                title=doc.title,
                section_title="Overview",
                category=doc.category,
                tags=doc.tags,
                metadata=doc.metadata,
                content=intro_text,
                file_path=doc.file_path,
                chunk_index=0
            )
            doc.chunks.append(chunk)

        # Iterate through H2 sections
        for i, match in enumerate(splits):
            sec_title = match.group(2).strip()
            content_start = match.end()
            content_end = splits[i + 1].start() if i + 1 < len(splits) else len(body)
            sec_content = body[content_start:content_end].strip()

            chunk = CorpusChunk(
                chunk_id=f"{doc.doc_id}_{i+1}",
                doc_id=doc.doc_id,
                title=doc.title,
                section_title=sec_title,
                category=doc.category,
                tags=doc.tags,
                metadata=doc.metadata,
                content=sec_content,
                file_path=doc.file_path,
                chunk_index=i + 1
            )
            doc.chunks.append(chunk)

        return doc

    def get_all_chunks(self) -> List[CorpusChunk]:
        all_chunks = []
        for doc in self.documents:
            all_chunks.extend(doc.chunks)
        return all_chunks

    def get_document(self, doc_id: str) -> Optional[CorpusDocument]:
        return self._doc_map.get(doc_id)

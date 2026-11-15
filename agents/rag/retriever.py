import os
import re
from pathlib import Path
from typing import List, Dict, Any
from app.config import settings

class RAGRetriever:
    """
    Lightweight, fast in-memory RAG retriever for official policy and health documents.
    Does not require heavy PyTorch or GPU dependencies to maintain strict < 512MB RAM budget.
    """
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self._load_knowledge()

    def _load_knowledge(self):
        kdir = settings.KNOWLEDGE_DIR
        if not kdir.exists():
            return

        for fpath in kdir.glob("*.md"):
            if fpath.name == "SOURCES.md":
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Extract source URL
                source_url = "https://cpcb.nic.in"
                m = re.search(r"Source URL:\s*([^\n]+)", content)
                if m:
                    source_url = m.group(1).strip()

                # Split by sections (## Headers)
                sections = re.split(r"\n(?=##\s+)", content)
                for sec in sections:
                    if not sec.strip():
                        continue
                    lines = sec.strip().split("\n")
                    header = lines[0].replace("##", "").strip() if lines[0].startswith("##") else "Overview"
                    body = "\n".join(lines[1:]).strip() if len(lines) > 1 else lines[0]
                    
                    self.chunks.append({
                        "doc_name": fpath.stem,
                        "header": header,
                        "text": sec.strip(),
                        "source_url": source_url,
                        "terms": set(re.findall(r"\w+", sec.lower()))
                    })
            except Exception as e:
                print(f"Error loading {fpath}: {e}")

    def search(self, query: str, category_filter: str = "", top_k: int = 3) -> List[Dict[str, Any]]:
        query_terms = set(re.findall(r"\w+", query.lower()))
        if not query_terms:
            return self.chunks[:top_k]

        scored = []
        for chunk in self.chunks:
            if category_filter and category_filter not in chunk["doc_name"]:
                continue
            # Term overlap score
            overlap = len(query_terms.intersection(chunk["terms"]))
            if overlap > 0:
                scored.append((overlap, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]

retriever = RAGRetriever()

def rag_search_policy(query: str) -> List[Dict[str, Any]]:
    return retriever.search(query, category_filter="grap", top_k=2)

def rag_search_health(query: str) -> List[Dict[str, Any]]:
    return retriever.search(query, category_filter="health", top_k=2)

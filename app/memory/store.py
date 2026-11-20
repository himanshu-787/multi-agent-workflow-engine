import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.memory.embedding import DeterministicFastEmbedding


class LongTermMemoryStore:
    """Manages persistent semantic vector memory for past workflow runs."""

    def __init__(self, chroma_path: str | None = None, in_memory: bool = False) -> None:
        self.embedding_fn = DeterministicFastEmbedding()
        if in_memory:
            self.client = chromadb.Client()
        else:
            db_dir = Path(chroma_path or settings.chroma_path).resolve()
            db_dir.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=str(db_dir),
                settings=ChromaSettings(anonymized_telemetry=False),
            )

        self.collection = self.client.get_or_create_collection(
            name="workflow_memories",
            embedding_function=self.embedding_fn,
        )

    def save_run(
        self,
        task: str,
        code: str,
        critique: str,
        thread_id: str | None = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        record_id = str(uuid.uuid4())
        meta = {
            "thread_id": thread_id or "",
            "timestamp": time.time(),
            "has_code": bool(code),
        }
        if metadata:
            meta.update({k: str(v) for k, v in metadata.items()})

        # We store task + code summary as document for semantic indexing
        document_text = f"Task: {task}\nCode:\n{code[:500]}\nCritique: {critique[:300]}"

        self.collection.add(
            ids=[record_id],
            documents=[document_text],
            metadatas=[meta],
        )
        return record_id

    def search(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        total_items = self.collection.count()
        if total_items == 0:
            return []

        limit = min(n_results, total_items)
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
        )

        matches = []
        if results and results["documents"] and results["documents"][0]:
            for doc, meta, doc_id in zip(
                results["documents"][0],
                results["metadatas"][0] if results["metadatas"] else [{}],
                results["ids"][0],
            ):
                matches.append({"id": doc_id, "document": doc, "metadata": meta})
        return matches

    def format_context(self, matches: List[Dict[str, Any]]) -> str:
        if not matches:
            return ""
        formatted = []
        for i, m in enumerate(matches, 1):
            formatted.append(f"--- Prior Experience #{i} ---\n{m['document']}")
        return "\n\n".join(formatted)


# Default singleton instance
default_memory_store = LongTermMemoryStore()

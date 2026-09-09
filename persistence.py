"""
persistence.py - JARVIS v6 persistence layer
Tasks, Macros, Notifications, Chat History, Vaults (ChromaDB/FAISS)
"""

import json
import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import threading

# ── Base directory for data ──
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Task Manager
# ─────────────────────────────────────────────────────────────

class TaskManager:
    def __init__(self, filepath: Path = DATA_DIR / "tasks.json"):
        self.filepath = filepath
        self._lock = threading.Lock()
        self.tasks = self._load()

    def _load(self) -> List[Dict]:
        if self.filepath.exists():
            with open(self.filepath, "r") as f:
                return json.load(f)
        return []

    def _save(self):
        with self._lock:
            with open(self.filepath, "w") as f:
                json.dump(self.tasks, f, indent=2)

    def get_all(self) -> List[Dict]:
        return self.tasks

    def add(self, text: str) -> Dict:
        task = {
            "id": str(uuid.uuid4()),
            "text": text,
            "done": False,
            "created_at": datetime.now().isoformat()
        }
        self.tasks.append(task)
        self._save()
        return task

    def toggle(self, task_id: str, done: bool) -> bool:
        for t in self.tasks:
            if t["id"] == task_id:
                t["done"] = done
                self._save()
                return True
        return False

    def delete(self, task_id: str) -> bool:
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self._save()
        return True


# ─────────────────────────────────────────────────────────────
# Macro Manager
# ─────────────────────────────────────────────────────────────

class MacroManager:
    def __init__(self, filepath: Path = DATA_DIR / "macros.json"):
        self.filepath = filepath
        self._lock = threading.Lock()
        self.macros = self._load()

    def _load(self) -> List[Dict]:
        if self.filepath.exists():
            with open(self.filepath, "r") as f:
                return json.load(f)
        return []

    def _save(self):
        with self._lock:
            with open(self.filepath, "w") as f:
                json.dump(self.macros, f, indent=2)

    def get_all(self) -> List[Dict]:
        return self.macros

    def add(self, name: str, steps: List[Dict], description: str = "") -> Dict:
        macro = {
            "name": name,
            "description": description,
            "steps": steps,
            "created_at": datetime.now().isoformat()
        }
        self.macros.append(macro)
        self._save()
        return macro

    def delete(self, name: str) -> bool:
        self.macros = [m for m in self.macros if m["name"] != name]
        self._save()
        return True

    def run(self, name: str, tool_dispatch: Dict) -> List[Dict]:
        """Execute macro steps. tool_dispatch maps tool names to functions."""
        for macro in self.macros:
            if macro["name"] == name:
                results = []
                for step in macro["steps"]:
                    tool_name = step.get("tool")
                    args = step.get("args", {})
                    if tool_name in tool_dispatch:
                        try:
                            result = tool_dispatch[tool_name](**args)
                            results.append({"tool": tool_name, "result": result, "skipped": False})
                        except Exception as e:
                            results.append({"tool": tool_name, "error": str(e), "skipped": False})
                    else:
                        results.append({"tool": tool_name, "error": "Unknown tool", "skipped": True})
                return results
        return []


# ─────────────────────────────────────────────────────────────
# Notification (Alert) Manager
# ─────────────────────────────────────────────────────────────

class NotificationManager:
    def __init__(self, filepath: Path = DATA_DIR / "notifications.json"):
        self.filepath = filepath
        self._lock = threading.Lock()
        self.notifications = self._load()

    def _load(self) -> List[Dict]:
        if self.filepath.exists():
            with open(self.filepath, "r") as f:
                return json.load(f)
        return []

    def _save(self):
        with self._lock:
            with open(self.filepath, "w") as f:
                json.dump(self.notifications, f, indent=2)

    def get_all(self) -> List[Dict]:
        return self.notifications

    def add(self, tool_name: str, args: Dict, conv_id: str = None) -> Dict:
        notif = {
            "id": str(uuid.uuid4()),
            "name": tool_name,
            "args": args,
            "conversation_id": conv_id,
            "status": "pending",  # pending, approved, denied
            "created_at": datetime.now().isoformat()
        }
        self.notifications.append(notif)
        self._save()
        return notif

    def resolve(self, notif_id: str, approved: bool) -> bool:
        for n in self.notifications:
            if n["id"] == notif_id:
                n["status"] = "approved" if approved else "denied"
                self._save()
                return True
        return False


# ─────────────────────────────────────────────────────────────
# Chat History Manager
# ─────────────────────────────────────────────────────────────

class ChatHistoryManager:
    def __init__(self, dirpath: Path = DATA_DIR / "chats"):
        self.dirpath = dirpath
        self.dirpath.mkdir(exist_ok=True)

    def _get_path(self, conv_id: str) -> Path:
        return self.dirpath / f"{conv_id}.json"

    def save(self, conv_id: str, messages: List[Dict], title: str = None):
        data = {
            "id": conv_id,
            "title": title or "Untitled",
            "messages": messages,
            "updated_at": datetime.now().timestamp()
        }
        path = self._get_path(conv_id)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def get(self, conv_id: str) -> Dict:
        path = self._get_path(conv_id)
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {"ok": False, "error": "Chat not found"}

    def list_all(self, limit: int = 50) -> List[Dict]:
        chats = []
        for f in self.dirpath.glob("*.json"):
            try:
                with open(f, "r") as fp:
                    data = json.load(fp)
                    chats.append({
                        "id": data["id"],
                        "title": data.get("title", "Untitled"),
                        "updated_at": data.get("updated_at", 0)
                    })
            except:
                pass
        chats.sort(key=lambda x: x["updated_at"], reverse=True)
        return chats[:limit]


# ─────────────────────────────────────────────────────────────
# Vault Manager (RAG with ChromaDB/FAISS fallback)
# ─────────────────────────────────────────────────────────────

class VaultManager:
    def __init__(self):
        self.vaults = {}
        self._load_vaults()
        self._init_vector_store()

    def _load_vaults(self):
        vaults_file = DATA_DIR / "vaults_index.json"
        if vaults_file.exists():
            with open(vaults_file, "r") as f:
                self.vaults = json.load(f)
        else:
            self.vaults = {}

    def _save_vaults(self):
        with open(DATA_DIR / "vaults_index.json", "w") as f:
            json.dump(self.vaults, f, indent=2)

    def _init_vector_store(self):
        """Try ChromaDB, fallback to FAISS"""
        try:
            import chromadb
            from chromadb.config import Settings
            self.store_type = "chromadb"
            self.client = chromadb.PersistentClient(path=str(DATA_DIR / "chromadb"))
            print("  ✓ Vector store: ChromaDB")
        except ImportError:
            try:
                import faiss
                import numpy as np
                self.store_type = "faiss"
                self.faiss_index = None
                self.faiss_metadata = {}
                print("  ✓ Vector store: FAISS (fallback)")
            except ImportError:
                self.store_type = None
                print("  ⚠ No vector store (ChromaDB or FAISS)")

    def index_folder(self, folder_path: str, vault_name: str) -> Dict:
        """Index all text files in a folder into the vault."""
        if self.store_type is None:
            return {"ok": False, "error": "No vector store available"}
        folder_path = Path(folder_path)
        if not folder_path.exists():
            return {"ok": False, "error": "Folder not found"}

        # Collect text files
        files = []
        for ext in [".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".csv", ".pdf"]:
            files.extend(folder_path.glob(f"*{ext}"))
        if not files:
            return {"ok": False, "error": "No supported files found"}

        # Extract text content
        chunks = []
        for f in files[:20]:  # limit for performance
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                # simple chunking by paragraphs
                paragraphs = [p for p in content.split("\n\n") if len(p) > 50]
                for para in paragraphs[:5]:
                    chunks.append({
                        "source": str(f.name),
                        "text": para[:1000],
                        "vault": vault_name
                    })
            except:
                pass

        if not chunks:
            return {"ok": False, "error": "No text content extracted"}

        # Store in vector DB
        if self.store_type == "chromadb":
            return self._index_chromadb(vault_name, chunks)
        else:
            return self._index_faiss(vault_name, chunks)

    def _index_chromadb(self, vault_name: str, chunks: List[Dict]):
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            collection_name = f"vault_{vault_name}"
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            )
            ids = [str(uuid.uuid4()) for _ in chunks]
            documents = [c["text"] for c in chunks]
            metadatas = [{"source": c["source"], "vault": c["vault"]} for c in chunks]
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            # Save vault info
            self.vaults[vault_name] = {
                "folder": str(Path(chunks[0]["source"]).parent),
                "file_count": len(chunks),
                "chunk_count": len(chunks),
                "backend": "chromadb"
            }
            self._save_vaults()
            return {"ok": True, "vault": vault_name, "chunks": len(chunks)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _index_faiss(self, vault_name: str, chunks: List[Dict]):
        try:
            import faiss
            import numpy as np
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            # Create embeddings
            texts = [c["text"] for c in chunks]
            embeddings = model.encode(texts)
            dim = embeddings.shape[1]
            index = faiss.IndexFlatL2(dim)
            index.add(np.array(embeddings).astype('float32'))
            # Store index and metadata
            faiss_dir = DATA_DIR / "faiss"
            faiss_dir.mkdir(exist_ok=True)
            faiss.write_index(index, str(faiss_dir / f"{vault_name}.index"))
            with open(faiss_dir / f"{vault_name}_meta.json", "w") as f:
                json.dump({"chunks": chunks}, f)
            self.vaults[vault_name] = {
                "folder": str(Path(chunks[0]["source"]).parent),
                "file_count": len(chunks),
                "chunk_count": len(chunks),
                "backend": "faiss"
            }
            self._save_vaults()
            return {"ok": True, "vault": vault_name, "chunks": len(chunks)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def query(self, vault_name: str, question: str, top_k: int = 5) -> Dict:
        if self.store_type is None:
            return {"ok": False, "error": "No vector store"}
        try:
            if self.store_type == "chromadb":
                collection_name = f"vault_{vault_name}"
                collection = self.client.get_collection(name=collection_name)
                results = collection.query(query_texts=[question], n_results=top_k)
                if results and results['documents']:
                    docs = results['documents'][0]
                    metas = results['metadatas'][0] if results['metadatas'] else [{}]*len(docs)
                    return {
                        "ok": True,
                        "results": [{"text": d, "source": m.get("source", "unknown")}
                                    for d, m in zip(docs, metas)]
                    }
                return {"ok": True, "results": []}
            elif self.store_type == "faiss":
                import faiss
                import numpy as np
                from sentence_transformers import SentenceTransformer
                faiss_dir = DATA_DIR / "faiss"
                index_path = faiss_dir / f"{vault_name}.index"
                meta_path = faiss_dir / f"{vault_name}_meta.json"
                if not index_path.exists():
                    return {"ok": False, "error": "Vault not found"}
                index = faiss.read_index(str(index_path))
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                model = SentenceTransformer('all-MiniLM-L6-v2')
                query_emb = model.encode([question])
                distances, indices = index.search(np.array(query_emb).astype('float32'), top_k)
                results = []
                for idx in indices[0]:
                    if idx < len(meta["chunks"]):
                        results.append({
                            "text": meta["chunks"][idx]["text"],
                            "source": meta["chunks"][idx]["source"]
                        })
                return {"ok": True, "results": results}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {"ok": False, "error": "Unsupported store type"}

    def list_vaults(self) -> List[Dict]:
        return [{"name": k, **v} for k, v in self.vaults.items()]

    def delete_vault(self, name: str) -> bool:
        if name in self.vaults:
            del self.vaults[name]
            self._save_vaults()
            # Also delete physical data
            if self.store_type == "chromadb":
                try:
                    self.client.delete_collection(f"vault_{name}")
                except:
                    pass
            elif self.store_type == "faiss":
                faiss_dir = DATA_DIR / "faiss"
                for f in faiss_dir.glob(f"{name}.*"):
                    f.unlink()
            return True
        return False
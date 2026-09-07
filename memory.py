"""Semantic memory backed by SQLite and Gemini embeddings.

Inspired by the Anthropic memory tool: the model manipulates virtual files
under /memories through a command enum (view, create, str_replace, insert,
delete, rename), plus a semantic `search` command that ranks entries by
cosine similarity of their gemini-embedding-2 vectors.
"""

import json
import sqlite3
import numpy as np

from typing import List, Optional

from google.genai import Client
from google.genai.types import EmbedContentConfig

MEMORY_ROOT = "/memories"
EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIM = 768


class SemanticMemory:
    def __init__(self, client: Client, db_path: str = "memories.db"):
        self.client = client
        self.db = sqlite3.connect(db_path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS memories ("
            "  path TEXT PRIMARY KEY,"
            "  content TEXT NOT NULL,"
            "  embedding BLOB NOT NULL"
            ")"
        )
        self.db.commit()

    async def _embed(self, text: str) -> bytes:
        response = await self.client.aio.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
        )
        vector = np.asarray(response.embeddings[0].values, dtype=np.float32)
        # dimensions below 3072 are not pre-normalized by the API
        vector /= np.linalg.norm(vector)
        return vector.tobytes()

    def _validate(self, path: str) -> str:
        if not path.startswith(MEMORY_ROOT):
            raise ValueError(f"path must start with {MEMORY_ROOT}: {path}")
        if ".." in path:
            raise ValueError(f"path traversal is not allowed: {path}")
        return path

    def _get(self, path: str) -> Optional[str]:
        row = self.db.execute(
            "SELECT content FROM memories WHERE path = ?", (path,)
        ).fetchone()
        return row[0] if row else None

    async def _put(self, path: str, content: str):
        self.db.execute(
            "INSERT INTO memories (path, content, embedding) VALUES (?, ?, ?) "
            "ON CONFLICT(path) DO UPDATE SET content=excluded.content, "
            "embedding=excluded.embedding",
            (path, content, await self._embed(content)),
        )
        self.db.commit()

    @staticmethod
    def _numbered(content: str) -> str:
        lines = content.rstrip("\n").split("\n")
        return "\n".join(f"{i + 1:6d}\t{line}" for i, line in enumerate(lines))

    # -- commands -----------------------------------------------------------

    def view(self, path: str, view_range: Optional[List[int]] = None) -> str:
        if path == MEMORY_ROOT:
            rows = self.db.execute(
                "SELECT path, length(content) FROM memories ORDER BY path"
            ).fetchall()
            listing = "\n".join(f"{size / 1024:.1f}K\t{p}" for p, size in rows)
            return f"Entries in {MEMORY_ROOT}:\n{listing or '(empty)'}"

        content = self._get(path)
        if content is None:
            return f"The path {path} does not exist. Please provide a valid path."
        if view_range is not None:
            start, end = view_range
            lines = content.rstrip("\n").split("\n")
            end = len(lines) if end == -1 else end
            content = "\n".join(lines[start - 1:end])
            return f"Here's the content of {path} (lines {start}-{end}):\n" \
                   + self._numbered(content)
        return f"Here's the content of {path} with line numbers:\n" \
               + self._numbered(content)

    async def create(self, path: str, file_text: str) -> str:
        await self._put(path, file_text)
        return f"File created successfully at: {path}"

    async def str_replace(self, path: str, old_str: str, new_str: str = "") -> str:
        content = self._get(path)
        if content is None:
            return f"Error: The path {path} does not exist. Please provide a valid path."
        occurrences = content.count(old_str)
        if occurrences == 0:
            return (f"No replacement was performed, old_str `{old_str}` "
                    f"did not appear verbatim in {path}.")
        if occurrences > 1:
            return (f"No replacement was performed. Multiple occurrences of "
                    f"old_str `{old_str}` in {path}. Please ensure it is unique.")
        await self._put(path, content.replace(old_str, new_str, 1))
        return "The memory file has been edited."

    async def insert(self, path: str, insert_line: int, insert_text: str) -> str:
        content = self._get(path)
        if content is None:
            return f"Error: The path {path} does not exist"
        lines = content.split("\n")
        if not 0 <= insert_line <= len(lines):
            return (f"Error: Invalid `insert_line` parameter: {insert_line}. "
                    f"It should be within the range of lines of the file: "
                    f"[0, {len(lines)}]")
        lines.insert(insert_line, insert_text.rstrip("\n"))
        await self._put(path, "\n".join(lines))
        return f"The file {path} has been edited."

    def delete(self, path: str) -> str:
        if path == MEMORY_ROOT:
            return f"Error: cannot delete the {MEMORY_ROOT} directory itself"
        cursor = self.db.execute("DELETE FROM memories WHERE path = ?", (path,))
        self.db.commit()
        if cursor.rowcount == 0:
            return f"Error: The path {path} does not exist"
        return f"Successfully deleted {path}"

    def rename(self, old_path: str, new_path: str) -> str:
        if self._get(old_path) is None:
            return f"Error: The path {old_path} does not exist"
        if self._get(new_path) is not None:
            return f"Error: The destination {new_path} already exists"
        self.db.execute(
            "UPDATE memories SET path = ? WHERE path = ?", (new_path, old_path)
        )
        self.db.commit()
        return f"Successfully renamed {old_path} to {new_path}"

    async def search(self, query: str, top_k: int = 5) -> str:
        rows = self.db.execute(
            "SELECT path, content, embedding FROM memories"
        ).fetchall()
        if not rows:
            return "The memory is empty: no entries to search."
        query_vector = np.frombuffer(await self._embed(query), dtype=np.float32)
        matrix = np.stack([
            np.frombuffer(embedding, dtype=np.float32) for _, _, embedding in rows
        ])
        # vectors are unit-normalized at write time: dot product = cosine
        scores = matrix @ query_vector
        ranked = sorted(zip(scores, rows), key=lambda item: -item[0])[:top_k]
        results = [
            {"path": path, "score": round(float(score), 4), "content": content}
            for score, (path, content, _) in ranked
        ]
        return json.dumps(results, ensure_ascii=False, indent=2)

    # -- dispatch -----------------------------------------------------------

    async def execute(self, command: str, **arguments) -> str:
        for key in ("path", "old_path", "new_path"):
            if key in arguments:
                self._validate(arguments[key])

        match command:
            case "view":
                return self.view(**arguments)
            case "create":
                return await self.create(**arguments)
            case "str_replace":
                return await self.str_replace(**arguments)
            case "insert":
                return await self.insert(**arguments)
            case "delete":
                return self.delete(**arguments)
            case "rename":
                return self.rename(**arguments)
            case "search":
                return await self.search(**arguments)
            case _:
                return f"Error: unknown command {command}"

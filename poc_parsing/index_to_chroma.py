import html
import json
import os
import re
from pathlib import Path

ROOT = Path("/home/ellena89/chatbot/poc_parsing")
CACHE = ROOT / ".cache"
CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE))
os.environ.setdefault("HF_HOME", str(CACHE / "huggingface"))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(CACHE / "huggingface" / "hub"))
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "0")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY_IMPLEMENTATION", "none")

from sentence_transformers import SentenceTransformer
import chromadb

MODEL_ID = "BAAI/bge-m3"
COLLECTION = "manual_chunks"
CHROMA_DIR = ROOT / "chroma_db"
SOURCES = [ROOT / "merged_ko.json", ROOT / "merged_en.json"]
QUERY = "공구경보정"
EXTRA_QUERIES = ["새 프로그램", "소프트키"]
EXPECTED = 124
TAG_RE = re.compile(r"<[^>]+>")


def html_to_text(raw: str) -> str:
    text = TAG_RE.sub(" ", raw or "")
    text = html.unescape(text)
    return " ".join(text.split())


def nested(chunk: dict, key: str) -> dict:
    blob = chunk.get(key)
    return blob if isinstance(blob, dict) else {}


def image_path_of(chunk: dict) -> str:
    for key in ("figure", "ui_screen"):
        path = nested(chunk, key).get("image_path")
        if path:
            return str(path)
    return ""


def note_of(chunk: dict, kind: str) -> str:
    text = (chunk.get("note") or "").strip()
    if not text:
        text = (nested(chunk, kind).get("note") or "").strip()
    return text


def embed_text(chunk: dict) -> str:
    kind = chunk.get("chunk_type")
    if kind == "text":
        text = (chunk.get("text") or "").strip()
    elif kind == "table":
        text = html_to_text(nested(chunk, "table").get("html") or "")
        if not text:
            text = (chunk.get("text") or "").strip()
    elif kind in {"figure", "ui_screen"}:
        note = note_of(chunk, kind)
        body = (chunk.get("text") or "").strip()
        if note and body:
            text = f"{note}. 화면 내용: {body}"
        else:
            text = note or body
    else:
        text = (chunk.get("text") or "").strip()
    return text or f"[{kind or 'chunk'}]"


def meta_value(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        return value
    return json.dumps(value, ensure_ascii=False)


def to_metadata(chunk: dict) -> dict:
    keys = [
        "doc_id",
        "lang",
        "chunk_id",
        "chunk_type",
        "page",
        "section_path",
        "text",
        "table",
        "figure",
        "ui_screen",
        "source_anchor",
        "note",
    ]
    meta = {key: meta_value(chunk.get(key)) for key in keys}
    meta["image_path"] = image_path_of(chunk)
    return meta


def load_chunks() -> list[dict]:
    chunks = []
    for path in SOURCES:
        data = json.loads(path.read_text(encoding="utf-8"))
        print(f"{path.name}: {len(data)} chunks", flush=True)
        chunks.extend(data)
    return chunks


def main() -> None:
    chunks = load_chunks()
    documents = [embed_text(c) for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    if len(ids) != len(set(ids)):
        raise SystemExit("chunk_id 중복")
    empty = sum(1 for d in documents if d.startswith("["))
    print(f"embed texts ready n={len(documents)} placeholder={empty}", flush=True)

    print("BAAI/bge-m3 모델을 로드합니다.", flush=True)
    print("첫 실행이면 Hugging Face에서 모델을 받으므로 수 분이 걸릴 수 있습니다.", flush=True)
    model = SentenceTransformer(MODEL_ID)
    print(f"모델 로드 완료. device={model.device}", flush=True)

    print("임베딩 변환 중...", flush=True)
    vectors = model.encode(
        documents,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    print(f"vector shape={vectors.shape}", flush=True)

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    existing = {c.name for c in client.list_collections()}
    if COLLECTION in existing:
        client.delete_collection(COLLECTION)
        print(f"기존 컬렉션 {COLLECTION} 삭제", flush=True)
    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=ids,
        embeddings=vectors.tolist(),
        documents=documents,
        metadatas=[to_metadata(c) for c in chunks],
    )
    count = collection.count()
    print(f"collection={COLLECTION} count={count} expected={EXPECTED}", flush=True)
    if count != EXPECTED:
        raise SystemExit(f"저장 개수 불일치: {count} != {EXPECTED}")

    def run_query(q: str, n_results: int = 3) -> None:
        qvec = model.encode(
            [q],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        result = collection.query(
            query_embeddings=qvec.tolist(),
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        print(f'query="{q}" top {n_results}:', flush=True)
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists), start=1):
            preview = " ".join((doc or "").split())[:180]
            print(
                f"  #{i} page={meta.get('page')} chunk_type={meta.get('chunk_type')} "
                f"chunk_id={meta.get('chunk_id')} dist={dist:.4f}",
                flush=True,
            )
            print(f"     {preview}", flush=True)

    run_query(QUERY, n_results=3)
    for extra in EXTRA_QUERIES:
        run_query(extra, n_results=5)


if __name__ == "__main__":
    main()

import json
import os
import time
from pathlib import Path

ROOT = Path("/home/ellena89/chatbot/poc_parsing")
CACHE = ROOT / ".cache"
CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE))
os.environ.setdefault("HF_HOME", str(CACHE / "huggingface"))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(CACHE / "huggingface" / "hub"))
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "0")

from sentence_transformers import SentenceTransformer, util

MODEL_ID = "BAAI/bge-m3"
N_EACH = 3


def load_texts(path: Path, n: int) -> list[str]:
    chunks = json.loads(path.read_text(encoding="utf-8"))
    texts = []
    for chunk in chunks:
        if chunk.get("chunk_type") != "text":
            continue
        text = (chunk.get("text") or "").strip()
        if not text:
            continue
        texts.append(f"[{chunk['chunk_id']}] {text}")
        if len(texts) >= n:
            break
    if len(texts) < n:
        raise SystemExit(f"{path.name}: text 청크가 {len(texts)}개뿐입니다")
    return texts


def main() -> None:
    started = time.perf_counter()
    print("BAAI/bge-m3 모델을 로드합니다.", flush=True)
    print("첫 실행이면 Hugging Face에서 모델을 받으므로 수 분이 걸릴 수 있습니다.", flush=True)

    model = SentenceTransformer(MODEL_ID)
    print(f"모델 로드 완료. device={model.device}", flush=True)

    ko_texts = load_texts(ROOT / "merged_ko.json", N_EACH)
    en_texts = load_texts(ROOT / "merged_en.json", N_EACH)
    print("--- ko samples ---", flush=True)
    for t in ko_texts:
        print(t[:180].replace("\n", " "), flush=True)
    print("--- en samples ---", flush=True)
    for t in en_texts:
        print(t[:180].replace("\n", " "), flush=True)

    all_texts = ko_texts + en_texts
    print("임베딩 변환 중...", flush=True)
    vectors = model.encode(
        all_texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    print(f"vector shape={vectors.shape}", flush=True)

    ko_vec = vectors[0]
    en_vec = vectors[N_EACH]
    score = util.cos_sim(ko_vec, en_vec).item()
    print(f"cosine(ko[0], en[0])={score:.4f}", flush=True)

    elapsed = time.perf_counter() - started
    print(f"elapsed_sec={elapsed:.1f}", flush=True)


if __name__ == "__main__":
    main()

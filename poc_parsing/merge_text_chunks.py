import json
import os
import traceback
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

ROOT = Path("/home/ellena89/chatbot/poc_parsing")
CACHE = ROOT / ".cache"
CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE))
os.environ.setdefault("HF_HOME", str(CACHE / "huggingface"))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(CACHE / "huggingface" / "hub"))
os.environ.setdefault("TORCH_HOME", str(CACHE / "torch"))

from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter
from docling_core.types.doc.items.node import DocItem
from docling_core.types.doc.items.picture.picture import PictureItem
from docling_core.types.doc.items.table.table import TableItem

settings.cache_dir = CACHE / "docling"

JOBS = [
    {
        "pdf": ROOT / "sample_ko.pdf",
        "src": ROOT / "normalized_ko.json",
        "out": ROOT / "merged_ko.json",
        "lang": "ko",
    },
    {
        "pdf": ROOT / "sample_en.pdf",
        "src": ROOT / "normalized_en.json",
        "out": ROOT / "merged_en.json",
        "lang": "en",
    },
]

TEXT_LABELS = {
    "text",
    "list_item",
    "section_header",
    "title",
    "caption",
    "paragraph",
    "formula",
    "code",
    "footnote",
}
Y_GAP = 30
MERGE_MAX = 800
SPLIT_OVER = 2000
SENTENCE_PUNCT = ".!?。"


def to_tl_bbox(item: DocItem, doc) -> tuple[int, tuple[float, float, float, float]] | None:
    if not item.prov:
        return None
    prov = item.prov[0]
    dpage = doc.pages.get(prov.page_no)
    height = dpage.size.height if dpage is not None else 0.0
    bb = prov.bbox.to_top_left_origin(height) if height else prov.bbox
    return prov.page_no, (bb.l, bb.t, bb.r, bb.b)


def y_dist(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ay0, ay1 = min(a[1], a[3]), max(a[1], a[3])
    by0, by1 = min(b[1], b[3]), max(b[1], b[3])
    if ay1 < by0:
        return by0 - ay1
    if by1 < ay0:
        return ay0 - by1
    return 0.0


def collect_layout(pdf_path: Path, converter: DocumentConverter):
    result = converter.convert(pdf_path)
    doc = result.document
    text_q: dict[tuple[int, str], list] = defaultdict(list)
    anchors: dict[int, list] = defaultdict(list)
    for item, _level in doc.iterate_items():
        if not isinstance(item, DocItem):
            continue
        loc = to_tl_bbox(item, doc)
        if loc is None:
            continue
        page, bbox = loc
        label = str(getattr(item, "label", ""))
        if isinstance(item, (PictureItem, TableItem)) or label in {"picture", "chart", "table"}:
            kind = "table" if (isinstance(item, TableItem) or label == "table") else "figure"
            anchors[page].append({"kind": kind, "bbox": bbox})
        if label in TEXT_LABELS:
            text = (getattr(item, "text", "") or "").strip()
            text_q[(page, text)].append(bbox)
    return text_q, anchors


def attach_text_bbox(chunks: list[dict], text_q: dict) -> None:
    leftover = {k: list(v) for k, v in text_q.items()}
    for chunk in chunks:
        if chunk.get("chunk_type") != "text":
            continue
        key = (chunk["page"], (chunk.get("text") or "").strip())
        pool = leftover.get(key)
        if pool:
            chunk["_bbox"] = pool.pop(0)
        else:
            chunk["_bbox"] = None


def closest_anchor(chunk: dict, anchors: dict) -> dict | None:
    bbox = chunk.get("_bbox")
    if bbox is None:
        return None
    page = chunk["page"]
    best = None
    best_d = None
    for anc in anchors.get(page, []):
        dist = y_dist(bbox, anc["bbox"])
        if dist > Y_GAP:
            continue
        if best_d is None or dist < best_d:
            best = anc
            best_d = dist
    return best


def append_note(target: dict, text: str) -> None:
    blob = target.get(target["chunk_type"])
    if isinstance(blob, dict):
        prev = (blob.get("note") or "").strip()
        blob["note"] = (prev + " " + text).strip() if prev else text
    prev = (target.get("note") or "").strip()
    target["note"] = (prev + " " + text).strip() if prev else text


def absorb_nearby_text(chunks: list[dict], anchors: dict) -> tuple[list[dict], int]:
    ft_by_page_kind: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for chunk in chunks:
        kind = chunk.get("chunk_type")
        if kind in {"figure", "table"}:
            ft_by_page_kind[(chunk["page"], kind)].append(chunk)

    kept: list[dict] = []
    absorbed = 0
    for chunk in chunks:
        if chunk.get("chunk_type") != "text":
            kept.append(chunk)
            continue
        anc = closest_anchor(chunk, anchors)
        if anc is None:
            kept.append(chunk)
            continue
        candidates = ft_by_page_kind.get((chunk["page"], anc["kind"])) or []
        if not candidates:
            kept.append(chunk)
            continue
        target = candidates[0]
        if len(candidates) > 1 and chunk.get("_bbox") is not None:
            # JSON figure already has bbox; pick nearest by that if present
            scored = []
            for cand in candidates:
                fb = None
                if cand["chunk_type"] == "figure" and cand.get("figure"):
                    bb = cand["figure"].get("bbox")
                    if bb and len(bb) == 4:
                        fb = tuple(bb)
                scored.append((0.0 if fb is None else y_dist(chunk["_bbox"], fb), cand))
            scored.sort(key=lambda x: x[0])
            target = scored[0][1]
        append_note(target, chunk.get("text") or "")
        absorbed += 1
    return kept, absorbed


def pack_texts(texts: list[str], max_len: int = MERGE_MAX) -> list[str]:
    out: list[str] = []
    buf = ""
    for raw in texts:
        piece = raw.strip()
        if not piece:
            continue
        if not buf:
            buf = piece
            continue
        candidate = f"{buf} {piece}"
        if len(candidate) <= max_len:
            buf = candidate
        else:
            out.append(buf)
            buf = piece
    if buf:
        out.append(buf)
    return out


def split_overlong(text: str, limit: int = SPLIT_OVER) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    rest = text
    while len(rest) > limit:
        mid = len(rest) // 2
        best = -1
        best_dist = 10**9
        for i, ch in enumerate(rest):
            if ch not in SENTENCE_PUNCT:
                continue
            dist = abs(i - mid)
            if 0 < i < len(rest) - 1 and dist < best_dist:
                best = i
                best_dist = dist
        if best < 0:
            best = mid
        left = rest[: best + 1].strip()
        right = rest[best + 1 :].strip()
        if not left or not right:
            parts.append(rest)
            rest = ""
            break
        parts.append(left)
        rest = right
    if rest:
        parts.append(rest)
    return parts


def make_text_chunk(template: dict, text: str) -> dict:
    chunk = {
        "doc_id": template["doc_id"],
        "lang": template["lang"],
        "chunk_id": "",
        "chunk_type": "text",
        "page": template["page"],
        "section_path": [],
        "text": text,
        "table": None,
        "figure": None,
        "ui_screen": None,
        "source_anchor": f"{template['source_anchor'].split('#')[0]}#page={template['page']}",
    }
    return chunk


def merge_consecutive_text(chunks: list[dict]) -> list[dict]:
    out: list[dict] = []
    i = 0
    n = len(chunks)
    while i < n:
        cur = chunks[i]
        if cur.get("chunk_type") != "text":
            cleaned = {k: v for k, v in cur.items() if not k.startswith("_")}
            out.append(cleaned)
            i += 1
            continue
        group = [cur]
        page = cur["page"]
        i += 1
        while i < n and chunks[i].get("chunk_type") == "text" and chunks[i]["page"] == page:
            group.append(chunks[i])
            i += 1
        packed = pack_texts([g.get("text") or "" for g in group])
        split: list[str] = []
        for block in packed:
            split.extend(split_overlong(block))
        for text in split:
            out.append(make_text_chunk(group[0], text))
    return out


def reassign_ids(chunks: list[dict], lang: str) -> None:
    seq: dict[int, int] = {}
    for chunk in chunks:
        page = chunk["page"]
        seq[page] = seq.get(page, 0) + 1
        chunk["chunk_id"] = f"{lang}_p{page:04d}_c{seq[page]:02d}"


def text_stats(chunks: list[dict]) -> str:
    lens = [len(c.get("text") or "") for c in chunks if c.get("chunk_type") == "text"]
    if not lens:
        return "text=0"
    return (
        f"text={len(lens)} len min={min(lens)} max={max(lens)} "
        f"mean={mean(lens):.1f} median={median(lens):.1f}"
    )


def process_one(job: dict, converter: DocumentConverter) -> None:
    chunks = json.loads(job["src"].read_text(encoding="utf-8"))
    before_n = len(chunks)
    before_text = sum(1 for c in chunks if c.get("chunk_type") == "text")
    text_q, anchors = collect_layout(job["pdf"], converter)
    attach_text_bbox(chunks, text_q)
    kept, absorbed = absorb_nearby_text(chunks, anchors)
    merged = merge_consecutive_text(kept)
    reassign_ids(merged, job["lang"])
    job["out"].write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    after_n = len(merged)
    print(f"=== {job['lang']} ===", flush=True)
    print(f"absorbed into figure/table note: {absorbed}", flush=True)
    print(f"chunks before={before_n} (text={before_text}) after={after_n}", flush=True)
    print(f"after {text_stats(merged)} -> {job['out'].name}", flush=True)


def main() -> None:
    converter = DocumentConverter()
    for job in JOBS:
        process_one(job, converter)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise

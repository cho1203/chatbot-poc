import json
import os
import traceback
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path("/home/ellena89/chatbot/poc_parsing")
CACHE = ROOT / ".cache"
CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE))
os.environ.setdefault("HF_HOME", str(CACHE / "huggingface"))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(CACHE / "huggingface" / "hub"))
os.environ.setdefault("TORCH_HOME", str(CACHE / "torch"))

import pymupdf
from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter
from docling_core.types.doc.items.node import DocItem
from docling_core.types.doc.items.picture.picture import PictureItem
from docling_core.types.doc.items.table.table import TableItem

settings.cache_dir = CACHE / "docling"

JOBS = [
    {
        "pdf": ROOT / "sample_ko.pdf",
        "doc_id": "B-64484KO-2",
        "lang": "ko",
        "out": ROOT / "normalized_ko.json",
    },
    {
        "pdf": ROOT / "sample_en.pdf",
        "doc_id": "B-63874EN-2",
        "lang": "en",
        "out": ROOT / "normalized_en.json",
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
UI_TOP_GAP = 50
RENDER_DPI = 200


@dataclass
class Located:
    item: DocItem
    page: int
    bbox: tuple[float, float, float, float]
    label: str


def item_label(item: DocItem) -> str:
    label = getattr(item, "label", None)
    return str(label) if label is not None else type(item).__name__


def to_tl_bbox(item: DocItem, doc) -> tuple[int, tuple[float, float, float, float]] | None:
    if not item.prov:
        return None
    prov = item.prov[0]
    page_no = prov.page_no
    dpage = doc.pages.get(page_no)
    height = dpage.size.height if dpage is not None else 0.0
    bb = prov.bbox.to_top_left_origin(height) if height else prov.bbox
    return page_no, (bb.l, bb.t, bb.r, bb.b)


def is_ui_word(word: str) -> bool:
    if not word:
        return True
    for ch in word:
        if ch.isalpha() and not ("A" <= ch <= "Z"):
            return False
    return True


def is_ui_table(table: TableItem) -> bool:
    if table.data.num_rows != 1:
        return False
    words: list[str] = []
    for row in table.data.grid:
        for cell in row:
            words.extend((cell.text or "").split())
    if not words:
        return False
    return all(is_ui_word(word) for word in words)


def table_cell_texts(table: TableItem) -> list[str]:
    parts: list[str] = []
    for row in table.data.grid:
        for cell in row:
            text = (cell.text or "").strip()
            if text:
                parts.append(text)
    return parts


def table_payload(table: TableItem, doc) -> dict:
    grid = table.data.grid
    columns = [cell.text or "" for cell in grid[0]] if grid else []
    rows = [[cell.text or "" for cell in row] for row in grid[1:]] if grid else []
    html = table.export_to_html(doc=doc) if grid else ""
    return {"columns": columns, "rows": rows, "html": html}


def union_bbox(
    boxes: list[tuple[float, float, float, float]],
) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def cluster_ui(candidates: list[Located]) -> list[list[Located]]:
    by_page: dict[int, list[Located]] = defaultdict(list)
    for item in candidates:
        by_page[item.page].append(item)
    clusters: list[list[Located]] = []
    for group in by_page.values():
        unused = list(group)
        while unused:
            seed = unused.pop(0)
            cluster = [seed]
            changed = True
            while changed:
                changed = False
                keep: list[Located] = []
                for other in unused:
                    if any(abs(other.bbox[1] - member.bbox[1]) <= UI_TOP_GAP for member in cluster):
                        cluster.append(other)
                        changed = True
                    else:
                        keep.append(other)
                unused = keep
            clusters.append(cluster)
    return clusters


def empty_fields() -> dict:
    return {"table": None, "figure": None, "ui_screen": None}


def make_chunk(
    *,
    doc_id: str,
    lang: str,
    pdf_name: str,
    page: int,
    seq: int,
    chunk_type: str,
    text: str,
    table=None,
    figure=None,
    ui_screen=None,
) -> dict:
    chunk = {
        "doc_id": doc_id,
        "lang": lang,
        "chunk_id": f"{lang}_p{page:04d}_c{seq:02d}",
        "chunk_type": chunk_type,
        "page": page,
        "section_path": [],
        "text": text,
        **empty_fields(),
        "source_anchor": f"{pdf_name}#page={page}",
    }
    if table is not None:
        chunk["table"] = table
    if figure is not None:
        chunk["figure"] = figure
    if ui_screen is not None:
        chunk["ui_screen"] = ui_screen
    return chunk


def render_image(
    pdf_doc: pymupdf.Document,
    page: int,
    bbox: tuple[float, float, float, float],
    out_path: Path,
) -> None:
    fitz_page = pdf_doc[page - 1]
    rect = pymupdf.Rect(*bbox) & fitz_page.rect
    if rect.is_empty or rect.width < 1 or rect.height < 1:
        rect = fitz_page.rect
    else:
        rect = pymupdf.Rect(rect.x0 - 2, rect.y0 - 2, rect.x1 + 2, rect.y1 + 2) & fitz_page.rect
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pix = fitz_page.get_pixmap(clip=rect, dpi=RENDER_DPI)
    pix.save(out_path)


def next_seq(counters: dict[int, int], page: int) -> int:
    counters[page] = counters.get(page, 0) + 1
    return counters[page]


def next_image_n(counters: dict[tuple[int, str], int], page: int, kind: str) -> int:
    key = (page, kind)
    counters[key] = counters.get(key, 0) + 1
    return counters[key]


def normalize_one(job: dict, converter: DocumentConverter) -> list[dict]:
    pdf_path: Path = job["pdf"]
    doc_id = job["doc_id"]
    lang = job["lang"]
    result = converter.convert(pdf_path)
    doc = result.document
    pdf_doc = pymupdf.open(pdf_path)

    located: list[Located] = []
    for item, _level in doc.iterate_items():
        if not isinstance(item, DocItem):
            continue
        loc = to_tl_bbox(item, doc)
        if loc is None:
            continue
        page, bbox = loc
        located.append(Located(item=item, page=page, bbox=bbox, label=item_label(item)))

    ui_candidates = [
        loc for loc in located if loc.label == "table" and isinstance(loc.item, TableItem) and is_ui_table(loc.item)
    ]
    ui_clusters = cluster_ui(ui_candidates)
    cluster_of: dict[str, int] = {}
    for idx, cluster in enumerate(ui_clusters):
        for loc in cluster:
            cluster_of[loc.item.self_ref] = idx
    emitted_clusters: set[int] = set()

    chunks: list[dict] = []
    page_seq: dict[int, int] = {}
    image_seq: dict[tuple[int, str], int] = {}

    try:
        for loc in located:
            label = loc.label
            page = loc.page
            if label == "table" and loc.item.self_ref in cluster_of:
                cid = cluster_of[loc.item.self_ref]
                if cid in emitted_clusters:
                    continue
                emitted_clusters.add(cid)
                cluster = ui_clusters[cid]
                bbox = union_bbox([m.bbox for m in cluster])
                n = next_image_n(image_seq, page, "ui")
                rel = f"images/{lang}/p{page:04d}_ui{n:02d}.png"
                render_image(pdf_doc, page, bbox, ROOT / rel)
                texts = []
                for member in cluster:
                    texts.extend(table_cell_texts(member.item))
                chunks.append(
                    make_chunk(
                        doc_id=doc_id,
                        lang=lang,
                        pdf_name=pdf_path.name,
                        page=page,
                        seq=next_seq(page_seq, page),
                        chunk_type="ui_screen",
                        text=" ".join(texts),
                        ui_screen={
                            "image_path": rel,
                            "bbox": list(bbox),
                            "note": "소프트키 화면(재분류됨)",
                        },
                    )
                )
                continue

            if label == "table" and isinstance(loc.item, TableItem):
                payload = table_payload(loc.item, doc)
                chunks.append(
                    make_chunk(
                        doc_id=doc_id,
                        lang=lang,
                        pdf_name=pdf_path.name,
                        page=page,
                        seq=next_seq(page_seq, page),
                        chunk_type="table",
                        text=" ".join(table_cell_texts(loc.item)),
                        table=payload,
                    )
                )
                continue

            if label in {"picture", "chart"} and isinstance(loc.item, PictureItem):
                n = next_image_n(image_seq, page, "f")
                rel = f"images/{lang}/p{page:04d}_f{n:02d}.png"
                render_image(pdf_doc, page, loc.bbox, ROOT / rel)
                caption = loc.item.caption_text(doc) or getattr(loc.item, "text", "") or ""
                chunks.append(
                    make_chunk(
                        doc_id=doc_id,
                        lang=lang,
                        pdf_name=pdf_path.name,
                        page=page,
                        seq=next_seq(page_seq, page),
                        chunk_type="figure",
                        text=caption,
                        figure={"image_path": rel, "bbox": list(loc.bbox)},
                    )
                )
                continue

            if label in TEXT_LABELS:
                text = (getattr(loc.item, "text", "") or "").strip()
                if not text:
                    continue
                chunks.append(
                    make_chunk(
                        doc_id=doc_id,
                        lang=lang,
                        pdf_name=pdf_path.name,
                        page=page,
                        seq=next_seq(page_seq, page),
                        chunk_type="text",
                        text=text,
                    )
                )
    finally:
        pdf_doc.close()
    return chunks


def count_types(chunks: list[dict]) -> str:
    counts = {"text": 0, "table": 0, "figure": 0, "ui_screen": 0}
    for chunk in chunks:
        kind = chunk["chunk_type"]
        if kind in counts:
            counts[kind] += 1
    return ", ".join(f"{k}={v}" for k, v in counts.items())


def report_softkey_pages(chunks: list[dict], pages: tuple[int, ...] = (8, 9, 11)) -> None:
    print(f"--- page {','.join(str(p) for p in pages)} ---", flush=True)
    leftover = 0
    moved = 0
    for chunk in chunks:
        if chunk["page"] not in pages:
            continue
        kind = chunk["chunk_type"]
        if kind == "ui_screen":
            moved += 1
            print(
                f"ui_screen page={chunk['page']} chunk_id={chunk['chunk_id']} "
                f"text={chunk.get('text', '')[:80]}",
                flush=True,
            )
        elif kind == "table":
            payload = chunk.get("table") or {}
            cols = payload.get("columns") or []
            rows = payload.get("rows") or []
            n_rows = 1 + len(rows) if cols else len(rows)
            if n_rows == 1:
                leftover += 1
            print(
                f"table page={chunk['page']} rows={n_rows} cols={len(cols)} "
                f"chunk_id={chunk['chunk_id']}",
                flush=True,
            )
    print(f"page 8,9,11 ui_screen={moved}, remaining 1-row tables={leftover}", flush=True)


def main() -> None:
    converter = DocumentConverter()
    for job in JOBS:
        chunks = normalize_one(job, converter)
        job["out"].write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{job['lang']}: {count_types(chunks)} -> {job['out'].name}", flush=True)
        if job["lang"] == "en":
            report_softkey_pages(chunks)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise

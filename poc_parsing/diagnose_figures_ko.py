import os
import re
import traceback
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
from docling_core.types.doc.common.content_layer import ContentLayer
from docling_core.types.doc.items.node import DocItem
from docling_core.types.doc.items.picture.picture import PictureItem

settings.cache_dir = CACHE / "docling"

KO_PDF = Path("/home/ellena89/chatbot/uploads/manual_1.pdf")
CANDIDATES = ROOT / "real_figure_candidates_ko.txt"
MINI_PDF = ROOT / "sample_ko_figures.pdf"
OUT_DIR = ROOT / "diagnose"
DPI = 150
ALL_LAYERS = set(ContentLayer)
CAPTION_RE = re.compile(r"그림\s*\d+(?:\.\d+)*")
PICTURE_LABELS = {"picture", "chart"}


def open_ko_pdf(path: Path) -> pymupdf.Document:
    doc = pymupdf.open(path)
    if doc.needs_pass:
        result = doc.authenticate("")
        if result == 0:
            doc.close()
            raise SystemExit(
                f"암호화된 PDF를 빈 비밀번호로 열 수 없습니다: {path.name} "
                f'(authenticate("")={result})'
            )
    return doc


def read_pages(path: Path) -> list[int]:
    pages: list[int] = []
    seen: set[int] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        page = int(line.split(":", 1)[0].strip())
        if page in seen:
            continue
        seen.add(page)
        pages.append(page)
    if not pages:
        raise SystemExit(f"{path.name}: 페이지 번호가 없습니다")
    return pages


def extract_mini_pdf(page_numbers: list[int], out_path: Path) -> None:
    src = open_ko_pdf(KO_PDF)
    try:
        dst = pymupdf.open()
        for num in page_numbers:
            if num < 1 or num > src.page_count:
                src.close()
                dst.close()
                raise SystemExit(
                    f"{KO_PDF.name}: 페이지 {num}은 범위 밖입니다 (1~{src.page_count})"
                )
            dst.insert_pdf(src, from_page=num - 1, to_page=num - 1)
        dst.save(out_path)
        dst.close()
    finally:
        src.close()
    print(
        f"{out_path.name}: {out_path.stat().st_size} bytes, pages={len(page_numbers)}",
        flush=True,
    )


def render_pages(page_numbers: list[int]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src = open_ko_pdf(KO_PDF)
    try:
        for page in page_numbers:
            pix = src[page - 1].get_pixmap(dpi=DPI)
            out = OUT_DIR / f"ko_full_p{page}.png"
            pix.save(out)
            print(f"{out.name}: {out.stat().st_size} bytes", flush=True)
    finally:
        src.close()


def item_label(item) -> str:
    label = getattr(item, "label", None)
    if label is None:
        return type(item).__name__
    return str(label)


def bbox_str(box) -> str:
    if box is None:
        return "()"
    x0, y0, x1, y1 = box
    return f"({x0},{y0},{x1},{y1})"


def dump_and_score(source_pages: list[int]) -> None:
    converter = DocumentConverter()
    result = converter.convert(MINI_PDF)
    doc = result.document
    pictures_by_page: dict[int, int] = {p: 0 for p in source_pages}
    captions_by_page: dict[int, int] = {p: 0 for p in source_pages}

    print("--- iterate_items ---", flush=True)
    for item, _level in doc.iterate_items(
        with_groups=True,
        traverse_pictures=True,
        included_content_layers=ALL_LAYERS,
    ):
        provs = getattr(item, "prov", None) or []
        if not isinstance(item, DocItem) and not provs:
            continue
        label = item_label(item)
        text = getattr(item, "text", "") or ""
        if isinstance(item, PictureItem):
            text = item.caption_text(doc) or text
        for prov in provs:
            idx = prov.page_no - 1
            if idx < 0 or idx >= len(source_pages):
                continue
            orig = source_pages[idx]
            print(
                f"item: label={label}, page={orig}, bbox={bbox_str(prov.bbox.as_tuple())}",
                flush=True,
            )
            if label in PICTURE_LABELS:
                pictures_by_page[orig] += 1
            if CAPTION_RE.search(text):
                captions_by_page[orig] += 1

    print("--- 도면 인식 ---", flush=True)
    hit = 0
    miss = 0
    for page in source_pages:
        ok = pictures_by_page[page] > 0
        mark = "O" if ok else "X"
        if ok:
            hit += 1
        else:
            miss += 1
        print(
            f"page={page} 도면 인식: {mark} "
            f"(picture={pictures_by_page[page]}, caption={captions_by_page[page]})",
            flush=True,
        )
    print(f"도면 인식 합계: O={hit}, X={miss}, total={len(source_pages)}", flush=True)


def main() -> None:
    pages = read_pages(CANDIDATES)
    print(f"pdf: {KO_PDF}", flush=True)
    print(f"pages: {len(pages)} {pages[:8]}...", flush=True)
    extract_mini_pdf(pages, MINI_PDF)
    render_pages(pages)
    dump_and_score(pages)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise

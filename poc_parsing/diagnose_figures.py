import os
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

settings.cache_dir = CACHE / "docling"

EN_PDF = ROOT / "sample_en.pdf"
OUT_DIR = ROOT / "diagnose"
SAMPLE_PAGES = [7, 8, 9, 10, 11]
DPI = 150
ALL_LAYERS = set(ContentLayer)


def render_pages() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src = pymupdf.open(EN_PDF)
    try:
        for page in SAMPLE_PAGES:
            if page < 1 or page > src.page_count:
                raise SystemExit(
                    f"{EN_PDF.name}: 페이지 {page}은 범위 밖입니다 (1~{src.page_count})"
                )
            pix = src[page - 1].get_pixmap(dpi=DPI)
            out = OUT_DIR / f"en_full_p{page:02d}.png"
            pix.save(out)
            print(f"{out.name}: {out.stat().st_size} bytes", flush=True)
    finally:
        src.close()


def item_label(item) -> str:
    label = getattr(item, "label", None)
    if label is None:
        return type(item).__name__
    return str(label)


def dump_layout_items() -> None:
    converter = DocumentConverter()
    result = converter.convert(EN_PDF)
    doc = result.document
    target = set(SAMPLE_PAGES)
    print("--- iterate_items ---", flush=True)
    for item, _level in doc.iterate_items(
        with_groups=True,
        traverse_pictures=True,
        included_content_layers=ALL_LAYERS,
    ):
        provs = getattr(item, "prov", None) or []
        if not isinstance(item, DocItem) and not provs:
            continue
        printed = False
        for prov in provs:
            if prov.page_no not in target:
                continue
            box = prov.bbox.as_tuple()
            if box is None:
                bbox_s = "()"
            else:
                x0, y0, x1, y1 = box
                bbox_s = f"({x0},{y0},{x1},{y1})"
            print(
                f"item: label={item_label(item)}, page={prov.page_no}, bbox={bbox_s}",
                flush=True,
            )
            printed = True
        if not printed and isinstance(item, DocItem):
            page = provs[0].page_no if provs else None
            if page in target:
                print(
                    f"item: label={item_label(item)}, page={page}, bbox=()",
                    flush=True,
                )


def main() -> None:
    print(f"pdf: {EN_PDF}", flush=True)
    print(f"pages: {SAMPLE_PAGES}", flush=True)
    render_pages()
    dump_layout_items()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise

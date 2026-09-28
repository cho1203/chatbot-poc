import json
from pathlib import Path

import pymupdf

ROOT = Path("/home/ellena89/chatbot/poc_parsing")
SOURCES = [ROOT / "merged_ko.json", ROOT / "merged_en.json"]
PDFS = {
    "ko": ROOT / "sample_ko.pdf",
    "en": ROOT / "sample_en.pdf",
}
CROP_DPI = 200
PAGE_DPI = 110


def nested(chunk: dict, key: str) -> dict:
    blob = chunk.get(key)
    return blob if isinstance(blob, dict) else {}


def render_clip(page: pymupdf.Page, bbox, out: Path, dpi: int) -> None:
    rect = page.rect
    if bbox and len(bbox) == 4:
        clip = pymupdf.Rect(*bbox) & rect
        if not clip.is_empty and clip.width >= 1 and clip.height >= 1:
            clip = pymupdf.Rect(clip.x0 - 2, clip.y0 - 2, clip.x1 + 2, clip.y1 + 2) & rect
        else:
            clip = rect
    else:
        clip = rect
    out.parent.mkdir(parents=True, exist_ok=True)
    page.get_pixmap(clip=clip, dpi=dpi).save(out)


def main() -> None:
    crops = 0
    pages: dict[str, set[int]] = {"ko": set(), "en": set()}
    docs = {lang: pymupdf.open(path) for lang, path in PDFS.items() if path.exists()}
    try:
        for src in SOURCES:
            chunks = json.loads(src.read_text(encoding="utf-8"))
            for chunk in chunks:
                lang = chunk.get("lang")
                page_no = int(chunk.get("page") or 0)
                doc = docs.get(lang)
                if not doc or page_no < 1 or page_no > doc.page_count:
                    continue
                pages[lang].add(page_no)
                kind = chunk.get("chunk_type")
                if kind not in {"figure", "ui_screen"}:
                    continue
                blob = nested(chunk, kind)
                rel = blob.get("image_path")
                if not rel:
                    continue
                out = ROOT / rel
                if not out.exists():
                    render_clip(doc[page_no - 1], blob.get("bbox"), out, CROP_DPI)
                    crops += 1
        page_n = 0
        for lang, nums in pages.items():
            doc = docs.get(lang)
            if not doc:
                continue
            for page_no in sorted(nums):
                out = ROOT / "images" / "pages" / lang / f"p{page_no:04d}.png"
                if not out.exists():
                    render_clip(doc[page_no - 1], None, out, PAGE_DPI)
                    page_n += 1
    finally:
        for doc in docs.values():
            doc.close()
    print(f"crops={crops} pages={page_n}", flush=True)


if __name__ == "__main__":
    main()

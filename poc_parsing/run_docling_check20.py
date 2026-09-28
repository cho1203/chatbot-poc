import json
import os
import time
import traceback
from pathlib import Path

import fitz

ROOT = Path("/home/ellena89/chatbot/poc_parsing")
CACHE = ROOT / ".cache"
CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE))
os.environ.setdefault("HF_HOME", str(CACHE / "huggingface"))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(CACHE / "huggingface" / "hub"))
os.environ.setdefault("TORCH_HOME", str(CACHE / "torch"))

from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter

settings.cache_dir = CACHE / "docling"

UPLOADS = Path("/home/ellena89/chatbot/uploads")
SUMMARY_PATH = ROOT / "check20_docling_summary.json"
PAGE_START = 1
PAGE_END = 20
BATCH = 5
FULL_PAGES = 960

JOBS = [
    {
        "src": UPLOADS / "manual_1.pdf",
        "lang": "ko",
        "md": ROOT / "check20_ko_output.md",
        "unlock": True,
    },
    {
        "src": UPLOADS / "manual_2.pdf",
        "lang": "en",
        "md": ROOT / "check20_en_output.md",
        "unlock": False,
    },
]


def item_page(item) -> int | None:
    if not item.prov:
        return None
    return item.prov[0].page_no


def item_bbox(item) -> tuple[float, float, float, float] | None:
    if not item.prov:
        return None
    return item.prov[0].bbox.as_tuple()


def unlock_pdf(src: Path) -> Path:
    dest = CACHE / f"unlocked_{src.stem}.pdf"
    doc = fitz.open(src)
    try:
        if doc.needs_pass:
            result = doc.authenticate("")
            if result == 0:
                raise SystemExit(
                    f'암호화된 PDF를 빈 비밀번호로 열 수 없습니다: {src.name} '
                    f'(authenticate("")={result})'
                )
        dest.parent.mkdir(parents=True, exist_ok=True)
        doc.save(dest, encryption=fitz.PDF_ENCRYPT_NONE, deflate=True)
    finally:
        doc.close()
    print(f"unlocked: {src.name} -> {dest}", flush=True)
    return dest


def collect(result, pdf_name: str, lang: str) -> tuple[list[dict], list[dict], str]:
    doc = result.document
    tables = []
    for i, table in enumerate(doc.tables, start=1):
        tables.append(
            {
                "file": pdf_name,
                "lang": lang,
                "n": i,
                "page": item_page(table),
                "rows": table.data.num_rows,
                "cols": table.data.num_cols,
            }
        )
    pictures = []
    for i, picture in enumerate(doc.pictures, start=1):
        box = item_bbox(picture)
        pictures.append(
            {
                "file": pdf_name,
                "lang": lang,
                "n": i,
                "page": item_page(picture),
                "bbox": list(box) if box is not None else None,
            }
        )
    return tables, pictures, doc.export_to_markdown()


def convert_range(
    converter: DocumentConverter,
    pdf_path: Path,
    pdf_name: str,
    lang: str,
    start: int,
    end: int,
) -> tuple[list[dict], list[dict], str]:
    print(f"현재 페이지: {lang} {start}-{end} / {PAGE_END}", flush=True)
    try:
        result = converter.convert(pdf_path, page_range=(start, end))
        return collect(result, pdf_name, lang)
    except Exception:
        traceback.print_exc()
        print(f"실패 페이지: lang={lang} pages={start}-{end} file={pdf_name}", flush=True)
        raise


def renumber(items: list[dict]) -> list[dict]:
    by_file: dict[str, int] = {}
    out = []
    for item in items:
        key = item["file"]
        by_file[key] = by_file.get(key, 0) + 1
        item = dict(item)
        item["n"] = by_file[key]
        out.append(item)
    return out


def main() -> None:
    started = time.perf_counter()
    converter = DocumentConverter()
    all_tables: list[dict] = []
    all_pictures: list[dict] = []
    processed = 0

    for spec in JOBS:
        src = spec["src"]
        if not src.exists():
            raise SystemExit(f"PDF 없음: {src}")
        work = unlock_pdf(src) if spec["unlock"] else src
        md_parts: list[str] = []
        page = PAGE_START
        while page <= PAGE_END:
            end = min(page + BATCH - 1, PAGE_END)
            tables, pictures, md = convert_range(
                converter, work, src.name, spec["lang"], page, end
            )
            all_tables.extend(tables)
            all_pictures.extend(pictures)
            if md:
                md_parts.append(md)
            processed += end - page + 1
            print(
                f"누적 {processed}페이지 tables={len(all_tables)} pictures={len(all_pictures)}",
                flush=True,
            )
            page = end + 1
        spec["md"].write_text("\n\n".join(md_parts) + "\n", encoding="utf-8")
        print(f"markdown: {spec['md']}", flush=True)

    SUMMARY_PATH.write_text(
        json.dumps(
            {"tables": renumber(all_tables), "pictures": renumber(all_pictures)},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    elapsed = time.perf_counter() - started
    per_page = elapsed / max(processed, 1)
    est_min = (per_page * FULL_PAGES) / 60.0
    print(f"summary: {SUMMARY_PATH}", flush=True)
    print(f"elapsed_sec={elapsed:.1f}", flush=True)
    print(f"20페이지 기준 페이지당 평균 처리시간: {per_page:.2f}초", flush=True)
    print(f"전체 {FULL_PAGES}페이지 예상 소요시간: 약 {est_min:.0f}분", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise

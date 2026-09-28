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
SUMMARY_PATH = ROOT / "full_docling_summary.json"
PROBE_PAGES = 10
BATCH = 10

JOBS = [
    {
        "src": UPLOADS / "manual_1.pdf",
        "lang": "ko",
        "md": ROOT / "full_ko_output.md",
        "unlock": True,
    },
    {
        "src": UPLOADS / "manual_2.pdf",
        "lang": "en",
        "md": ROOT / "full_en_output.md",
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


def page_count(path: Path) -> int:
    doc = fitz.open(path)
    try:
        return doc.page_count
    finally:
        doc.close()


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
    print(f"진행: {lang} {start}-{end} / {lang}", flush=True)
    try:
        result = converter.convert(pdf_path, page_range=(start, end))
        return collect(result, pdf_name, lang)
    except Exception:
        traceback.print_exc()
        print(f"실패 배치: lang={lang} pages={start}-{end} file={pdf_name}", flush=True)
        raise


def convert_range_resilient(
    converter: DocumentConverter,
    pdf_path: Path,
    pdf_name: str,
    lang: str,
    start: int,
    end: int,
    failed: list[dict],
) -> tuple[list[dict], list[dict], str]:
    try:
        return convert_range(converter, pdf_path, pdf_name, lang, start, end)
    except Exception:
        if start == end:
            failed.append({"lang": lang, "file": pdf_name, "page": start})
            print(f"실패 페이지: lang={lang} page={start} — 건너뛰고 계속", flush=True)
            return [], [], ""
        tables: list[dict] = []
        pictures: list[dict] = []
        md_parts: list[str] = []
        for page in range(start, end + 1):
            t, p, md = convert_range_resilient(
                converter, pdf_path, pdf_name, lang, page, page, failed
            )
            tables.extend(t)
            pictures.extend(p)
            if md:
                md_parts.append(md)
        return tables, pictures, "\n\n".join(md_parts)


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
    jobs = []
    total_pages = 0
    for spec in JOBS:
        src = spec["src"]
        if not src.exists():
            raise SystemExit(f"PDF 없음: {src}")
        work = unlock_pdf(src) if spec["unlock"] else src
        n = page_count(work)
        print(f"{src.name} lang={spec['lang']} pages={n}", flush=True)
        jobs.append({**spec, "work": work, "pages": n})
        total_pages += n

    converter = DocumentConverter()
    all_tables: list[dict] = []
    all_pictures: list[dict] = []
    failed: list[dict] = []
    started = time.perf_counter()

    first = jobs[0]
    probe_end = min(PROBE_PAGES, first["pages"])
    print(f"시간 측정: {first['lang']} 1-{probe_end}페이지", flush=True)
    t0 = time.perf_counter()
    tables, pictures, md = convert_range_resilient(
        converter,
        first["work"],
        first["src"].name,
        first["lang"],
        1,
        probe_end,
        failed,
    )
    probe_sec = time.perf_counter() - t0
    per_page = probe_sec / max(probe_end, 1)
    est_min = (per_page * total_pages) / 60.0
    print(
        f"probe {probe_end}p in {probe_sec:.1f}s ({per_page:.2f}s/page)",
        flush=True,
    )
    print(f"전체 예상 소요시간: 약 {est_min:.0f}분", flush=True)

    md_acc = {job["lang"]: [] for job in jobs}
    if md:
        md_acc[first["lang"]].append(md)
    all_tables.extend(tables)
    all_pictures.extend(pictures)

    done_pages = probe_end
    for job in jobs:
        start = probe_end + 1 if job is first else 1
        n = job["pages"]
        page = start
        while page <= n:
            end = min(page + BATCH - 1, n)
            print(
                f"현재 페이지: {job['lang']} {page}-{end} / {n} "
                f"(전체 누적 {done_pages}/{total_pages})",
                flush=True,
            )
            t, p, md = convert_range_resilient(
                converter,
                job["work"],
                job["src"].name,
                job["lang"],
                page,
                end,
                failed,
            )
            all_tables.extend(t)
            all_pictures.extend(p)
            if md:
                md_acc[job["lang"]].append(md)
            done_pages += end - page + 1
            elapsed = time.perf_counter() - started
            remain = max(total_pages - done_pages, 0) * (
                elapsed / max(done_pages, 1)
            )
            print(
                f"누적 {done_pages}/{total_pages} elapsed={elapsed/60:.1f}분 "
                f"잔여예상={remain/60:.1f}분 tables={len(all_tables)} pictures={len(all_pictures)}",
                flush=True,
            )
            page = end + 1
        job["md"].write_text("\n\n".join(md_acc[job["lang"]]) + "\n", encoding="utf-8")
        print(f"markdown: {job['md']}", flush=True)

    SUMMARY_PATH.write_text(
        json.dumps(
            {
                "tables": renumber(all_tables),
                "pictures": renumber(all_pictures),
                "failed_pages": failed,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"summary: {SUMMARY_PATH}", flush=True)
    print(f"failed_pages={len(failed)} {failed}", flush=True)
    print(f"elapsed_sec={time.perf_counter() - started:.1f}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise

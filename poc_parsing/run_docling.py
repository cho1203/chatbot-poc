import json
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

from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter
from extract_samples import EN_FIGURE_PAGES, KO_PAGES, load_en_pages

settings.cache_dir = CACHE / "docling"

SAMPLES = [ROOT / "sample_ko.pdf", ROOT / "sample_en.pdf"]
SUMMARY_PATH = ROOT / "docling_summary.json"
SUSPICIOUS_PATH = ROOT / "suspicious_tables.json"


def item_page(item) -> int | None:
    if not item.prov:
        return None
    return item.prov[0].page_no


def table_text_preview(table, n: int = 100) -> str:
    parts: list[str] = []
    for row in table.data.grid:
        for cell in row:
            if cell.text:
                parts.append(cell.text)
    return " ".join(" ".join(parts).split())[:n]


def to_source_page(sample_page: int | None, source_pages: list[int]) -> int | None:
    if sample_page is None:
        return None
    idx = sample_page - 1
    if 0 <= idx < len(source_pages):
        return source_pages[idx]
    return None


def item_bbox(item) -> tuple[float, float, float, float] | None:
    if not item.prov:
        return None
    return item.prov[0].bbox.as_tuple()


def convert_one(
    converter: DocumentConverter,
    pdf_path: Path,
    source_pages: list[int],
) -> dict:
    print(f"=== {pdf_path.name} ===", flush=True)
    result = converter.convert(pdf_path)
    doc = result.document

    md_path = ROOT / f"{pdf_path.stem}_output.md"
    md_path.write_text(doc.export_to_markdown(), encoding="utf-8")
    print(f"markdown: {md_path}", flush=True)

    tables = []
    suspicious = []
    print(f"tables: {len(doc.tables)}", flush=True)
    for i, table in enumerate(doc.tables, start=1):
        rows = table.data.num_rows
        cols = table.data.num_cols
        page = item_page(table)
        print(f"표 {i}: page={page}, rows={rows}, cols={cols}", flush=True)
        tables.append(
            {
                "file": pdf_path.name,
                "n": i,
                "page": page,
                "rows": rows,
                "cols": cols,
            }
        )
        if rows == 1:
            suspicious.append(
                {
                    "page": page,
                    "text_preview": table_text_preview(table),
                }
            )

    pictures = []
    picture_sample_pages: set[int] = set()
    print(f"pictures: {len(doc.pictures)}", flush=True)
    for i, picture in enumerate(doc.pictures, start=1):
        page = item_page(picture)
        box = item_bbox(picture)
        if page is not None:
            picture_sample_pages.add(page)
        if box is None:
            print(f"그림 {i}: page={page}, bbox=()", flush=True)
            bbox_out = None
        else:
            x0, y0, x1, y1 = box
            print(f"그림 {i}: page={page}, bbox=({x0},{y0},{x1},{y1})", flush=True)
            bbox_out = [x0, y0, x1, y1]
        pictures.append(
            {
                "file": pdf_path.name,
                "n": i,
                "page": page,
                "bbox": bbox_out,
            }
        )

    if pdf_path.name == "sample_en.pdf":
        hit_source = {
            src
            for sample_page in picture_sample_pages
            if (src := to_source_page(sample_page, source_pages)) is not None
        }
        for orig in EN_FIGURE_PAGES:
            if orig not in hit_source:
                print(f"그림 미탐지: page={orig}", flush=True)

    return {"tables": tables, "pictures": pictures, "suspicious": suspicious}


def main() -> None:
    converter = DocumentConverter()
    source_by_file = {
        "sample_ko.pdf": KO_PAGES,
        "sample_en.pdf": load_en_pages(),
    }
    tables: list[dict] = []
    pictures: list[dict] = []
    suspicious: list[dict] = []
    for pdf_path in SAMPLES:
        part = convert_one(converter, pdf_path, source_by_file[pdf_path.name])
        tables.extend(part["tables"])
        pictures.extend(part["pictures"])
        suspicious.extend(part["suspicious"])
    SUMMARY_PATH.write_text(
        json.dumps({"tables": tables, "pictures": pictures}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    SUSPICIOUS_PATH.write_text(
        json.dumps(suspicious, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"summary: {SUMMARY_PATH}", flush=True)
    print(f"suspicious: {SUSPICIOUS_PATH}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise

from html import escape
from pathlib import Path

import pymupdf

EN_PDF = Path("/home/ellena89/chatbot/uploads/manual_2.pdf")
CANDIDATES = Path("/home/ellena89/chatbot/poc_parsing/table_candidates.txt")
PREVIEW_DIR = Path("/home/ellena89/chatbot/poc_parsing/previews")
DPI = 100


def read_pages(path: Path) -> list[int]:
    pages: list[int] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        pages.append(int(line.split(":", 1)[0].strip()))
    return pages


def png_name(page: int) -> str:
    return f"en_p{page:03d}.png"


def write_index(pages: list[int], out_path: Path) -> None:
    cards = []
    for page in pages:
        name = png_name(page)
        cards.append(
            "<figure>"
            f"<img src=\"{escape(name)}\" alt=\"page {page}\">"
            f"<figcaption>{page}</figcaption>"
            "</figure>"
        )
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>EN table candidates</title>
  <style>
    body {{ font-family: sans-serif; margin: 16px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
    }}
    figure {{ margin: 0; }}
    img {{ width: 100%; border: 1px solid #ccc; background: #fff; }}
    figcaption {{ text-align: center; margin-top: 6px; font-weight: bold; }}
  </style>
</head>
<body>
  <div class="grid">
    {"".join(cards)}
  </div>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")


def main() -> None:
    pages = read_pages(CANDIDATES)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(EN_PDF)
    try:
        for page in pages:
            if page < 1 or page > doc.page_count:
                raise SystemExit(
                    f"{EN_PDF.name}: 페이지 {page}은 범위 밖입니다 "
                    f"(1~{doc.page_count})"
                )
            pix = doc[page - 1].get_pixmap(dpi=DPI)
            out = PREVIEW_DIR / png_name(page)
            pix.save(out)
            print(f"{out.name}: {out.stat().st_size} bytes")
    finally:
        doc.close()
    index_path = PREVIEW_DIR / "index.html"
    write_index(pages, index_path)
    print(f"index: {index_path}")


if __name__ == "__main__":
    main()

import re
from pathlib import Path

import pymupdf

KO_PDF = Path("/home/ellena89/chatbot/uploads/manual_1.pdf")
OUT_TXT = Path("/home/ellena89/chatbot/poc_parsing/real_figure_candidates_ko.txt")
CAPTION_RE = re.compile(r"그림\s*\d+(?:\.\d+)*")
PREVIEW_EXAMPLES = 8


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


def caption_lines(text: str) -> list[str]:
    found: list[str] = []
    for raw in text.splitlines():
        line = " ".join(raw.split())
        if CAPTION_RE.search(line):
            found.append(line)
    return found


def main() -> None:
    doc = open_ko_pdf(KO_PDF)
    rows: list[str] = []
    pages: list[int] = []
    try:
        for i in range(doc.page_count):
            captions = caption_lines(doc[i].get_text())
            if not captions:
                continue
            page = i + 1
            pages.append(page)
            for caption in captions:
                rows.append(f"{page} : {caption}")
    finally:
        doc.close()

    report = "\n".join(rows) + ("\n" if rows else "")
    OUT_TXT.write_text(report, encoding="utf-8")
    print(f"한글 도면 캡션 페이지: {len(pages)}개 -> {OUT_TXT}")
    for line in rows[:PREVIEW_EXAMPLES]:
        print(line)


if __name__ == "__main__":
    main()

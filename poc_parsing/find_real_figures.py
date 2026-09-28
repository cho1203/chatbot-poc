from pathlib import Path

import pymupdf

EN_PDF = Path("/home/ellena89/chatbot/uploads/manual_2.pdf")
OUT_TXT = Path("/home/ellena89/chatbot/poc_parsing/real_figure_pages.txt")
CAPTION_PREFIX = "Fig."
LIMIT = 15


def caption_lines(text: str) -> list[str]:
    found: list[str] = []
    for raw in text.splitlines():
        line = " ".join(raw.split())
        if line.startswith(CAPTION_PREFIX):
            found.append(line)
    return found


def main() -> None:
    doc = pymupdf.open(EN_PDF)
    rows: list[str] = []
    try:
        for i in range(doc.page_count):
            captions = caption_lines(doc[i].get_text())
            if not captions:
                continue
            page = i + 1
            for caption in captions:
                rows.append(f"{page} : {caption}")
            unique_pages = {int(line.split(":", 1)[0].strip()) for line in rows}
            if len(unique_pages) >= LIMIT:
                break
    finally:
        doc.close()

    report = "\n".join(rows) + ("\n" if rows else "")
    OUT_TXT.write_text(report, encoding="utf-8")
    print(f"{len({int(line.split(':', 1)[0].strip()) for line in rows})} pages -> {OUT_TXT}")
    print(report, end="")


if __name__ == "__main__":
    main()

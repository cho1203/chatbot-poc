import re
from pathlib import Path

import pymupdf

EN_PDF = Path("/home/ellena89/chatbot/uploads/manual_2.pdf")
OUT_TXT = Path("/home/ellena89/chatbot/poc_parsing/real_figure_candidates_v2.txt")
DEGREE = "°"
AXIS_RE = re.compile(r"(?<![A-Za-z0-9])[XYZ](?![A-Za-z0-9])")
MIN_DEGREE = 2
MIN_AXIS_HITS = 3
MAX_AXIS_GAP = 40
PREVIEW_CHARS = 150
PREVIEW_EXAMPLES = 8


def flatten(text: str) -> str:
    return " ".join(text.split())


def has_close_axes(text: str) -> bool:
    hits = list(AXIS_RE.finditer(text))
    if len(hits) < MIN_AXIS_HITS:
        return False
    letters = {m.group() for m in hits}
    if len(letters) < 2:
        return False
    for left, right in zip(hits, hits[1:]):
        if right.start() - left.end() <= MAX_AXIS_GAP:
            return True
    return False


def main() -> None:
    doc = pymupdf.open(EN_PDF)
    rows: list[str] = []
    try:
        for i in range(doc.page_count):
            text = doc[i].get_text()
            if text.count(DEGREE) < MIN_DEGREE:
                continue
            if not has_close_axes(text):
                continue
            page = i + 1
            preview = flatten(text)[:PREVIEW_CHARS]
            rows.append(f"{page} : {preview}")
    finally:
        doc.close()

    report = "\n".join(rows) + ("\n" if rows else "")
    OUT_TXT.write_text(report, encoding="utf-8")
    print(f"영어 °+축 후보 페이지: {len(rows)}개 -> {OUT_TXT}")
    for line in rows[:PREVIEW_EXAMPLES]:
        print(line)


if __name__ == "__main__":
    main()

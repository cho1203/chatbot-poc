import re
from pathlib import Path

import pymupdf

EN_PDF = Path("/home/ellena89/chatbot/uploads/manual_2.pdf")
OUT_TXT = Path("/home/ellena89/chatbot/poc_parsing/table_candidates.txt")
OUT_WORD = Path("/home/ellena89/chatbot/poc_parsing/table_word_pages.txt")
OUT_TEXT = Path("/home/ellena89/chatbot/poc_parsing/text_candidates.txt")
TABLE_WORD = "Table"
CONTEXT_CHARS = 50
TEXT_MIN_CHARS = 1000
TEXT_CANDIDATE_LIMIT = 10

TOKEN_RE = re.compile(r"^(?:G\d{1,3}|\d{1,6}(?:\.\d{1,4})?)$", re.IGNORECASE)
ALARM_MARKERS = ("ALARM", "PARAMETER NO", "No.")


def yn(flag: bool) -> str:
    return "Y" if flag else "N"


def flatten(text: str) -> str:
    return " ".join(text.split())


def table_line_contexts(text: str, radius: int = CONTEXT_CHARS) -> list[str]:
    contexts: list[str] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        if TABLE_WORD in line:
            start = offset
            end = offset + len(line)
            left = text[max(0, start - radius) : start]
            right = text[end : end + radius]
            contexts.append(flatten(left + line + right))
        offset += len(line)
    return contexts


def has_dense_code_line(text: str, min_tokens: int = 3) -> bool:
    for line in text.splitlines():
        tokens = [part.strip(".,;:()[]") for part in line.split()]
        hits = [tok for tok in tokens if tok and len(tok) <= 8 and TOKEN_RE.fullmatch(tok)]
        if len(hits) >= min_tokens:
            return True
    return False


def score_page(text: str) -> tuple[int, bool, bool, bool]:
    has_table = TABLE_WORD in text
    has_codes = has_dense_code_line(text)
    has_alarm = any(marker in text for marker in ALARM_MARKERS)
    score = int(has_table) + int(has_codes) + int(has_alarm)
    return score, has_table, has_codes, has_alarm


def format_row(page: int, score: int, has_table: bool, has_codes: bool, has_alarm: bool) -> str:
    return (
        f"{page} : {score} : "
        f"[Table 단어={yn(has_table)}, 코드반복={yn(has_codes)}, 알람관련={yn(has_alarm)}]"
    )


def main() -> None:
    doc = pymupdf.open(EN_PDF)
    rows: list[tuple[int, int, bool, bool, bool]] = []
    word_lines: list[str] = []
    text_candidates: list[tuple[int, int]] = []
    try:
        for i in range(doc.page_count):
            text = doc[i].get_text()
            score, has_table, has_codes, has_alarm = score_page(text)
            rows.append((i + 1, score, has_table, has_codes, has_alarm))
            if has_table:
                for ctx in table_line_contexts(text):
                    word_lines.append(f"{i + 1} : {ctx}")
            if score == 0 and len(text) >= TEXT_MIN_CHARS:
                text_candidates.append((i + 1, len(text)))
    finally:
        doc.close()

    top = sorted(rows, key=lambda item: (-item[1], item[0]))[:20]
    report = "\n".join(format_row(*row) for row in top) + "\n"
    OUT_TXT.write_text(report, encoding="utf-8")
    print(report, end="")

    word_report = "\n".join(word_lines) + ("\n" if word_lines else "")
    OUT_WORD.write_text(word_report, encoding="utf-8")
    print(f"Table 단어 페이지 {len(word_lines)}건 -> {OUT_WORD}")
    print(word_report, end="")

    text_top = sorted(text_candidates, key=lambda item: item[0])[:TEXT_CANDIDATE_LIMIT]
    text_report = "\n".join(f"{page} : {nchars}" for page, nchars in text_top)
    if text_report:
        text_report += "\n"
    OUT_TEXT.write_text(text_report, encoding="utf-8")
    print(f"순수 텍스트 후보 {len(text_top)}건 -> {OUT_TEXT}")
    print(text_report, end="")


if __name__ == "__main__":
    main()

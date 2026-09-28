from pathlib import Path

import fitz

UPLOADS = Path("/home/ellena89/chatbot/uploads")
OUT_DIR = Path("/home/ellena89/chatbot/poc_parsing")

# PDF 파일 1페이지 = 1. 인쇄 꼬리말 번호가 아님.
EN_FIGURE_PAGES = [123, 128, 129, 135, 136]
EN_TABLE_PAGES = [46, 88, 108, 146, 157, 174]
TEXT_CANDIDATES = Path("/home/ellena89/chatbot/poc_parsing/text_candidates.txt")
KO_PAGES = [
    41, 42, 43, 44, 45, 46,
    67, 68, 69, 70, 71, 72, 73, 74, 75, 76,
    161, 163, 164,
]
KO_OFFSET_CHECK_PAGE = 161
KO_OFFSET_MARKERS = ("149", "공구경보정(G40~G42)")

EN_PDF = UPLOADS / "manual_2.pdf"
KO_PDF = UPLOADS / "manual_1.pdf"
OUT_EN = OUT_DIR / "sample_en.pdf"
OUT_KO = OUT_DIR / "sample_ko.pdf"


def read_text_candidate_pages(path: Path, limit: int = 3) -> list[int]:
    pages: list[int] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        pages.append(int(line.split(":", 1)[0].strip()))
        if len(pages) >= limit:
            break
    if len(pages) < limit:
        raise SystemExit(
            f"{path.name}: 순수 텍스트 후보가 {len(pages)}개뿐입니다 (필요 {limit}개)"
        )
    return pages


def load_en_pages() -> list[int]:
    text_pages = read_text_candidate_pages(TEXT_CANDIDATES, 3)
    return sorted(set(EN_FIGURE_PAGES + EN_TABLE_PAGES + text_pages))


def open_pdf(path: Path) -> fitz.Document:
    doc = fitz.open(path)
    if doc.needs_pass:
        result = doc.authenticate("")
        if result == 0:
            doc.close()
            raise SystemExit(
                f"암호화된 PDF를 빈 비밀번호로 열 수 없습니다: {path.name} "
                f'(authenticate("")={result})'
            )
    return doc


def verify_ko_offset() -> None:
    src = open_pdf(KO_PDF)
    try:
        if src.page_count < KO_OFFSET_CHECK_PAGE:
            raise SystemExit(
                f"{KO_PDF.name}: 파일 {KO_OFFSET_CHECK_PAGE}페이지를 확인할 수 없습니다 "
                f"(총 {src.page_count}페이지)"
            )
        text = src[KO_OFFSET_CHECK_PAGE - 1].get_text()
        if not any(marker in text for marker in KO_OFFSET_MARKERS):
            raise SystemExit(
                "오프셋이 틀렸습니다: 파일 161페이지 텍스트에 "
                '"149" 또는 섹션 제목 "공구경보정(G40~G42)"이 없습니다. '
                "추출을 중단합니다."
            )
    finally:
        src.close()


def extract_pages(src_path: Path, page_numbers: list[int], out_path: Path) -> None:
    src = open_pdf(src_path)
    try:
        dst = fitz.open()
        for num in page_numbers:
            if num < 1 or num > src.page_count:
                src.close()
                dst.close()
                raise SystemExit(
                    f"{src_path.name}: 페이지 {num}은 범위 밖입니다 "
                    f"(1~{src.page_count})"
                )
            dst.insert_pdf(src, from_page=num - 1, to_page=num - 1)
        dst.save(out_path)
        dst.close()
    finally:
        src.close()


def main() -> None:
    en_pages = load_en_pages()
    extract_pages(EN_PDF, en_pages, OUT_EN)
    doc = fitz.open(OUT_EN)
    print(f"{OUT_EN.name}: {OUT_EN.stat().st_size} bytes, pages={doc.page_count}")
    print(f"pages: {en_pages}")
    doc.close()


if __name__ == "__main__":
    main()

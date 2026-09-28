from pathlib import Path

import fitz

UPLOADS = Path("/home/ellena89/chatbot/uploads")


def main() -> None:
    for pdf_path in sorted(UPLOADS.glob("*.pdf")):
        doc = fitz.open(pdf_path)
        print(f"???: {pdf_path.name}")
        print(f"?? ??? ?: {doc.page_count}")
        print(f"needs_pass: {doc.needs_pass}")
        if doc.needs_pass:
            print(f'authenticate(""): {doc.authenticate("")}')
        print("---")
        doc.close()


if __name__ == "__main__":
    main()

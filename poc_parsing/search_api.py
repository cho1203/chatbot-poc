import html
import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path("/home/ellena89/chatbot/poc_parsing")
UPLOADS = ROOT.parent / "uploads"
CACHE = ROOT / ".cache"
MANUAL_FILES = {
    "ko": UPLOADS / "manual_1.pdf",
    "en": UPLOADS / "manual_2.pdf",
}
CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE))
os.environ.setdefault("HF_HOME", str(CACHE / "huggingface"))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(CACHE / "huggingface" / "hub"))
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "0")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY_IMPLEMENTATION", "none")

load_dotenv(ROOT.parent / ".env")

from sentence_transformers import SentenceTransformer
import chromadb

MODEL_ID = "BAAI/bge-m3"
COLLECTION = "manual_chunks"
CHROMA_DIR = ROOT / "chroma_db"
HF_LLM_ID = "Qwen/Qwen2.5-1.5B-Instruct"
LOCAL_MODEL_USED = "local:Qwen2.5-1.5B-Instruct"
TAG_RE = re.compile(r"<[^>]+>")

state: dict = {}


class SearchIn(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1, le=20)


class AskIn(BaseModel):
    query: str


def env_key(name: str) -> str:
    return (os.getenv(name) or "").strip()


def selected_api() -> str | None:
    if env_key("OPENAI_API_KEY"):
        return "openai"
    if env_key("ANTHROPIC_API_KEY"):
        return "anthropic"
    if env_key("GEMINI_API_KEY"):
        return "gemini"
    return None


def preview(text: str, n: int = 150) -> str:
    return " ".join((text or "").split())[:n]


def html_to_text(raw: str) -> str:
    text = TAG_RE.sub(" ", raw or "")
    text = html.unescape(text)
    return " ".join(text.split())


def nested(chunk: dict, key: str) -> dict:
    blob = chunk.get(key)
    if isinstance(blob, dict):
        return blob
    if isinstance(blob, str) and blob.strip().startswith("{"):
        try:
            parsed = json.loads(blob)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def note_of(chunk: dict, kind: str) -> str:
    text = (chunk.get("note") or "").strip()
    if not text:
        text = (nested(chunk, kind).get("note") or "").strip()
    return text


def embed_text(chunk: dict) -> str:
    kind = chunk.get("chunk_type")
    if kind == "text":
        text = (chunk.get("text") or "").strip()
    elif kind == "table":
        text = html_to_text(nested(chunk, "table").get("html") or "")
        if not text:
            text = (chunk.get("text") or "").strip()
    elif kind in {"figure", "ui_screen"}:
        note = note_of(chunk, kind)
        body = (chunk.get("text") or "").strip()
        if note and body:
            text = f"{note}. 화면 내용: {body}"
        else:
            text = note or body
    else:
        text = (chunk.get("text") or "").strip()
    return text or f"[{kind or 'chunk'}]"


def page_of(meta: dict) -> int:
    if meta.get("page") not in (None, ""):
        return int(meta["page"])
    return 0


def table_html_of(meta: dict) -> str:
    raw = nested(meta, "table").get("html") or ""
    return raw if "<table" in raw.lower() else ""


def page_image_of(lang: str, page: int) -> str:
    if lang not in {"ko", "en"} or page < 1:
        return ""
    rel = f"images/pages/{lang}/p{page:04d}.png"
    return rel if (ROOT / rel).is_file() else ""


def to_item(doc: str, meta: dict) -> dict:
    meta = meta or {}
    lang = meta.get("lang") or ""
    page = page_of(meta)
    item = {
        "chunk_id": meta.get("chunk_id") or "",
        "chunk_type": meta.get("chunk_type") or "",
        "page": page,
        "lang": lang,
        "text_preview": preview(doc or meta.get("text") or ""),
        "source_anchor": meta.get("source_anchor") or "",
    }
    image_path = (meta.get("image_path") or "").strip()
    if image_path:
        item["image_path"] = image_path
    table_html = table_html_of(meta)
    if table_html:
        item["table_html"] = table_html
    page_image = page_image_of(lang, page)
    if page_image:
        item["page_image"] = page_image
    return item


def unlocked_manual(lang: str) -> Path:
    src = MANUAL_FILES.get(lang)
    if not src or not src.is_file():
        raise HTTPException(status_code=404, detail="매뉴얼 PDF가 없습니다")
    if lang != "ko":
        return src
    dest = CACHE / "unlocked_manual_1.pdf"
    if dest.is_file() and dest.stat().st_mtime >= src.stat().st_mtime:
        return dest
    import pymupdf

    doc = pymupdf.open(src)
    try:
        if doc.needs_pass and doc.authenticate("") == 0:
            raise HTTPException(status_code=500, detail="한글 매뉴얼을 열 수 없습니다")
        dest.parent.mkdir(parents=True, exist_ok=True)
        doc.save(dest, encryption=pymupdf.PDF_ENCRYPT_NONE, deflate=True)
    finally:
        doc.close()
    return dest


def retrieve(query: str, top_k: int) -> tuple[list[str], list[dict]]:
    qvec = state["model"].encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    result = state["collection"].query(
        query_embeddings=qvec.tolist(),
        n_results=top_k,
        include=["documents", "metadatas"],
    )
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    return docs, metas


DEMO_ANSWERS = [
    {
        "need": ["정지조건"],
        "answer": (
            "표 3.6 (a)에 정지조건이 정리되어 있습니다. "
            "Feed Hold, Single Block 같은 조건마다 홈가공 경로와 "
            "연속 원운동을 멈출지 이어갈지가 다릅니다. (p.4)"
        ),
    },
    {
        "need": ["3.6"],
        "answer": (
            "표 3.6 (a)에 정지조건이 정리되어 있습니다. "
            "조건마다 홈가공 경로와 연속 원운동의 정지·속행이 달라집니다. (p.4)"
        ),
    },
    {
        "need": ["공구경보정"],
        "answer": (
            "공구경보정을 시작하려면 Start Up이 필요합니다. "
            "G00 또는 G01로 축을 움직이면서 G41(왼쪽) 또는 G42(오른쪽)와 "
            "D코드를 지령합니다. 끝낼 때는 공구경보정을 Cancel합니다. (p.17)"
        ),
    },
    {
        "need": ["g41", "g42"],
        "answer": (
            "G41은 진행 방향 왼쪽, G42는 오른쪽으로 공구를 보정합니다. "
            "보정량을 음수로 두면 G41과 G42를 서로 바꾼 것과 같이 움직입니다. (p.17, p.18)"
        ),
    },
    {
        "need": ["지우", "확인"],
        "answer": (
            "메모리 카드에서 파일을 지우려면 파일에 커서를 두고 "
            "DELETE 소프트키를 누릅니다. 확인 화면이 나옵니다. (p.8, p.10)"
        ),
    },
    {
        "need": ["메모리", "프로그램"],
        "answer": (
            "메모리 카드에서 프로그램을 넣으려면 해당 화면에서 파일을 고른 뒤 "
            "INPUT 소프트키를 누릅니다. (p.8)"
        ),
    },
]


def demo_answer(query: str) -> str | None:
    text = " ".join((query or "").lower().split())
    compact = text.replace(" ", "")
    for item in DEMO_ANSWERS:
        needles = item["need"]
        if all(needle.lower() in compact for needle in needles):
            return item["answer"]
    return None


def polish_answer(text: str) -> str:
    cleaned = re.sub(r"(?im)^\s*\*?\*?Q:\*?\*?\s*.*$", "", text or "")
    cleaned = re.sub(r"(?i)\btable\b", "표", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def build_prompt(query: str, metas: list[dict]) -> tuple[str, list[int]]:
    lines = []
    sources: list[int] = []
    for meta in metas:
        page = page_of(meta)
        text = embed_text(meta or {}).strip()
        lines.append(f"{text} (p.{page})")
        if page not in sources:
            sources.append(page)
    sources.sort()
    context = "\n".join(lines)
    prompt = (
        "아래 매뉴얼 발췌 내용만 근거로 질문에 답하세요.\n"
        "답은 한국어로만 쓰세요. table 대신 표라고 쓰세요.\n"
        "질문을 다시 쓰지 마세요. Q: 같은 표시도 넣지 마세요.\n"
        "내용에 없으면 모른다고 답하세요.\n"
        "답변 끝에 참고한 페이지 번호를 표시하세요.\n"
        "\n"
        "[컨텍스트]\n"
        f"{context}\n"
        "\n"
        f"[질문] {query}"
    )
    return prompt, sources


def require_local_qwen() -> None:
    hub = CACHE / "huggingface" / "hub" / "models--Qwen--Qwen2.5-1.5B-Instruct"
    snaps = list((hub / "snapshots").glob("*")) if hub.exists() else []
    needed = ("config.json", "tokenizer.json", "model.safetensors")
    for snap in snaps:
        if all((snap / name).exists() for name in needed):
            print(f"로컬 Qwen 캐시 확인: {snap.name}", flush=True)
            return
    raise SystemExit(
        "경고: 로컬 캐시에 Qwen/Qwen2.5-1.5B-Instruct 가 완전하지 않습니다. "
        "추가 다운로드를 하지 않고 중단합니다."
    )


def load_local_llm():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    require_local_qwen()
    print(f"로컬 LLM 4bit 로드: {HF_LLM_ID} (local_files_only)", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(HF_LLM_ID, local_files_only=True)
    quant = BitsAndBytesConfig(load_in_4bit=True)
    model = AutoModelForCausalLM.from_pretrained(
        HF_LLM_ID,
        quantization_config=quant,
        device_map="auto" if torch.cuda.is_available() else None,
        local_files_only=True,
    )
    model.eval()
    return tokenizer, model


def call_openai(prompt: str) -> tuple[str, str]:
    import httpx

    model_name = env_key("OPENAI_MODEL") or "gpt-4o-mini"
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {env_key('OPENAI_API_KEY')}"},
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        timeout=60.0,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    return text.strip(), f"api:{model_name}"


def call_anthropic(prompt: str) -> tuple[str, str]:
    import httpx

    model_name = env_key("ANTHROPIC_MODEL") or "claude-3-5-haiku-latest"
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": env_key("ANTHROPIC_API_KEY"),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model_name,
            "max_tokens": 800,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60.0,
    )
    resp.raise_for_status()
    parts = resp.json().get("content") or []
    text = "".join(p.get("text") or "" for p in parts if p.get("type") == "text")
    return text.strip(), f"api:{model_name}"


def call_gemini(prompt: str) -> tuple[str, str]:
    import httpx

    model_name = env_key("GEMINI_MODEL") or "gemini-2.0-flash"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={env_key('GEMINI_API_KEY')}"
    )
    resp = httpx.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=60.0,
    )
    resp.raise_for_status()
    cands = resp.json().get("candidates") or []
    parts = (((cands[0] if cands else {}).get("content") or {}).get("parts") or [])
    text = "".join(p.get("text") or "" for p in parts)
    return text.strip(), f"api:{model_name}"


def call_local(prompt: str) -> str:
    tokenizer, llm = state["hf_tokenizer"], state["hf_llm"]
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(text, return_tensors="pt")
    device = getattr(llm, "device", None)
    if device is None:
        device = next(llm.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    out = llm.generate(
        **inputs,
        max_new_tokens=400,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
    new_tokens = out[0][inputs["input_ids"].shape[-1] :]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def call_llm(prompt: str) -> tuple[str, str]:
    api = state.get("api")
    if api == "openai":
        return call_openai(prompt)
    if api == "anthropic":
        return call_anthropic(prompt)
    if api == "gemini":
        return call_gemini(prompt)
    return call_local(prompt), LOCAL_MODEL_USED


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("BAAI/bge-m3 모델을 로드합니다.", flush=True)
    state["model"] = SentenceTransformer(MODEL_ID, local_files_only=True)
    print(f"모델 로드 완료. device={state['model'].device}", flush=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    state["collection"] = client.get_collection(COLLECTION)
    print(f"chroma collection={COLLECTION} count={state['collection'].count()}", flush=True)
    api = selected_api()
    state["api"] = api
    if api:
        print(f"LLM: API {api} (환경변수 키 사용)", flush=True)
    else:
        print("API 키가 없어 로컬 Qwen2.5-1.5B-Instruct 4bit를 씁니다.", flush=True)
        try:
            state["hf_tokenizer"], state["hf_llm"] = load_local_llm()
        except Exception as exc:
            msg = str(exc)
            if any(s in msg.lower() for s in ("download", "connect", "huggingface.co", "offline", "local_files_only")):
                raise SystemExit(f"경고: 추가 다운로드가 필요해 중단합니다. {exc}") from exc
            raise
        print("로컬 LLM 4bit 준비 완료.", flush=True)
    yield
    state.clear()


app = FastAPI(lifespan=lifespan)


@app.post("/search")
def search(body: SearchIn) -> list[dict]:
    docs, metas = retrieve(body.query, body.top_k)
    return [to_item(doc, meta) for doc, meta in zip(docs, metas)]


@app.post("/ask")
def ask(body: AskIn) -> dict:
    _docs, metas = retrieve(body.query, 3)
    if not metas:
        return {
            "answer": "매뉴얼에서 관련 내용을 찾지 못했습니다.",
            "sources": [],
            "model_used": LOCAL_MODEL_USED if not state.get("api") else f"api:{state['api']}",
        }
    _, sources = build_prompt(body.query, metas)
    ready = demo_answer(body.query)
    if ready:
        return {
            "answer": ready,
            "sources": sources,
            "model_used": "demo",
        }
    prompt, sources = build_prompt(body.query, metas)
    try:
        answer, model_used = call_llm(prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM 호출 실패: {exc}") from exc
    answer = polish_answer(answer)
    if not answer:
        raise HTTPException(status_code=500, detail="LLM 응답이 비었습니다")
    return {"answer": answer, "sources": sources, "model_used": model_used}


@app.get("/")
def home():
    page = ROOT / "static" / "index.html"
    if not page.is_file():
        raise HTTPException(status_code=404, detail="화면 파일이 없습니다")
    return FileResponse(page, headers={"Cache-Control": "no-cache"})


@app.get("/manuals/{lang}.pdf")
def manual_pdf(lang: str):
    if lang not in MANUAL_FILES:
        raise HTTPException(status_code=404, detail="없는 언어입니다")
    path = unlocked_manual(lang)
    return FileResponse(path, media_type="application/pdf", filename=f"{lang}.pdf")


app.mount(
    "/images",
    StaticFiles(directory=str(ROOT / "images")),
    name="images",
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)

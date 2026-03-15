"""
extract_from_pdf.py
───────────────────
시험지 PDF에서 영어 지문을 문항별로 추출하는 스크립트.
LLM API의 structured output을 사용하여 정확한 형식을 보장한다.

사용법:
    python extract_from_pdf.py 고3_2025_11월_수능/시험지.pdf
    python extract_from_pdf.py 고3_2025_11월_수능/시험지.pdf -p claude
    python extract_from_pdf.py 고3_2025_11월_수능/시험지.pdf --skip-existing
"""

import argparse
import base64
import sys
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Pydantic 스키마 (structured output용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ExtractedPassage(BaseModel):
    problem_number: int = Field(description="문항 번호 (41-42는 41, 43-45는 43)")
    passage: str = Field(description="영어 지문 본문 (문제 지시문·선택지 제외)")


class ExamExtraction(BaseModel):
    passages: list[ExtractedPassage] = Field(description="추출된 문항별 지문 목록")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 문항 번호 규칙
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 25~28번 생략, 41-42는 41번, 43-45는 43번
PROBLEM_NUMBERS = [
    18, 19, 20, 21, 22, 23, 24,
    29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
    41,  # 41-42번 통합
    43,  # 43-45번 통합
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 프롬프트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM_PROMPT = """\
You are an expert at extracting English reading passages from Korean college \
entrance exam (수능/모의고사) PDF files.

Your task: Given a PDF of a Korean English exam, extract the English passage \
for each specified question number.

RULES:
1. Extract ONLY the English reading passage (지문) for each question.
2. Do NOT include:
   - Question stems (e.g., "다음 글의 주제로 가장 적절한 것은?")
   - Answer choices (①②③④⑤)
   - Footnotes or annotations (e.g., "* 주 ..." at the bottom)
   - Question numbers or labels
3. For questions 41-42 (장문), extract the single shared passage \
and return it under problem_number 41.
4. For questions 43-45 (장문), extract the single shared passage \
and return it under problem_number 43.
5. Preserve the original English text exactly as written in the PDF. \
Do not fix grammar, spelling, or punctuation.
6. Use natural line breaks at word boundaries, roughly 55-65 characters per line.
7. If a passage contains a blank (빈칸), represent it as a line of underscores: \
_______________
8. Include any quoted text, examples, or embedded dialogue that is part of the passage.
9. Skip questions 25-28 entirely (듣기/말하기 영역).
"""

USER_PROMPT = """\
이 시험지 PDF에서 다음 문항 번호의 영어 지문을 추출해 주세요:
{numbers}

주의사항:
- 25~28번은 생략합니다.
- 41~42번은 하나의 지문이므로 problem_number를 41로 저장합니다.
- 43~45번은 하나의 지문이므로 problem_number를 43으로 저장합니다.
- 한국어 문제 지시문이나 선택지(①②③④⑤)는 포함하지 마세요.
- 영어 지문 본문만 추출하세요.
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API 호출
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _call_openai(
    pdf_base64: str,
    pdf_filename: str,
    api_key: Optional[str],
    model: Optional[str],
    temperature: float,
) -> ExamExtraction:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = model or "gpt-5.4"

    numbers_str = ", ".join(str(n) for n in PROBLEM_NUMBERS)
    user_text = USER_PROMPT.format(numbers=numbers_str)

    resp = client.beta.chat.completions.parse(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "file",
                        "file": {
                            "filename": pdf_filename,
                            "file_data": f"data:application/pdf;base64,{pdf_base64}",
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            },
        ],
        response_format=ExamExtraction,
    )
    parsed = resp.choices[0].message.parsed
    if parsed is None:
        raise ValueError("OpenAI 응답을 파싱할 수 없습니다.")
    return parsed


def _call_claude(
    pdf_base64: str,
    pdf_filename: str,
    api_key: Optional[str],
    model: Optional[str],
    temperature: float,
) -> ExamExtraction:
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    model = model or "claude-sonnet-4-20250514"

    numbers_str = ", ".join(str(n) for n in PROBLEM_NUMBERS)
    user_text = USER_PROMPT.format(numbers=numbers_str)

    resp = client.messages.parse(
        model=model,
        max_tokens=16384,
        temperature=temperature,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_base64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            },
        ],
        output_format=ExamExtraction,
    )
    parsed = resp.parsed_output
    if parsed is None:
        raise ValueError("Claude 응답을 파싱할 수 없습니다.")
    return parsed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def extract_from_pdf(
    pdf_path: Path,
    *,
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
    output_dir: Optional[Path] = None,
    skip_existing: bool = False,
) -> dict[int, str]:
    """시험지 PDF에서 문항별 영어 지문을 추출한다.

    Returns:
        {문항번호: 지문} dict
    """
    pdf_path = Path(pdf_path).resolve()
    if not pdf_path.exists():
        print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")
        sys.exit(1)

    if output_dir is None:
        output_dir = pdf_path.parent / "원문"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 이미 존재하는 파일 확인
    existing: set[int] = set()
    if skip_existing:
        existing = {int(f.stem) for f in output_dir.glob("*.txt") if f.stem.isdigit()}
        needed = [n for n in PROBLEM_NUMBERS if n not in existing]
        if not needed:
            print("⏭️  모든 문항이 이미 존재합니다.")
            return {}
        print(f"📋 추출 대상: {len(needed)}개 문항 (기존 {len(existing)}개 건너뜀)")

    # PDF → base64
    print(f"📄 PDF 읽는 중: {pdf_path.name}")
    pdf_base64 = base64.standard_b64encode(pdf_path.read_bytes()).decode("utf-8")

    # API 호출
    provider = provider.lower().strip()
    print(f"📡 {provider} API 호출 중... (시간이 걸릴 수 있습니다)")

    if provider == "openai":
        result = _call_openai(pdf_base64, pdf_path.name, api_key, model, temperature)
    elif provider in ("claude", "anthropic"):
        result = _call_claude(pdf_base64, pdf_path.name, api_key, model, temperature)
    else:
        print(f"❌ 지원하지 않는 provider: {provider!r}  (openai 또는 claude)")
        sys.exit(1)

    # 결과 저장
    passages: dict[int, str] = {}
    for item in result.passages:
        num = item.problem_number
        if num not in PROBLEM_NUMBERS:
            print(f"⚠️  예상하지 않은 문항 번호 {num}, 건너뜀")
            continue
        if skip_existing and num in existing:
            continue

        text = item.passage.strip()
        txt_path = output_dir / f"{num}.txt"
        txt_path.write_text(text + "\n", encoding="utf-8")
        passages[num] = text
        print(f"✅ {num}번 → {txt_path.name}")

    # 누락 문항 확인
    extracted = set(passages.keys()) | existing
    missing = set(PROBLEM_NUMBERS) - extracted
    if missing:
        print(f"⚠️  누락된 문항: {sorted(missing)}")

    return passages


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="시험지 PDF에서 문항별 영어 지문 추출",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
예시:
  python extract_from_pdf.py 고3_2025_11월_수능/시험지.pdf
  python extract_from_pdf.py 고3_2025_11월_수능/시험지.pdf -p claude
  python extract_from_pdf.py 고3_2025_3월_모고/시험지.pdf --skip-existing
""",
    )
    parser.add_argument("pdf", help="시험지 PDF 파일 경로")
    parser.add_argument(
        "-p", "--provider", default="openai",
        choices=["openai", "claude"],
        help="사용할 API (기본: openai)",
    )
    parser.add_argument("-k", "--api-key", default=None, help="API 키 (생략하면 환경변수)")
    parser.add_argument("-m", "--model", default=None, help="모델명 (생략하면 기본값)")
    parser.add_argument(
        "-t", "--temperature", type=float, default=0.1,
        help="생성 온도 (기본: 0.1)",
    )
    parser.add_argument(
        "-o", "--output-dir", default=None,
        help="출력 디렉토리 (기본: PDF와 같은 폴더의 원문/)",
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="이미 .txt 파일이 있는 문항은 건너뛴다",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None

    passages = extract_from_pdf(
        Path(args.pdf),
        provider=args.provider,
        api_key=args.api_key,
        model=args.model,
        temperature=args.temperature,
        output_dir=output_dir,
        skip_existing=args.skip_existing,
    )

    print(f"\n🎉 완료! {len(passages)}개 문항 추출됨")

"""
text_to_json.py
───────────────
영어 본문을 LLM API에 보내 문장별 해설 JSON을 생성하는 모듈.
OpenAI, Claude(Anthropic) 두 가지 API를 지원한다.

사전 설치:
    pip install openai anthropic

사용법:
    # ── Python에서 ──
    from text_to_json import text_to_json

    result = text_to_json(
        text="Everyone likes to think of themselves as...",
        provider="openai",        # 또는 "claude"
        api_key="sk-...",
        model="gpt-4o",           # 또는 "claude-sonnet-4-20250514"
    )
    # result → dict (JSON 구조)

    # ── CLI에서 ──
    python text_to_json.py input.txt -p claude -k sk-ant-... -o output.json
    python text_to_json.py input.txt -p openai -k sk-...    -o output.json
"""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Pydantic 스키마
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class VocabularyItem(BaseModel):
    word: str
    meaning: str
    note: str


class Sentence(BaseModel):
    id: int
    original: str
    explanation: str
    vocabulary: list[VocabularyItem]


class PassageAnalysis(BaseModel):
    title: str
    summary: str
    sentences: list[Sentence]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 시스템 프롬프트 & 유저 프롬프트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM_PROMPT = """\
You are an expert English-Korean language tutor.
Your job: given an English passage, produce a structured analysis
that breaks the passage into individual sentences with
Korean explanations and vocabulary notes.

RULES:
1. Split the passage into individual sentences.
2. For each sentence, pick key vocabulary words or phrases
   that a Korean learner would benefit from knowing.
   - Choose 1-5 words/phrases per sentence.
   - Prefer words that are less common, idiomatic, or used
     in a non-obvious way.
3. For each vocabulary item provide:
   - "word": the word/phrase as it appears (or its base form
     if inflected). Multi-word phrases are OK.
   - "meaning": concise Korean translation/definition.
   - "note": optional extra context (etymology, usage tip,
     related forms). Use empty string "" if nothing to add.
4. Write "explanation" in natural Korean — a clear
   paraphrase/interpretation of the sentence's meaning,
   not a mechanical word-by-word translation.
5. Add a "title" (Korean, concise) and a one-line "summary"
   capturing the passage's core message.
"""

USER_PROMPT_TEMPLATE = """\
아래 영어 본문을 분석해서 JSON을 생성해 주세요.

--- 본문 시작 ---
{text}
--- 본문 끝 ---
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def text_to_json(
    text: str,
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> dict:
    """영어 본문 → 문장별 해설 JSON dict 반환.

    Args:
        text:        분석할 영어 본문 문자열.
        provider:    "openai" 또는 "claude".
        api_key:     API 키. None이면 환경변수에서 자동 로드.
                     (OPENAI_API_KEY / ANTHROPIC_API_KEY)
        model:       사용할 모델명. None이면 provider별 기본값 사용.
        temperature: 생성 온도 (0.0 ~ 1.0). 낮을수록 일관적.

    Returns:
        파싱된 dict (motivated_reasoning_data.json과 동일 구조).
    """
    provider = provider.lower().strip()
    user_message = USER_PROMPT_TEMPLATE.format(text=text.strip())

    if provider == "openai":
        result = _call_openai(user_message, api_key, model, temperature)
    elif provider in ("claude", "anthropic"):
        result = _call_claude(user_message, api_key, model, temperature)
    else:
        raise ValueError(f"지원하지 않는 provider: {provider!r}  (openai 또는 claude)")

    return result.model_dump()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OpenAI 호출
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _call_openai(
    user_message: str, api_key: Optional[str], model: Optional[str], temperature: float
) -> PassageAnalysis:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)  # api_key=None → 환경변수 OPENAI_API_KEY 사용
    model = model or "gpt-5.4"

    resp = client.beta.chat.completions.parse(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format=PassageAnalysis,
    )
    parsed = resp.choices[0].message.parsed
    if parsed is None:
        raise ValueError("OpenAI 응답을 파싱할 수 없습니다.")
    return parsed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Claude (Anthropic) 호출
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _call_claude(
    user_message: str, api_key: Optional[str], model: Optional[str], temperature: float
) -> PassageAnalysis:
    from anthropic import Anthropic

    client = Anthropic(
        api_key=api_key
    )  # api_key=None → 환경변수 ANTHROPIC_API_KEY 사용
    model = model or "claude-sonnet-4-20250514"

    resp = client.messages.parse(
        model=model,
        max_tokens=4096,
        temperature=temperature,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message},
        ],
        output_format=PassageAnalysis,
    )
    parsed = resp.parsed_output
    if parsed is None:
        raise ValueError("Claude 응답을 파싱할 수 없습니다.")
    return parsed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="영어 본문 → 문장별 해설 JSON 생성 (OpenAI / Claude)"
    )
    parser.add_argument("input", help="입력 텍스트 파일 경로")
    parser.add_argument(
        "-p",
        "--provider",
        default="openai",
        choices=["openai", "claude"],
        help="사용할 API (기본: openai)",
    )
    parser.add_argument(
        "-k", "--api-key", default=None, help="API 키 (생략하면 환경변수에서 로드)"
    )
    parser.add_argument(
        "-m", "--model", default=None, help="모델명 (생략하면 provider별 기본값)"
    )
    parser.add_argument(
        "-t", "--temperature", type=float, default=0.3, help="생성 온도 (기본: 0.3)"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output.json",
        help="출력 JSON 파일 경로 (기본: output.json)",
    )
    args = parser.parse_args()

    input_text = Path(args.input).read_text(encoding="utf-8")

    print(f"📡 {args.provider} API 호출 중...")
    result = text_to_json(
        text=input_text,
        provider=args.provider,
        api_key=args.api_key,
        model=args.model,
        temperature=args.temperature,
    )

    out = Path(args.output)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ JSON 생성 완료 → {out.resolve()}")

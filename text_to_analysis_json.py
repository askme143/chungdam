"""
text_to_analysis_json.py
────────────────────────
영어 본문을 LLM API에 보내 본문분석(구문분석·지문구조·핵심단어·패러프레이징) JSON을 생성하는 모듈.
OpenAI, Claude(Anthropic) 두 가지 API를 지원한다.

사전 설치:
    pip install openai anthropic

사용법:
    # ── Python에서 ──
    from text_to_analysis_json import text_to_analysis_json

    result = text_to_analysis_json(
        text="The economic benefit of culturtainment...",
        provider="openai",
        api_key="sk-...",
    )
    # result → dict (FullPassageAnalysis 구조)

    # ── CLI에서 ──
    python text_to_analysis_json.py input.txt -p claude -o output.json
"""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Pydantic 스키마
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class StructureSection(BaseModel):
    label: str
    english: str
    korean: str


class KeyVocabItem(BaseModel):
    word: str
    meaning: str
    synonyms: list[str]
    antonyms: list[str]
    emphasized: bool


class AnalyzedPhrase(BaseModel):
    text: str
    type: str
    label: Optional[str] = None
    annotation_above: Optional[str] = None
    annotation_below: Optional[str] = None
    children: list["AnalyzedPhrase"] = []


class SentenceAnalysis(BaseModel):
    id: int
    type_label: str
    phrases: list[AnalyzedPhrase]
    korean: str
    points: list[str]
    paraphrase_en: str
    paraphrase_ko: str


class FullPassageAnalysis(BaseModel):
    title_en: str
    title_ko: str
    theme_en: str
    theme_ko: str
    summary_en: str
    summary_ko: str
    structure: list[StructureSection]
    key_vocabulary: list[KeyVocabItem]
    sentences: list[SentenceAnalysis]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 시스템 프롬프트 & 유저 프롬프트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM_PROMPT = """\
You are an expert English-Korean language tutor specializing in \
Korean college entrance exam (수능) English reading comprehension.

Your job: given an English passage, produce a structured JSON analysis \
that includes passage structure, title/theme/summary, key vocabulary, \
and detailed sentence-by-sentence grammatical analysis.

═══════════════════════════════════════════════
SECTION 1: 지문 구조 (structure)
═══════════════════════════════════════════════
Identify the logical flow of the passage using these labels:
- 도입 (Introduction)
- 문제 (Problem)
- 반론 (Counter-argument)
- 근거 (Evidence)
- 부연 (Elaboration)
- 예시 (Example)
- 결론 (Conclusion)

For each section:
- english: copy the ORIGINAL sentence(s) from the passage verbatim. \
Do NOT summarize, paraphrase, or add meta-commentary like \
"The passage begins by stating that...". Just use the exact sentence \
from the text.
- korean: direct Korean translation of that original sentence only. \
Do NOT add meta-commentary like "~라고 말하며 시작한다", \
"~라고 설명한다", "~라고 경고한다". Just translate the sentence itself.
Typically 3-5 sections.

═══════════════════════════════════════════════
SECTION 2: 제목, 주제, 요약
═══════════════════════════════════════════════
- title_en/title_ko: concise passage title
- theme_en/theme_ko: one-sentence topic statement
- summary_en/summary_ko: one-sentence summary

═══════════════════════════════════════════════
SECTION 3: 핵심 단어 (key_vocabulary)
═══════════════════════════════════════════════
Select 10-18 important vocabulary words from the passage.
For each word:
- word: the word as it appears (base form if inflected)
- meaning: Korean meaning
- synonyms: 0-3 English synonyms
- antonyms: 0-3 English antonyms
- emphasized: true if it's a commonly tested word on 수능

═══════════════════════════════════════════════
SECTION 4: 문장별 분석 (sentences)
═══════════════════════════════════════════════
For EACH sentence in the passage, provide:

1) id: sentence number (starting from 1)

2) type_label: sentence role in the passage
   - 주제문, 부연, 서술, 삽입, 비판, 결론

3) phrases: a tree of AnalyzedPhrase objects representing the \
   grammatical structure. This is the CORE of the analysis.

4) korean: full Korean translation

5) points: grammar tips (0-2 items). Only include when there's \
   a notable grammar pattern tested on 수능. Empty list if none.

6) paraphrase_en: simplified English restatement
7) paraphrase_ko: Korean translation of the paraphrase

═══════════════════════════════════════════════
AnalyzedPhrase TREE STRUCTURE
═══════════════════════════════════════════════

Each phrase node has:
- text: the actual text span (empty string "" for container nodes)
- type: one of:
  - "plain": normal text
  - "bold": main verbs only (V, 5V, 3V labels). Do NOT use bold for complements (C, OC), discourse markers (However, But), or other non-verb elements.
  - "underline": subjects, important nouns to emphasize
  - "boxed": relative pronouns like "that", "which" (shown with border)
  - "bracket": groups a phrase in parentheses ( )
  - "slash": represents "/" separator between major clause boundaries
- label: grammar annotation in RED below the text. Use these labels:
  - S (주어), V (동사), O (목적어), OC (목적보어), C (보어)
  - 5V (5형식 동사), 3V (3형식 동사), etc.
  - 주관대 (주격관계대명사), 목관대 (목적격관계대명사)
  - 과거 분사구문, 현재 분사구문
  - 형용사적 용법, 부사적 용법, 명사적 용법
  - 병렬1, 병렬2 (parallel structure markers)
  - null if no label needed
  NOTE: Do NOT use "삽입" as a phrase label. Words like "However,", \
"Yes,", "Overall,", "In other words," are discourse markers — \
use "plain" type with label null.

IMPORTANT LABELING RULES:
- O (목적어) should only be labeled on the DIRECT noun/noun phrase \
that is the object, not on to-infinitive phrases in general.
- "persuade/encourage/allow/enable + O + to do" is 5형식: \
label the verb as 5V, the noun as O, and "to do" as OC (목적보어).
- "to persuade ..." modifying a noun like "efforts" is 형용사적 용법; \
"to persuade ..." expressing purpose/reason is 부사적 용법. \
Do NOT confuse these two — 형용사적 용법 modifies a noun directly; \
부사적 용법 answers "why" or "in order to".
- Keep each labeled phrase SHORT (1-3 words). If a phrase is longer, \
split it into multiple phrase nodes with separate labels.
- annotation_above: text shown ABOVE the word (for common mistakes)
  - e.g., "attractively (X)" above "attractive" to warn against \
    confusing adjective with adverb
  - null if not needed
- annotation_below: text shown BELOW the word
  - e.g., "≠ delusion (망상, 착각)" to distinguish similar words
  - "≠ prescribed (지방하다)" for commonly confused words
  - null if not needed
- children: nested phrase nodes (empty [] for leaf nodes)

STRUCTURAL RULES:
- Use "slash" nodes to separate major clause boundaries
- Use "bracket" nodes to group prepositional phrases, relative \
  clauses, and other modifying structures
- Brackets can be nested (e.g., PP inside a relative clause)
- Mark subjects with "underline" type + label "S"
- Mark main verbs with "bold" type + label "V" (or "5V", "3V")
- Mark relative pronoun "that/which/who" with "boxed" type
- Use annotation_above sparingly — only for common word confusion
- Use annotation_below for confusable word pairs (≠ similar word)

═══════════════════════════════════════════════
FEW-SHOT EXAMPLE
═══════════════════════════════════════════════

For the sentence:
"The economic benefit of culturtainment makes it attractive to \
politicians and policy makers alike."

The correct phrases array is:
[
  {"text": "The economic benefit", "type": "underline", "label": "S", \
"annotation_above": null, "annotation_below": null, "children": []},
  {"text": "", "type": "bracket", "label": null, \
"annotation_above": null, "annotation_below": null, "children": [
    {"text": "of culturtainment", "type": "plain", "label": null, \
"annotation_above": null, "annotation_below": null, "children": []}
  ]},
  {"text": "makes", "type": "bold", "label": "5V", \
"annotation_above": null, "annotation_below": null, "children": []},
  {"text": "it", "type": "plain", "label": "O", \
"annotation_above": null, "annotation_below": null, "children": []},
  {"text": "attractive", "type": "plain", "label": "OC", \
"annotation_above": "attractively (X)", "annotation_below": null, \
"children": []},
  {"text": "", "type": "bracket", "label": null, \
"annotation_above": null, "annotation_below": null, "children": [
    {"text": "to politicians and policy makers alike.", "type": "plain", \
"label": null, "annotation_above": null, "annotation_below": null, \
"children": []}
  ]}
]

For the sentence:
"However, such commercialization risks culturtainment becoming \
homogeneous and losing its original 'message' that could lead \
to a dilution of audiences."

The correct phrases array shows:
- "However," as plain with label null (discourse markers are never bold)
- "such commercialization" as underline with label "S"
- "risks" as bold with label "V"
- slash "/" separator
- "becoming" bold with label "병렬1"
- "losing" bold with label "병렬2"
- bracket containing "that" as boxed with label "주관대"
- "dilution" with annotation_below "≠ delusion (망상, 착각)"
- points: ["동사 risk는 3형식 동사로 '~가 ...하는 위험이 있다'로 \
해석되는데 목적어 자리에 동명사를 취한다. 접속사 and에 의해 목적어 \
becoming과 losing이 병렬로 묶인 구조이며, culturtainment는 동명사의 \
의미상 주어이다."]

═══════════════════════════════════════════════
WRITING STYLE (매우 중요)
═══════════════════════════════════════════════
- 모든 한국어 설명(korean, meaning, points, paraphrase_ko, \
  structure korean)은 고등학생이 쉽게 이해할 수 있도록 \
  쉬운 우리말로 풀어서 써라.
- 어려운 한자어(예: 수반하다, 촉진하다, 함의, 내재적)를 \
  가급적 피하고, 같은 뜻의 쉬운 표현으로 바꿔라.
- 한 문장이 너무 길면 짧게 나눠서 설명해라.
- 설명을 읽는 학생이 사전 없이도 바로 이해할 수 있어야 한다.
"""

USER_PROMPT_TEMPLATE = """\
아래 영어 본문을 분석해서 본문분석 JSON을 생성해 주세요.
지문의 모든 문장에 대해 구문분석을 수행하세요.

--- 본문 시작 ---
{text}
--- 본문 끝 ---
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def text_to_analysis_json(
    text: str,
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> dict:
    """영어 본문 → 본문분석 JSON dict 반환.

    Args:
        text:        분석할 영어 본문 문자열.
        provider:    "openai" 또는 "claude".
        api_key:     API 키. None이면 환경변수에서 자동 로드.
        model:       사용할 모델명. None이면 provider별 기본값 사용.
        temperature: 생성 온도 (0.0 ~ 1.0).

    Returns:
        파싱된 dict (FullPassageAnalysis 구조).
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
) -> FullPassageAnalysis:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = model or "gpt-5.4"

    resp = client.beta.chat.completions.parse(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format=FullPassageAnalysis,
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
) -> FullPassageAnalysis:
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    model = model or "claude-sonnet-4-20250514"

    resp = client.messages.parse(
        model=model,
        max_tokens=8192,
        temperature=temperature,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message},
        ],
        output_format=FullPassageAnalysis,
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
        description="영어 본문 → 본문분석 JSON 생성 (OpenAI / Claude)"
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
        default="analysis_output.json",
        help="출력 JSON 파일 경로 (기본: analysis_output.json)",
    )
    args = parser.parse_args()

    input_text = Path(args.input).read_text(encoding="utf-8")

    print(f"📡 {args.provider} API 호출 중 (본문분석)...")
    result = text_to_analysis_json(
        text=input_text,
        provider=args.provider,
        api_key=args.api_key,
        model=args.model,
        temperature=args.temperature,
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 분석 JSON 생성 완료 → {out.resolve()}")

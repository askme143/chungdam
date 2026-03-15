"""
pipeline.py
───────────
text_to_json → generate_viewer → generate_index 를 한 번에 실행하는 CLI 스크립트.

디렉토리 구조 규칙:
    {시험지정보}/{원문|문장별|페이지}
    예) 고3_2025_11월_수능/원문/34.txt
      → 고3_2025_11월_수능/문장별/34.json
      → 고3_2025_11월_수능/페이지/34.html

사용법:
    # 단일 파일 처리
    python pipeline.py 고3_2025_11월_수능/원문/34.txt

    # 여러 파일 처리
    python pipeline.py 고3_2025_11월_수능/원문/34.txt 고3_2025_11월_수능/원문/35.txt

    # 원문 폴더 전체 처리
    python pipeline.py 고3_2025_11월_수능/원문/

    # provider / model 지정
    python pipeline.py 고3_2025_11월_수능/원문/34.txt -p claude -m claude-sonnet-4-20250514
"""

import argparse
import json
import sys
from pathlib import Path

from text_to_json import text_to_json
from generate_viewer import generate_html
from generate_index import generate_index


ROOT = Path(__file__).parent


def _find_next_page(html_path: Path) -> str | None:
    """같은 페이지 디렉토리에서 다음 번호의 HTML 파일명을 반환한다."""
    page_dir = html_path.parent
    current_num = int(html_path.stem)
    siblings = sorted(
        [f for f in page_dir.glob("*.html") if f.stem.isdigit()],
        key=lambda f: int(f.stem),
    )
    # 아직 생성 안 된 파일도 고려: 현재 파일 포함
    nums = [int(f.stem) for f in siblings]
    if current_num not in nums:
        nums.append(current_num)
        nums.sort()
    idx = nums.index(current_num)
    if idx < len(nums) - 1:
        return f"{nums[idx + 1]}.html"
    return None


def resolve_input_files(paths: list[str]) -> list[Path]:
    """입력 경로들을 개별 .txt 파일 목록으로 변환한다.

    - 파일 경로 → 그대로 사용
    - 디렉토리 경로 → 하위 .txt 파일 전부 수집
    """
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            found = sorted(path.glob("*.txt"))
            if not found:
                print(f"⚠️  디렉토리에 .txt 파일 없음: {path}")
            files.extend(found)
        elif path.is_file():
            files.append(path)
        else:
            print(f"⚠️  파일을 찾을 수 없음: {path}")
    return files


def validate_structure(txt_path: Path) -> tuple[Path, Path, Path]:
    """원문 파일 경로가 {시험지정보}/원문/XX.txt 구조인지 확인하고,
    대응하는 JSON·HTML 경로를 반환한다.

    Returns:
        (txt_path, json_path, html_path)

    Raises:
        SystemExit: 경로가 규칙에 맞지 않을 때
    """
    txt_path = txt_path.resolve()

    # 부모가 '원문'이어야 한다
    if txt_path.parent.name != "원문":
        print(f"❌ 파일이 '원문' 폴더 안에 있어야 합니다: {txt_path}")
        print(f"   예) 고3_2025_11월_수능/원문/34.txt")
        sys.exit(1)

    exam_dir = txt_path.parent.parent  # 시험지정보 폴더
    stem = txt_path.stem

    json_path = exam_dir / "문장별" / f"{stem}.json"
    html_path = exam_dir / "페이지" / f"{stem}.html"

    return txt_path, json_path, html_path


def process_file(
    txt_path: Path,
    json_path: Path,
    html_path: Path,
    *,
    provider: str,
    api_key: str | None,
    model: str | None,
    temperature: float,
    skip_existing: bool,
) -> bool:
    """단일 파일에 대해 text→json→html 파이프라인을 실행한다.

    Returns:
        True if processed, False if skipped.
    """
    label = f"{txt_path.parent.parent.name}/{txt_path.stem}"

    # ── 1) text_to_json ──
    if skip_existing and json_path.exists():
        print(f"⏭️  JSON 이미 존재, 건너뜀: {label}")
    else:
        print(f"📡 [{label}] {provider} API 호출 중...")
        input_text = txt_path.read_text(encoding="utf-8").strip()
        if not input_text:
            print(f"⚠️  빈 파일, 건너뜀: {txt_path}")
            return False

        result = text_to_json(
            text=input_text,
            provider=provider,
            api_key=api_key,
            model=model,
            temperature=temperature,
        )

        result["problem_number"] = stem

        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"✅ [{label}] JSON 생성 → {json_path.name}")

    # ── 2) generate_viewer ──
    # 기존 JSON에 problem_number가 없으면 추가
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "problem_number" not in data:
        data["problem_number"] = stem
        json_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # next_page 계산
    next_page = _find_next_page(html_path)

    html_path.parent.mkdir(parents=True, exist_ok=True)
    generate_html(str(json_path), str(html_path), next_page=next_page)
    print(f"✅ [{label}] HTML 생성 → {html_path.name}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="원문 → JSON → HTML → index.html 전체 파이프라인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
예시:
  python pipeline.py 고3_2025_11월_수능/원문/34.txt
  python pipeline.py 고3_2025_11월_수능/원문/
  python pipeline.py 고3_2025_11월_수능/원문/ -p claude
  python pipeline.py 고3_2025_11월_수능/원문/34.txt --skip-existing
""",
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="원문 .txt 파일 또는 원문 디렉토리 (여러 개 가능)",
    )
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
        "-t",
        "--temperature",
        type=float,
        default=0.3,
        help="생성 온도 (기본: 0.3)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="이미 JSON이 존재하면 API 호출을 건너뛴다 (HTML은 항상 재생성)",
    )
    args = parser.parse_args()

    # ── 입력 파일 수집 ──
    txt_files = resolve_input_files(args.input)
    if not txt_files:
        print("❌ 처리할 .txt 파일이 없습니다.")
        sys.exit(1)

    # ── 구조 검증 ──
    targets = [validate_structure(f) for f in txt_files]

    print(f"\n{'='*50}")
    print(f"📋 처리 대상: {len(targets)}개 파일")
    for txt, json_p, _ in targets:
        status = "📄" if not json_p.exists() else "📄 (JSON 존재)"
        print(f"   {status} {txt.parent.parent.name}/{txt.stem}")
    print(f"{'='*50}\n")

    # ── 파이프라인 실행 ──
    processed = 0
    for txt, json_p, html_p in targets:
        if process_file(
            txt,
            json_p,
            html_p,
            provider=args.provider,
            api_key=args.api_key,
            model=args.model,
            temperature=args.temperature,
            skip_existing=args.skip_existing,
        ):
            processed += 1

    # ── 3) index.html 갱신 ──
    if processed > 0:
        generate_index()

    print(f"\n🎉 완료! ({processed}/{len(targets)}개 처리됨)")


if __name__ == "__main__":
    main()

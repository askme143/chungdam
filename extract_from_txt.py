"""
extract_from_txt.py
───────────────────
수능특강 텍스트 파일에서 지문을 개별 파일로 분리하는 스크립트.

[Gateway], [01], [02] 등의 마커를 기준으로 지문을 분리하여
원문/ 폴더에 저장한다.

사용법:
    # 단일 파일 처리
    python extract_from_txt.py "수특_2027_1강/01강 - 글의 목적 파악.txt"

    # 디렉토리 내 모든 txt 처리
    python extract_from_txt.py 수특_2027_1강/

    # 이미 존재하는 파일 건너뛰기
    python extract_from_txt.py 수특_2027_1강/ --skip-existing
"""

import argparse
import re
import sys
from pathlib import Path


# [Gateway], [01], [02] 등의 마커 패턴
MARKER_PATTERN = re.compile(r"^\[(.+?)\]\s*$", re.MULTILINE)


def extract_passages(text: str) -> dict[str, str]:
    """텍스트에서 [마커]별 지문을 추출한다.

    Returns:
        {마커: 지문} dict (예: {"Gateway": "Dear students,...", "01": "Dear Parents,..."})
    """
    markers = list(MARKER_PATTERN.finditer(text))
    if not markers:
        print("⚠️  마커([Gateway], [01] 등)를 찾을 수 없습니다.")
        return {}

    passages: dict[str, str] = {}
    for i, match in enumerate(markers):
        marker = match.group(1)
        start = match.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        passage = text[start:end].strip()
        if passage:
            passages[marker] = passage

    return passages


def extract_from_txt(
    txt_path: Path,
    *,
    output_dir: Path | None = None,
    skip_existing: bool = False,
) -> dict[str, str]:
    """수특 텍스트 파일에서 지문을 추출하여 개별 파일로 저장한다.

    Returns:
        {마커: 지문} dict (저장된 것만)
    """
    txt_path = Path(txt_path).resolve()
    if not txt_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {txt_path}")
        sys.exit(1)

    if output_dir is None:
        output_dir = txt_path.parent / "원문"
    output_dir.mkdir(parents=True, exist_ok=True)

    text = txt_path.read_text(encoding="utf-8")
    passages = extract_passages(text)

    if not passages:
        return {}

    saved: dict[str, str] = {}
    for marker, passage in passages.items():
        out_path = output_dir / f"{marker}.txt"
        if skip_existing and out_path.exists():
            print(f"⏭️  이미 존재, 건너뜀: {out_path.name}")
            continue
        out_path.write_text(passage + "\n", encoding="utf-8")
        saved[marker] = passage
        print(f"✅ [{marker}] → {out_path.name}")

    return saved


def resolve_input_files(paths: list[str]) -> list[Path]:
    """입력 경로들을 .txt 파일 목록으로 변환한다.

    디렉토리가 주어지면 하위 .txt 파일 수집 (원문/ 폴더는 제외).
    """
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            found = sorted(
                f
                for f in path.glob("*.txt")
                if f.parent.name != "원문"
            )
            if not found:
                print(f"⚠️  디렉토리에 .txt 파일 없음: {path}")
            files.extend(found)
        elif path.is_file():
            files.append(path)
        else:
            print(f"⚠️  파일을 찾을 수 없음: {path}")
    return files


def main():
    parser = argparse.ArgumentParser(
        description="수능특강 텍스트에서 지문별 원문 추출",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
예시:
  python extract_from_txt.py "수특_2027_1강/01강 - 글의 목적 파악.txt"
  python extract_from_txt.py 수특_2027_1강/
  python extract_from_txt.py 수특_2027_1강/ --skip-existing
""",
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="수특 .txt 파일 또는 디렉토리 (여러 개 가능)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="출력 디렉토리 (기본: 입력 파일과 같은 폴더의 원문/)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="이미 파일이 있으면 건너뛴다",
    )
    args = parser.parse_args()

    txt_files = resolve_input_files(args.input)
    if not txt_files:
        print("❌ 처리할 .txt 파일이 없습니다.")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else None

    total = 0
    for txt_file in txt_files:
        print(f"\n📄 처리 중: {txt_file.name}")
        passages = extract_from_txt(
            txt_file,
            output_dir=output_dir,
            skip_existing=args.skip_existing,
        )
        total += len(passages)

    print(f"\n🎉 완료! {total}개 지문 추출됨")


if __name__ == "__main__":
    main()

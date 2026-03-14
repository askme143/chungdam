"""
generate_index.py
─────────────────
프로젝트 루트의 디렉토리 구조를 스캔하여 index.html을 자동 생성한다.

사용법:
    python generate_index.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent

# 디렉토리 이름 → 표시 이름 변환
# 예: "고3_2025_3월_모고" → "고3 2025년 3월 모의고사"
_TYPE_MAP = {"모고": "모의고사", "수능": "수능"}


def _display_name(dirname: str) -> str:
    """디렉토리 이름을 사람이 읽기 좋은 형태로 변환한다."""
    m = re.match(r"(.+?)_(\d{4})_(\d{1,2})월_(.+)", dirname)
    if not m:
        return dirname
    grade, year, month, exam_type = m.groups()
    exam_label = _TYPE_MAP.get(exam_type, exam_type)
    return f"{grade} {year}년 {month}월 {exam_label}"


def _sort_key(dirname: str):
    """연도·월 기준 내림차순 정렬 키."""
    m = re.match(r".+?_(\d{4})_(\d{1,2})월_", dirname)
    if m:
        return (-int(m.group(1)), -int(m.group(2)))
    return (0, 0)


def generate_index(output_path: Path | None = None) -> str:
    output_path = output_path or ROOT / "index.html"

    # 시험 디렉토리 탐색: 하위에 "페이지" 폴더가 있는 디렉토리
    exam_dirs = sorted(
        [d for d in ROOT.iterdir() if d.is_dir() and (d / "페이지").is_dir()],
        key=lambda d: _sort_key(d.name),
    )

    groups_html = ""
    for exam_dir in exam_dirs:
        page_dir = exam_dir / "페이지"
        html_files = sorted(page_dir.glob("*.html"), key=lambda f: int(f.stem) if f.stem.isdigit() else f.stem)

        display = _display_name(exam_dir.name)

        if html_files:
            links = "\n      ".join(
                f'<a href="{exam_dir.name}/페이지/{f.name}">{f.stem}번</a>'
                for f in html_files
            )
            groups_html += f"""
  <div class="exam-group">
    <h2>{display}</h2>
    <div class="page-list">
      {links}
    </div>
  </div>
"""
        else:
            groups_html += f"""
  <div class="exam-group">
    <h2>{display}</h2>
    <p style="color: var(--text-sub); font-size: 0.9rem;">준비 중...</p>
  </div>
"""

    html = _TEMPLATE.replace("<!-- __GROUPS__ -->", groups_html)

    out = Path(output_path)
    out.write_text(html, encoding="utf-8")
    print(f"✅ index.html 생성 완료 → {out.resolve()}")
    return html


_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>청담 - 영어 지문 해설</title>
<style>
  :root {
    --bg: #f8f7f4;
    --card: #ffffff;
    --accent: #2563eb;
    --accent-light: #dbeafe;
    --text: #1e293b;
    --text-sub: #64748b;
    --border: #e2e8f0;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Noto Sans KR", sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100dvh;
    padding: 2rem 1rem;
  }

  .container {
    max-width: 640px;
    margin: 0 auto;
  }

  h1 {
    font-size: 1.8rem;
    margin-bottom: 0.5rem;
  }

  .subtitle {
    color: var(--text-sub);
    margin-bottom: 2rem;
    font-size: 0.95rem;
  }

  .exam-group {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .exam-group h2 {
    font-size: 1.15rem;
    margin-bottom: 1rem;
    color: var(--accent);
  }

  .page-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .page-list a {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 3rem;
    padding: 0.5rem 0.9rem;
    background: var(--accent-light);
    color: var(--accent);
    text-decoration: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.95rem;
    transition: background 0.15s, color 0.15s;
  }

  .page-list a:hover {
    background: var(--accent);
    color: #fff;
  }
</style>
</head>
<body>
<div class="container">
  <h1>청담 영어</h1>
  <p class="subtitle">문장별 해설 뷰어</p>
<!-- __GROUPS__ -->
</div>
</body>
</html>
"""

if __name__ == "__main__":
    generate_index()

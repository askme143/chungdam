"""
generate_index.py
─────────────────
프로젝트 루트의 디렉토리 구조를 스캔하여 index.html을 자동 생성한다.

사용법:
    python generate_index.py
"""

import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).parent

# 디렉토리 이름 → 표시 이름 변환
# 예: "고3_2025_3월_모고" → "고3 2025년 3월 모의고사"
_TYPE_MAP = {"모고": "모의고사", "수능": "수능"}


def _display_name(dirname: str) -> str:
    """디렉토리 이름을 사람이 읽기 좋은 형태로 변환한다."""
    # 모의고사/수능: "고3_2025_3월_모고" → "고3 2025년 3월 모의고사"
    m = re.match(r"(.+?)_(\d{4})_(\d{1,2})월_(.+)", dirname)
    if m:
        grade, year, month, exam_type = m.groups()
        exam_label = _TYPE_MAP.get(exam_type, exam_type)
        return f"{grade} {year}년 {month}월 {exam_label}"
    # 수특: "수특_2027_1강" → "수능특강 2027 1강"
    m = re.match(r"수특_(\d{4})_(\d{1,2})강", dirname)
    if m:
        return f"수능특강 {m.group(1)} {m.group(2)}강"
    return dirname


def _series_key(dirname: str) -> str | None:
    """시리즈에 속하는 디렉토리이면 시리즈 키를 반환, 아니면 None."""
    m = re.match(r"(수특_\d{4})_\d{1,2}강", dirname)
    if m:
        return m.group(1)
    return None


def _series_display(series_key: str) -> str:
    """시리즈 키를 표시 이름으로 변환."""
    m = re.match(r"수특_(\d{4})", series_key)
    if m:
        return f"수능특강 {m.group(1)}"
    return series_key


def _sub_label(dirname: str) -> str:
    """시리즈 내 개별 항목의 짧은 라벨 (예: '1강')."""
    m = re.match(r"수특_\d{4}_(\d{1,2})강", dirname)
    if m:
        return f"{m.group(1)}강"
    return dirname


def _sort_key(dirname: str):
    """연도·월(또는 강) 기준 내림차순 정렬 키."""
    m = re.match(r".+?_(\d{4})_(\d{1,2})월_", dirname)
    if m:
        return (1, -int(m.group(1)), -int(m.group(2)))
    m = re.match(r"수특_(\d{4})_(\d{1,2})강", dirname)
    if m:
        return (0, -int(m.group(1)), int(m.group(2)))
    return (2, 0, 0)


def _build_links(exam_dir: Path) -> str:
    """페이지 디렉토리에서 링크 HTML을 생성한다."""
    page_dir = exam_dir / "페이지"
    analysis_dir = exam_dir / "분석페이지"
    has_analysis = analysis_dir.is_dir()

    html_files = sorted(
        page_dir.glob("*.html"),
        key=lambda f: (f.stem.isdigit(), int(f.stem) if f.stem.isdigit() else 0, f.stem),
    )
    if not html_files:
        return ""

    links = []
    for f in html_files:
        label = f"{f.stem}번" if f.stem.isdigit() else f.stem
        link = f'<a href="{exam_dir.name}/페이지/{f.name}">{label}</a>'
        if has_analysis and (analysis_dir / f.name).exists():
            link += f'<a href="{exam_dir.name}/분석페이지/{f.name}" class="analysis-badge">분석</a>'
        links.append(link)

    return "\n        ".join(links)


def generate_index(output_path: Path | None = None) -> str:
    output_path = output_path or ROOT / "index.html"

    # 시험 디렉토리 탐색: 하위에 "페이지" 폴더가 있는 디렉토리
    exam_dirs = sorted(
        [d for d in ROOT.iterdir() if d.is_dir() and (d / "페이지").is_dir()],
        key=lambda d: _sort_key(d.name),
    )

    # 시리즈 그룹과 개별 항목을 순서대로 모은다
    # OrderedDict로 시리즈 등장 순서 유지
    entries: list[tuple[str, str | Path]] = []  # (type, data)
    series_map: OrderedDict[str, list[Path]] = OrderedDict()

    for exam_dir in exam_dirs:
        sk = _series_key(exam_dir.name)
        if sk:
            if sk not in series_map:
                series_map[sk] = []
                entries.append(("series", sk))
            series_map[sk].append(exam_dir)
        else:
            entries.append(("single", exam_dir))

    groups_html = ""
    for entry_type, data in entries:
        if entry_type == "series":
            series_key = data
            members = series_map[series_key]
            series_name = _series_display(series_key)
            count = len(members)

            inner_html = ""
            for exam_dir in members:
                links = _build_links(exam_dir)
                label = _sub_label(exam_dir.name)
                if links:
                    inner_html += f"""
      <div class="series-item">
        <h3>{label}</h3>
        <div class="page-list">
          {links}
        </div>
      </div>"""
                else:
                    inner_html += f"""
      <div class="series-item">
        <h3>{label}</h3>
        <p style="color: var(--text-sub); font-size: 0.9rem;">준비 중...</p>
      </div>"""

            groups_html += f"""
  <div class="exam-group series-group">
    <details>
      <summary><h2>{series_name} <span class="series-count">{count}개 강</span></h2></summary>
      <div class="series-content">{inner_html}
      </div>
    </details>
  </div>
"""
        else:
            exam_dir = data
            links = _build_links(exam_dir)
            display = _display_name(exam_dir.name)

            if links:
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

  .page-list a.analysis-badge {
    min-width: auto;
    padding: 0.3rem 0.5rem;
    font-size: 0.75rem;
    background: #f3e8ff;
    color: #7c3aed;
    margin-left: -0.3rem;
    border-radius: 0 8px 8px 0;
  }
  .page-list a.analysis-badge:hover {
    background: #7c3aed;
    color: #fff;
  }

  /* 시리즈 접기/펼치기 */
  .series-group details {
    width: 100%;
  }

  .series-group summary {
    list-style: none;
    cursor: pointer;
    display: flex;
    align-items: center;
  }

  .series-group summary::-webkit-details-marker { display: none; }

  .series-group summary h2 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0;
  }

  .series-group summary h2::before {
    content: "▶";
    font-size: 0.7rem;
    transition: transform 0.2s;
    color: var(--text-sub);
  }

  .series-group details[open] summary h2::before {
    transform: rotate(90deg);
  }

  .series-count {
    font-size: 0.8rem;
    font-weight: 400;
    color: var(--text-sub);
  }

  .series-content {
    margin-top: 1rem;
  }

  .series-item {
    padding: 0.8rem 0;
    border-top: 1px solid var(--border);
  }

  .series-item h3 {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.5rem;
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

"""
generate_analysis_viewer.py
───────────────────────────
분석 JSON 데이터를 받아 본문분석 HTML 뷰어를 생성하는 모듈.

사용법:
    from generate_analysis_viewer import generate_analysis_html

    # 1) dict로 직접 전달
    generate_analysis_html(data_dict, "output.html")

    # 2) JSON 파일 경로로 전달
    generate_analysis_html("분석/Gateway.json", "output.html")

    # 3) HTML 문자열만 반환
    html_string = generate_analysis_html(data_dict)
"""

import json
from pathlib import Path
from typing import Union


def generate_analysis_html(
    data: Union[str, Path, dict],
    output_path: Union[str, Path, None] = None,
    viewer_page: Union[str, None] = None,
) -> str:
    """분석 JSON 데이터를 받아 본문분석 HTML 뷰어를 생성한다.

    Args:
        data: JSON 파일 경로(str/Path) 또는 이미 파싱된 dict.
        output_path: 저장할 HTML 파일 경로. None이면 저장하지 않고 문자열만 반환.
        viewer_page: 문장별 해설 뷰어 링크 (상대 경로).

    Returns:
        생성된 HTML 문자열.
    """
    json_path = None
    if isinstance(data, (str, Path)):
        json_path = Path(data)
        if json_path.suffix == ".json" and json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise FileNotFoundError(f"JSON 파일을 찾을 수 없습니다: {json_path}")

    if not isinstance(data, dict) or "sentences" not in data:
        raise ValueError("data에 'sentences' 키가 필요합니다.")

    # exam_info 자동 추출
    if "exam_info" not in data and json_path is not None:
        exam_dir_name = json_path.parent.parent.name
        data["exam_info"] = exam_dir_name.replace("_", " ")

    json_literal = json.dumps(data, ensure_ascii=False)

    html = _TEMPLATE.replace("/* __DATA_PLACEHOLDER__ */{}", json_literal)
    viewer_literal = json.dumps(viewer_page, ensure_ascii=False) if viewer_page else "null"
    html = html.replace("/* __VIEWER_PAGE_PLACEHOLDER__ */null", viewer_literal)

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print(f"✅ 분석 HTML 생성 완료 → {out.resolve()}")

    return html


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HTML 템플릿
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>본문분석</title>
<style>
  :root {
    --bg: #f8f7f4;
    --card: #ffffff;
    --accent: #2563eb;
    --accent-light: #dbeafe;
    --text: #1e293b;
    --text-sub: #64748b;
    --border: #e2e8f0;
    --red: #dc2626;
    --red-light: #fef2f2;
    --yellow: #eab308;
    --yellow-light: #fefce8;
    --green: #16a34a;
    --green-light: #f0fdf4;
    --blue: #2563eb;
    --blue-light: #dbeafe;
    --orange: #ea580c;
    --purple: #7c3aed;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Noto Sans KR", sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100dvh;
    line-height: 1.7;
  }

  /* ── Header ── */
  header {
    position: sticky;
    top: 0;
    z-index: 50;
    text-align: center;
    padding: 1rem;
    border-bottom: 1px solid var(--border);
    background: var(--card);
  }
  .header-top {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }
  .home-btn, .viewer-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.4rem 0.8rem;
    background: var(--accent-light);
    color: var(--accent);
    text-decoration: none;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 600;
    transition: background 0.15s, color 0.15s;
    border: none;
    cursor: pointer;
    font-family: inherit;
  }
  .home-btn { position: absolute; left: 1rem; }
  .viewer-btn { position: absolute; right: 1rem; }
  .home-btn:hover, .viewer-btn:hover {
    background: var(--accent);
    color: #fff;
  }
  header h1 {
    font-size: 1.05rem;
    font-weight: 700;
    word-break: keep-all;
  }
  .header-sub {
    font-size: 0.78rem;
    color: var(--text-sub);
    margin-top: 0.2rem;
  }

  /* ── Main ── */
  main {
    max-width: 720px;
    width: 100%;
    margin: 0 auto;
    padding: 1.5rem 1rem 3rem;
  }

  /* ── Section Titles ── */
  .section-title {
    font-size: 1.3rem;
    font-weight: 800;
    margin: 2.5rem 0 0.3rem;
    display: flex;
    align-items: baseline;
    gap: 0.6rem;
  }
  .section-title:first-child { margin-top: 0; }
  .section-title .sub {
    font-size: 0.78rem;
    font-weight: 400;
    color: var(--text-sub);
  }

  /* ── Section 1: 지문 구조 ── */
  .structure-timeline {
    position: relative;
    padding-left: 2rem;
    margin: 1rem 0;
  }
  .structure-timeline::before {
    content: '';
    position: absolute;
    left: 0.55rem;
    top: 0.6rem;
    bottom: 0.6rem;
    width: 2px;
    border-left: 2px dashed var(--border);
  }
  .structure-item {
    position: relative;
    padding: 0.8rem 0 0.8rem 0;
    border-bottom: 1px solid var(--border);
  }
  .structure-item:last-child { border-bottom: none; }
  .structure-dot {
    position: absolute;
    left: -1.65rem;
    top: 1rem;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--accent);
    border: 2px solid var(--card);
    box-shadow: 0 0 0 2px var(--accent);
  }
  .structure-label {
    font-weight: 700;
    font-size: 0.9rem;
    margin-bottom: 0.3rem;
  }
  .structure-en {
    font-size: 0.95rem;
    line-height: 1.6;
  }
  .structure-ko {
    font-size: 0.85rem;
    color: var(--text-sub);
    margin-top: 0.15rem;
  }

  /* ── Section 2: 제목, 주제, 요약 ── */
  .meta-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem;
    margin: 1rem 0;
  }
  .meta-row {
    display: flex;
    gap: 0.8rem;
    padding: 0.7rem 0;
    border-bottom: 1px solid var(--border);
    align-items: flex-start;
  }
  .meta-row:last-child { border-bottom: none; }
  .meta-label {
    flex-shrink: 0;
    display: inline-block;
    padding: 0.2rem 0.6rem;
    background: var(--accent);
    color: #fff;
    border-radius: 4px;
    font-size: 0.78rem;
    font-weight: 700;
    min-width: 3rem;
    text-align: center;
  }
  .meta-content { flex: 1; }
  .meta-en {
    font-size: 0.95rem;
    line-height: 1.6;
  }
  .meta-ko {
    font-size: 0.85rem;
    color: var(--text-sub);
    margin-top: 0.15rem;
  }

  /* ── Section 3: 핵심 단어 ── */
  .vocab-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    background: var(--card);
    margin: 1rem 0;
  }
  @media (max-width: 540px) {
    .vocab-grid { grid-template-columns: 1fr; }
  }
  .vocab-cell {
    padding: 0.8rem 1rem;
    border-bottom: 1px solid var(--border);
    border-right: 1px solid var(--border);
    display: flex;
    gap: 0.6rem;
    align-items: flex-start;
  }
  .vocab-cell:nth-child(2n) { border-right: none; }
  @media (max-width: 540px) {
    .vocab-cell { border-right: none; }
  }
  .vocab-cell:nth-last-child(-n+2) { border-bottom: none; }
  @media (max-width: 540px) {
    .vocab-cell:nth-last-child(-n+2) { border-bottom: 1px solid var(--border); }
    .vocab-cell:last-child { border-bottom: none; }
  }
  .vocab-cb {
    margin-top: 0.25rem;
    width: 16px;
    height: 16px;
    accent-color: var(--accent);
    cursor: pointer;
    flex-shrink: 0;
  }
  .vocab-info { flex: 1; }
  .vocab-word {
    font-weight: 700;
    font-size: 0.95rem;
  }
  .vocab-word .em-mark {
    color: var(--red);
    font-size: 0.8em;
  }
  .vocab-meaning {
    font-size: 0.85rem;
    color: var(--text-sub);
  }
  .vocab-syn {
    font-size: 0.8rem;
    color: var(--green);
  }
  .vocab-ant {
    font-size: 0.8rem;
    color: var(--red);
  }

  /* ── Section 4: 지문 읽기 ── */
  .passage-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    font-size: 1.05rem;
    line-height: 2;
  }
  .sent-num {
    color: var(--accent);
    font-size: 0.75em;
    font-weight: 700;
    vertical-align: super;
    margin-right: 0.1em;
  }
  .passage-translations {
    border-top: 2px dashed var(--border);
    margin-top: 1rem;
    padding-top: 1rem;
    font-size: 0.88rem;
    color: var(--text-sub);
    line-height: 1.8;
  }
  .passage-translations .t-item {
    margin-bottom: 0.4rem;
  }
  .passage-translations .t-num {
    color: var(--accent);
    font-weight: 700;
    margin-right: 0.3rem;
  }

  /* ── Section 5: 문장별 분석 ── */
  .analysis-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1.5rem 0;
  }
  .analysis-header {
    display: flex;
    align-items: baseline;
    gap: 0.8rem;
    margin-bottom: 1rem;
  }
  .analysis-num {
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1;
  }
  .analysis-type {
    font-size: 0.8rem;
    font-weight: 600;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    color: var(--accent);
    background: var(--accent-light);
  }

  /* Phrase rendering */
  .phrase-area {
    font-size: 1.05rem;
    line-height: 3;
    margin-bottom: 1rem;
    word-break: keep-all;
    overflow-wrap: break-word;
  }
  .phrase-unit {
    display: inline;
    position: relative;
  }
  .phrase-text {
    display: inline;
  }
  .phrase-bracket {
    font-size: 1.15em;
  }
  .phrase-bracket.depth-0 { color: var(--accent); }
  .phrase-bracket.depth-1 { color: var(--orange); }
  .phrase-bracket.depth-2 { color: var(--green); }
  .phrase-bracket.depth-3 { color: var(--purple); }
  .phrase-slash {
    color: var(--accent);
    font-weight: 700;
    margin: 0 0.2em;
  }
  .phrase-bold { font-weight: 700; }
  .phrase-underline {
    text-decoration: underline;
    text-decoration-color: var(--text);
    text-underline-offset: 3px;
  }
  .phrase-boxed {
    border: 1.5px solid var(--red);
    padding: 0 0.2em;
    border-radius: 3px;
  }
  .grammar-label {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    top: 100%;
    font-size: 0.68rem;
    color: var(--red);
    font-weight: 600;
    line-height: 1.2;
    text-align: center;
    white-space: nowrap;
    pointer-events: none;
  }
  .annot-above {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    bottom: 100%;
    font-size: 0.68rem;
    color: var(--red);
    font-weight: 400;
    line-height: 1.2;
    text-align: center;
    white-space: nowrap;
    pointer-events: none;
  }
  .annot-below {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    top: calc(100% + 0.55em);
    font-size: 0.68rem;
    color: var(--red);
    font-weight: 400;
    line-height: 1.2;
    text-align: center;
    white-space: nowrap;
    pointer-events: none;
  }

  /* Korean translation */
  .analysis-korean {
    font-size: 0.92rem;
    color: var(--text-sub);
    margin-bottom: 1rem;
    line-height: 1.7;
  }

  /* 포인트! */
  .point-box {
    background: var(--yellow-light);
    border: 1px solid var(--yellow);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 1rem;
  }
  .point-title {
    font-weight: 700;
    font-size: 0.85rem;
    color: #92400e;
    margin-bottom: 0.3rem;
  }
  .point-item {
    font-size: 0.85rem;
    line-height: 1.6;
    color: #78350f;
  }
  .point-item::before {
    content: '• ';
  }

  /* 패러프레이징 */
  .paraphrase-box {
    border-top: 2px dashed var(--border);
    padding-top: 0.8rem;
  }
  .paraphrase-label {
    font-weight: 800;
    font-size: 0.85rem;
    margin-bottom: 0.3rem;
    color: var(--text);
    text-decoration: underline;
    text-underline-offset: 3px;
  }
  .paraphrase-en {
    font-size: 0.92rem;
    line-height: 1.6;
  }
  .paraphrase-ko {
    font-size: 0.85rem;
    color: var(--text-sub);
    margin-top: 0.15rem;
  }

  /* ── Toast ── */
  .toast-msg {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%) translateY(10px);
    background: rgba(0,0,0,.8);
    color: #fff;
    padding: .6rem 1.2rem;
    border-radius: 8px;
    font-size: .85rem;
    opacity: 0;
    transition: opacity .3s, transform .3s;
    z-index: 200;
    pointer-events: none;
  }
  .toast-msg.show { opacity: 1; transform: translateX(-50%) translateY(0); }

  /* ── Nav anchors ── */
  .nav-toc {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin: 1rem 0 1.5rem;
  }
  .nav-toc-title {
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--text-sub);
    margin-bottom: 0.5rem;
  }
  .nav-toc a {
    display: inline-block;
    padding: 0.3rem 0.7rem;
    margin: 0.15rem;
    background: var(--accent-light);
    color: var(--accent);
    text-decoration: none;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    transition: background 0.15s;
  }
  .nav-toc a:hover {
    background: var(--accent);
    color: #fff;
  }
</style>
</head>
<body>

<header>
  <div class="header-top">
    <a class="home-btn" href="/chungdam/">&#x1F3E0; 홈</a>
    <div>
      <h1 id="pageTitle">본문분석</h1>
      <div class="header-sub" id="examInfo"></div>
    </div>
    <a class="viewer-btn" id="viewerLink" style="display:none">문장별 해설 &#x203A;</a>
  </div>
</header>

<main id="content">
</main>

<script>
const DATA = /* __DATA_PLACEHOLDER__ */{};
const VIEWER_PAGE = /* __VIEWER_PAGE_PLACEHOLDER__ */null;

function esc(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Init ──
(function init() {
  // Title
  const prefix = DATA.problem_number ? DATA.problem_number + '번 · ' : '';
  const titleText = prefix + (DATA.title_ko || DATA.title_en || '본문분석');
  document.getElementById('pageTitle').textContent = titleText;
  document.title = '본문분석 · ' + titleText;

  if (DATA.exam_info) {
    document.getElementById('examInfo').textContent = DATA.exam_info;
  }

  // Viewer link
  if (VIEWER_PAGE) {
    const vl = document.getElementById('viewerLink');
    vl.href = VIEWER_PAGE;
    vl.style.display = '';
  }

  // Build page
  const main = document.getElementById('content');
  let html = '';

  // TOC
  html += `<div class="nav-toc">
    <div class="nav-toc-title">바로가기</div>
    <a href="#sec-structure">지문 구조</a>
    <a href="#sec-meta">제목, 주제, 요약</a>
    <a href="#sec-vocab">핵심 단어</a>
    <a href="#sec-passage">지문 읽기</a>
    <a href="#sec-analysis">문장별 분석</a>
  </div>`;

  // ── Section 1: 지문 구조 ──
  html += `<div class="section-title" id="sec-structure">지문 구조 <span class="sub">지문의 전체적인 흐름을 확인해 보세요.</span></div>`;
  html += `<div class="structure-timeline">`;
  for (const s of DATA.structure) {
    html += `<div class="structure-item">
      <div class="structure-dot"></div>
      <div class="structure-label">${esc(s.label)}</div>
      <div class="structure-en">${esc(s.english)}</div>
      <div class="structure-ko">${esc(s.korean)}</div>
    </div>`;
  }
  html += `</div>`;

  // ── Section 2: 제목, 주제, 요약 ──
  html += `<div class="section-title" id="sec-meta">제목, 주제, 요약 <span class="sub">지문의 핵심 내용을 확인해 보세요.</span></div>`;
  html += `<div class="meta-card">`;
  const metaItems = [
    { label: '제목', en: DATA.title_en, ko: DATA.title_ko },
    { label: '주제', en: DATA.theme_en, ko: DATA.theme_ko },
    { label: '요약', en: DATA.summary_en, ko: DATA.summary_ko },
  ];
  for (const m of metaItems) {
    html += `<div class="meta-row">
      <span class="meta-label">${esc(m.label)}</span>
      <div class="meta-content">
        <div class="meta-en">${esc(m.en)}</div>
        <div class="meta-ko">${esc(m.ko)}</div>
      </div>
    </div>`;
  }
  html += `</div>`;

  // ── Section 3: 핵심 단어 ──
  html += `<div class="section-title" id="sec-vocab">핵심 단어 <span class="sub">시험에 자주 출제되는 단어를 학습해 보세요.</span></div>`;
  html += `<div class="vocab-grid">`;
  const storageKey = (DATA.exam_info || '') + '_' + (DATA.problem_number || '') + '_vocab_';
  for (let i = 0; i < DATA.key_vocabulary.length; i++) {
    const v = DATA.key_vocabulary[i];
    const cbId = 'vcb' + i;
    const checked = localStorage.getItem(storageKey + v.word) === '1' ? 'checked' : '';
    let wordHtml = esc(v.word);
    if (v.emphasized) wordHtml += '<span class="em-mark">*</span>';

    let extraHtml = '';
    if (v.meaning) extraHtml += `<div class="vocab-meaning">\u24D8 ${esc(v.meaning)}</div>`;
    if (v.synonyms && v.synonyms.length) extraHtml += `<div class="vocab-syn">\u224D ${esc(v.synonyms.join(', '))}</div>`;
    if (v.antonyms && v.antonyms.length) extraHtml += `<div class="vocab-ant">\u2260 ${esc(v.antonyms.join(', '))}</div>`;

    html += `<div class="vocab-cell">
      <input type="checkbox" class="vocab-cb" id="${cbId}" data-word="${esc(v.word)}" ${checked}>
      <div class="vocab-info">
        <div class="vocab-word">${wordHtml}</div>
        ${extraHtml}
      </div>
    </div>`;
  }
  html += `</div>`;

  // ── Section 4: 지문 읽기 ──
  html += `<div class="section-title" id="sec-passage">지문 읽기 <span class="sub">지문 전체를 꼼꼼히 읽어보며 출제될 만한 부분에 표시해 보세요.</span></div>`;
  html += `<div class="passage-card">`;
  // Reconstruct passage from sentences
  let passageText = '';
  for (const s of DATA.sentences) {
    passageText += `<span class="sent-num">${String(s.id).padStart(2, '0')}</span> `;
    passageText += extractText(s.phrases) + ' ';
  }
  html += passageText;
  // Translations
  html += `<div class="passage-translations">`;
  for (const s of DATA.sentences) {
    html += `<div class="t-item"><span class="t-num">${String(s.id).padStart(2, '0')}</span>${esc(s.korean)}</div>`;
  }
  html += `</div></div>`;

  // ── Section 5: 문장별 분석 ──
  html += `<div class="section-title" id="sec-analysis">문장별 분석 <span class="sub">문장별로 분석된 빈출 포인트를 확인해 보세요.</span></div>`;
  for (const s of DATA.sentences) {
    const numStr = String(s.id).padStart(2, '0');
    html += `<div class="analysis-card">`;
    html += `<div class="analysis-header">
      <span class="analysis-num">${numStr}</span>
      <span class="analysis-type">${esc(s.type_label)}</span>
    </div>`;

    // Phrase analysis
    html += `<div class="phrase-area">`;
    let phraseHtml = '';
    for (const p of s.phrases) {
      phraseHtml += renderPhrase(p);
    }
    // Remove spaces between consecutive closing parens: ") )" → "))"
    phraseHtml = phraseHtml.replace(/<\/span>\s+<span class="phrase-bracket close-paren">\)/g,
      '</span><span class="phrase-bracket close-paren">)');
    html += phraseHtml;
    html += `</div>`;

    // Korean
    html += `<div class="analysis-korean">${esc(s.korean)}</div>`;

    // Points
    if (s.points && s.points.length > 0) {
      html += `<div class="point-box">`;
      html += `<div class="point-title">포인트!</div>`;
      for (const pt of s.points) {
        html += `<div class="point-item">${esc(pt)}</div>`;
      }
      html += `</div>`;
    }

    // Paraphrase
    if (s.paraphrase_en || s.paraphrase_ko) {
      html += `<div class="paraphrase-box">`;
      html += `<div class="paraphrase-label">패러프레이징</div>`;
      if (s.paraphrase_en) html += `<div class="paraphrase-en">${esc(s.paraphrase_en)}</div>`;
      if (s.paraphrase_ko) html += `<div class="paraphrase-ko">${esc(s.paraphrase_ko)}</div>`;
      html += `</div>`;
    }

    html += `</div>`; // analysis-card
  }

  main.innerHTML = html;

  // ── Vocab checkbox persistence ──
  document.querySelectorAll('.vocab-cb').forEach(cb => {
    cb.addEventListener('change', function() {
      const word = this.dataset.word;
      if (this.checked) {
        localStorage.setItem(storageKey + word, '1');
      } else {
        localStorage.removeItem(storageKey + word);
      }
    });
  });
})();

// ── Extract plain text from phrase tree ──
function extractText(phrases) {
  if (!phrases) return '';
  let result = '';
  for (const p of phrases) {
    if (p.children && p.children.length > 0) {
      result += extractText(p.children);
    } else if (p.type === 'slash') {
      // skip slash separators in plain text view
    } else {
      result += p.text;
      if (p.text && !p.text.endsWith(' ')) result += ' ';
    }
  }
  return result;
}

// ── Render phrase tree to HTML ──
function renderPhrase(p, depth) {
  depth = depth || 0;

  // Slash
  if (p.type === 'slash') {
    return '<span class="phrase-slash">/</span>';
  }

  // Bracket with children
  if (p.type === 'bracket' && p.children && p.children.length > 0) {
    let inner = '';
    for (const c of p.children) {
      inner += renderPhrase(c, depth + 1);
    }
    const dc = 'depth-' + Math.min(depth, 3);
    return '<span class="phrase-bracket ' + dc + '">(</span>' + inner.trimEnd() + '<span class="phrase-bracket close-paren ' + dc + '">)</span> ';
  }

  // Node with children (non-bracket)
  if (p.children && p.children.length > 0) {
    let inner = '';
    for (const c of p.children) {
      inner += renderPhrase(c, depth);
    }
    return inner;
  }

  // Leaf node
  let aboveHtml = '';
  if (p.annotation_above) {
    aboveHtml = '<span class="annot-above">' + esc(p.annotation_above) + '</span>';
  }

  let textHtml = esc(p.text);
  if (p.type === 'bold') textHtml = '<strong class="phrase-bold">' + textHtml + '</strong>';
  else if (p.type === 'underline') textHtml = '<span class="phrase-underline">' + textHtml + '</span>';
  else if (p.type === 'boxed') textHtml = '<span class="phrase-boxed">' + textHtml + '</span>';

  let labelHtml = '';
  if (p.label) {
    labelHtml = '<span class="grammar-label">' + esc(p.label) + '</span>';
  }

  let belowHtml = '';
  if (p.annotation_below) {
    belowHtml = '<span class="annot-below">' + esc(p.annotation_below) + '</span>';
  }

  // Always wrap in phrase-unit for consistent baseline alignment
  return '<span class="phrase-unit">' + aboveHtml + '<span class="phrase-text">' + textHtml + '</span>' + labelHtml + belowHtml + '</span> ';
}

function showToast(msg) {
  const t = document.createElement('div');
  t.className = 'toast-msg';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.classList.add('show'), 10);
  setTimeout(() => {
    t.classList.remove('show');
    setTimeout(() => t.remove(), 300);
  }, 2500);
}
</script>
</body>
</html>"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI 실행 지원
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="분석 JSON → 본문분석 HTML 뷰어 생성기")
    parser.add_argument("input", help="입력 JSON 파일 경로")
    parser.add_argument(
        "-o",
        "--output",
        default="analysis_viewer.html",
        help="출력 HTML 파일 경로 (기본: analysis_viewer.html)",
    )
    parser.add_argument(
        "--viewer-page",
        default=None,
        help="문장별 해설 뷰어 링크 (상대 경로)",
    )
    args = parser.parse_args()

    generate_analysis_html(args.input, args.output, viewer_page=args.viewer_page)

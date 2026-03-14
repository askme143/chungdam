"""
generate_viewer.py
──────────────────
JSON 대본 데이터를 받아 문장별 해설 HTML 뷰어를 생성하는 모듈.

사용법:
    from generate_viewer import generate_html

    # 1) dict로 직접 전달
    generate_html(data_dict, "output.html")

    # 2) JSON 파일 경로로 전달
    generate_html("motivated_reasoning_data.json", "output.html")

    # 3) HTML 문자열만 반환
    html_string = generate_html(data_dict)
"""

import json
from pathlib import Path
from typing import Union


def generate_html(
    data: Union[str, Path, dict],
    output_path: Union[str, Path, None] = None,
) -> str:
    """JSON 대본 데이터를 받아 인터랙티브 HTML 뷰어를 생성한다.

    Args:
        data: JSON 파일 경로(str/Path) 또는 이미 파싱된 dict.
        output_path: 저장할 HTML 파일 경로. None이면 저장하지 않고 문자열만 반환.

    Returns:
        생성된 HTML 문자열.
    """
    # ── 데이터 로드 ──
    if isinstance(data, (str, Path)):
        path = Path(data)
        if path.suffix == ".json" and path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise FileNotFoundError(f"JSON 파일을 찾을 수 없습니다: {path}")

    if not isinstance(data, dict) or "sentences" not in data:
        raise ValueError("data에 'sentences' 키가 필요합니다.")

    # ── JSON을 JS 리터럴로 직렬화 ──
    json_literal = json.dumps(data, ensure_ascii=False)

    # ── HTML 조립 ──
    html = _TEMPLATE.replace("/* __DATA_PLACEHOLDER__ */{}", json_literal)

    # ── 저장 ──
    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print(f"✅ HTML 생성 완료 → {out.resolve()}")

    return html


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HTML 템플릿 (DATA만 주입하면 완성되는 단일 파일)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>문장별 해설 뷰어</title>
<style>
  :root {
    --bg: #f8f7f4;
    --card: #ffffff;
    --accent: #2563eb;
    --accent-light: #dbeafe;
    --highlight: #fef08a;
    --highlight-border: #eab308;
    --text: #1e293b;
    --text-sub: #64748b;
    --border: #e2e8f0;
    --vocab-bg: #f1f5f9;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Noto Sans KR", sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
  }

  /* ── Header ── */
  header {
    position: relative;
    text-align: center;
    padding: 1.5rem 1rem 1rem;
    border-bottom: 1px solid var(--border);
    background: var(--card);
  }
  .home-btn {
    position: absolute;
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.4rem 0.8rem;
    background: var(--accent-light);
    color: var(--accent);
    text-decoration: none;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    transition: background 0.15s, color 0.15s;
  }
  .home-btn:hover {
    background: var(--accent);
    color: #fff;
  }
  header h1 {
    font-size: 1.1rem;
    font-weight: 700;
    word-break: keep-all;
  }
  .progress-row {
    margin-top: .6rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: .5rem;
    font-size: .85rem;
    color: var(--text-sub);
  }
  .progress-bar {
    width: 120px; height: 5px;
    background: var(--border);
    border-radius: 3px;
    overflow: hidden;
  }
  .progress-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 3px;
    transition: width .3s;
  }

  /* ── Main ── */
  main {
    flex: 1;
    overflow-y: auto;
    padding: 1.25rem 1rem 7rem;
    max-width: 640px;
    width: 100%;
    margin: 0 auto;
  }

  .section-label {
    font-size: .75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .05em;
    color: var(--accent);
    margin-bottom: .5rem;
  }

  /* Original sentence */
  .original-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    font-size: 1.08rem;
    line-height: 1.75;
    margin-bottom: 1.25rem;
    word-break: keep-all;
  }
  .original-card .hw {
    background: var(--highlight);
    border-bottom: 2px solid var(--highlight-border);
    border-radius: 3px;
    padding: 0 3px;
    cursor: default;
  }

  /* Explanation */
  .explain-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    font-size: .97rem;
    line-height: 1.8;
    margin-bottom: 1.25rem;
    color: var(--text);
  }

  /* Vocabulary */
  .vocab-list {
    display: flex;
    flex-direction: column;
    gap: .6rem;
  }
  .vocab-item {
    background: var(--vocab-bg);
    border-radius: 10px;
    padding: 1rem 1.1rem;
  }
  .vocab-word {
    font-weight: 700;
    font-size: 1rem;
    color: var(--accent);
  }
  .vocab-meaning {
    margin-top: .25rem;
    font-size: .93rem;
  }
  .vocab-note {
    margin-top: .2rem;
    font-size: .82rem;
    color: var(--text-sub);
  }

  /* ── Bottom Nav ── */
  .bottom-nav {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: var(--card);
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: .75rem 1rem;
    padding-bottom: max(.75rem, env(safe-area-inset-bottom));
    z-index: 10;
  }
  .nav-btn {
    display: flex;
    align-items: center;
    gap: .35rem;
    background: none;
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: .6rem 1.1rem;
    font-size: .95rem;
    font-weight: 600;
    color: var(--text);
    cursor: pointer;
    transition: all .15s;
    min-width: 5.5rem;
    justify-content: center;
  }
  .nav-btn:active { transform: scale(.96); }
  .nav-btn:not(:disabled):hover {
    border-color: var(--accent);
    color: var(--accent);
  }
  .nav-btn:disabled { opacity: .3; cursor: default; }
  .nav-indicator {
    font-size: .85rem;
    font-weight: 600;
    color: var(--text-sub);
    min-width: 3rem;
    text-align: center;
  }

  /* Animation */
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  main > * { animation: fadeIn .3s ease; }
</style>
</head>
<body>

<header>
  <a class="home-btn" href="../../">&#8592; 홈</a>
  <h1 id="pageTitle">문장별 해설</h1>
  <div class="progress-row">
    <span id="progressLabel">1 / ?</span>
    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
  </div>
</header>

<main id="content"></main>

<nav class="bottom-nav">
  <button class="nav-btn" id="prevBtn" onclick="go(-1)">&#8249; 이전</button>
  <span class="nav-indicator" id="navIndicator">1 / ?</span>
  <button class="nav-btn" id="nextBtn" onclick="go(1)">다음 &#8250;</button>
</nav>

<script>
// ── DATA (injected by generate_html) ──
const DATA = /* __DATA_PLACEHOLDER__ */{};

// ── Levenshtein distance ──
function lev(a, b) {
  const m = a.length, n = b.length;
  const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = Math.min(
        dp[i-1][j] + 1,
        dp[i][j-1] + 1,
        dp[i-1][j-1] + (a[i-1] !== b[j-1] ? 1 : 0)
      );
  return dp[m][n];
}

// ── Tokenizer ──
function tokenize(text) {
  const re = /[A-Za-z\u2019']+(?:-[A-Za-z\u2019']+)*/g;
  const tokens = []; let m;
  while ((m = re.exec(text)) !== null)
    tokens.push({ text: m[0], start: m.index, end: m.index + m[0].length });
  return tokens;
}

function findConsecutive(text, phraseWords) {
  const tokens = tokenize(text);
  for (let i = 0; i <= tokens.length - phraseWords.length; i++) {
    let ok = true;
    for (let j = 0; j < phraseWords.length; j++)
      if (tokens[i+j].text.toLowerCase() !== phraseWords[j]) { ok = false; break; }
    if (ok) return { start: tokens[i].start, end: tokens[i + phraseWords.length - 1].end };
  }
  return null;
}

// ── Highlight logic ──
function highlightSentence(text, vocabList) {
  const ranges = [];
  const lower = text.toLowerCase();

  for (const v of vocabList) {
    const phrase = v.word.toLowerCase().replace(/\s*\(.*?\)\s*/g, '').trim();

    // 1) Exact substring
    const idx = lower.indexOf(phrase);
    if (idx !== -1) { ranges.push({ start: idx, end: idx + phrase.length }); continue; }

    // 2) Multi-word consecutive
    const pw = phrase.split(/\s+/);
    if (pw.length > 1) {
      const found = findConsecutive(text, pw);
      if (found) { ranges.push(found); continue; }
    }

    // 3) Fuzzy per token
    const tokens = tokenize(text);
    for (const w of pw) {
      let bestD = Infinity, bestT = null;
      const thresh = Math.max(2, Math.floor(w.length * 0.35));
      for (const t of tokens) {
        const d = lev(w, t.text.toLowerCase());
        if (d < bestD) { bestD = d; bestT = t; }
      }
      if (bestT && bestD <= thresh) ranges.push({ start: bestT.start, end: bestT.end });
    }
  }

  // Merge overlapping
  ranges.sort((a, b) => a.start - b.start);
  const merged = [];
  for (const r of ranges) {
    if (merged.length && r.start <= merged[merged.length-1].end)
      merged[merged.length-1].end = Math.max(merged[merged.length-1].end, r.end);
    else merged.push({ ...r });
  }

  let result = '', last = 0;
  for (const r of merged) {
    result += esc(text.slice(last, r.start));
    result += '<span class="hw">' + esc(text.slice(r.start, r.end)) + '</span>';
    last = r.end;
  }
  return result + esc(text.slice(last));
}

function esc(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Render ──
let cur = 0;
const total = DATA.sentences ? DATA.sentences.length : 0;

function render() {
  if (!total) { document.getElementById('content').innerHTML = '<p>데이터가 없습니다.</p>'; return; }
  const s = DATA.sentences[cur];
  const vocabHtml = s.vocabulary.map(v => `
    <div class="vocab-item">
      <div class="vocab-word">${esc(v.word)}</div>
      <div class="vocab-meaning">${esc(v.meaning)}</div>
      ${v.note ? `<div class="vocab-note">${esc(v.note)}</div>` : ''}
    </div>`).join('');

  document.getElementById('content').innerHTML = `
    <div class="section-label">원문</div>
    <div class="original-card">${highlightSentence(s.original, s.vocabulary)}</div>
    <div class="section-label">해설</div>
    <div class="explain-card">${esc(s.explanation)}</div>
    <div class="section-label">주요 단어</div>
    <div class="vocab-list">${vocabHtml}</div>`;

  const label = `${cur+1} / ${total}`;
  document.getElementById('progressLabel').textContent = label;
  document.getElementById('navIndicator').textContent = label;
  document.getElementById('progressFill').style.width = `${((cur+1)/total)*100}%`;
  document.getElementById('prevBtn').disabled = cur === 0;
  document.getElementById('nextBtn').disabled = cur === total - 1;
  document.getElementById('content').scrollTop = 0;
}

function go(dir) {
  const next = cur + dir;
  if (next < 0 || next >= total) return;
  cur = next; render();
}

// Keyboard
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowLeft') go(-1);
  if (e.key === 'ArrowRight') go(1);
});
// Swipe
let sx = 0;
document.addEventListener('touchstart', e => { sx = e.touches[0].clientX; });
document.addEventListener('touchend', e => {
  const d = e.changedTouches[0].clientX - sx;
  if (Math.abs(d) > 60) go(d < 0 ? 1 : -1);
});

// Init
if (DATA.title) document.getElementById('pageTitle').textContent = DATA.title;
render();
</script>
</body>
</html>"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI 실행 지원
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="JSON 대본 → HTML 뷰어 생성기")
    parser.add_argument("input", help="입력 JSON 파일 경로")
    parser.add_argument(
        "-o",
        "--output",
        default="viewer.html",
        help="출력 HTML 파일 경로 (기본: viewer.html)",
    )
    args = parser.parse_args()

    generate_html(args.input, args.output)

    # index.html 자동 갱신
    from generate_index import generate_index

    generate_index()

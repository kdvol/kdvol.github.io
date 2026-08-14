#!/usr/bin/env python3
"""내가 반응하거나 한마디를 남긴 스토리를 모아 보여준다 (/saved/).

반응 버튼(👍 🤔 🔥)은 눌러도 되돌아볼 곳이 없었다. 누른 사람 브라우저에는
기록이 남는데(localStorage.ss_react) 그걸 꺼내 보는 화면이 없어서, 사실상
누르고 잊는 버튼이었다. 서버는 합계만 갖고 개인 기록은 남기지 않는다 —
그건 그대로 두는 게 맞다. 그러니 되살릴 단서는 그 브라우저뿐이다.

  ss_react  { "0812-1": "🔥", "0805c-2": "👍" }   반응
  ss_cmt    { "0812-3": 1786500142 }              내가 한마디 남긴 곳

제목·날짜·주소는 story_atoms.json에서 붙인다. 1012건이라 56KB인데, 저장한
게 하나도 없는 사람에게까지 내려보낼 이유가 없다. 별도 JSON으로 빼고
기록이 있을 때만 가져온다 — 빈손이면 네트워크 요청이 0이다.

주의: 로그인이 없다. 브라우저를 지우거나 기기를 바꾸면 사라진다.
화면에 그렇게 밝힌다. 감추면 나중에 잃었을 때 더 나쁘다.
"""

import json
import re
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "saved"
ATOMS = ROOT / "content" / "story_atoms.json"
BASE = "https://soonsal.com"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#faf9f5;color:#1a1a1a;font-family:'Pretendard',-apple-system,BlinkMacSystemFont,
'Segoe UI',sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:720px;margin:0 auto;padding:30px 18px 80px}
h1{font-size:1.6rem;font-weight:800;letter-spacing:-.03em;margin-bottom:6px}
.sub{color:#8a857c;font-size:.9rem;margin-bottom:24px;line-height:1.7}
.bar{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:18px}
.fb{background:#fff;border:1px solid #e6e1d8;border-radius:999px;padding:7px 14px;
font-size:.84rem;font-weight:700;color:#6b665e;cursor:pointer;font-family:inherit}
.fb.on{background:#1a1a1a;border-color:#1a1a1a;color:#fff}
.fb .n{color:#a9a49b;font-weight:600;margin-left:5px}
.fb.on .n{color:#d8d3ca}
.it{display:flex;gap:13px;background:#fff;border:1px solid #ece8e0;border-radius:12px;
padding:14px 16px;margin-bottom:9px;text-decoration:none;color:inherit}
.it:hover{border-color:#d8d3ca}
.it .mk{flex:0 0 auto;width:34px;height:34px;border-radius:12px;background:#f6f4ef;
border:1px solid #ece8e0;display:flex;align-items:center;justify-content:center;font-size:1rem}
.it .bd{min-width:0;flex:1}
.it .bd>span{display:block}
.it .lb{font-size:.68rem;font-weight:800;letter-spacing:.05em;color:#b09a86;margin-bottom:3px}
.it .tt{font-size:.97rem;font-weight:700;letter-spacing:-.02em;line-height:1.45;
overflow-wrap:anywhere}
.it .dt{font-size:.78rem;color:#a9a49b;margin-top:4px}
.empty{background:#fff;border:1px dashed #ddd8ce;border-radius:12px;padding:34px 22px;
text-align:center;color:#8a857c;font-size:.92rem;line-height:1.8}
.empty b{display:block;color:#3a3632;font-size:1.02rem;margin-bottom:8px}
.empty a{color:#E55A00;font-weight:700;text-decoration:none}
.fine{margin-top:26px;padding-top:18px;border-top:1px solid #ece8e0;
color:#a9a49b;font-size:.78rem;line-height:1.8}
.fine a{color:#8a857c}
"""

JS = r"""
(function () {
  var MK = { '👍': '👍', '🤔': '🤔', '🔥': '🔥' };
  var app = document.getElementById('app'), bar = document.getElementById('bar');
  var MAP = null, MODE = 'all';

  function rd(k) { try { return JSON.parse(localStorage.getItem(k) || '{}'); } catch (e) { return {}; } }

  // id에서 주소를 되살린다. 0716c-4 → /newsletters/2026/0716-crypto.html#story-4
  function urlOf(id, date) {
    var m = /^(\d{4})(c?)-(\d+)$/.exec(id);
    if (!m) return null;
    return '/newsletters/' + date.slice(0, 4) + '/' + m[1] +
           (m[2] ? '-crypto' : '') + '.html#story-' + m[3];
  }

  function items() {
    var rc = rd('ss_react'), cm = rd('ss_cmt'), keys = {}, out = [];
    Object.keys(rc).forEach(function (k) { keys[k] = 1; });
    Object.keys(cm).forEach(function (k) { keys[k] = 1; });
    Object.keys(keys).forEach(function (k) {
      var a = MAP && MAP[k];
      if (!a) return;                       // 지난 회차가 아톰에서 빠졌으면 건너뛴다
      out.push({ k: k, t: a[0], d: a[1], l: a[2] || '',
                 e: rc[k] || '', c: !!cm[k] });
    });
    // 최신 회차부터. 같은 날이면 스토리 번호 순.
    out.sort(function (a, b) { return a.d === b.d ? (a.k < b.k ? -1 : 1) : (a.d < b.d ? 1 : -1); });
    return out;
  }

  function paint() {
    var all = items();
    var shown = all.filter(function (x) {
      if (MODE === 'all') return true;
      if (MODE === 'cmt') return x.c;
      return x.e === MODE;
    });

    var counts = { all: all.length, cmt: 0 };
    ['👍', '🤔', '🔥'].forEach(function (e) { counts[e] = 0; });
    all.forEach(function (x) { if (x.c) counts.cmt++; if (x.e) counts[x.e]++; });

    var tabs = [['all', '전체'], ['🔥', '🔥 중요함'],
                ['👍', '👍 좋았음'], ['🤔', '🤔 글쎄'],
                ['cmt', '💬 한마디']];
    bar.innerHTML = tabs.filter(function (t) { return counts[t[0]]; }).map(function (t) {
      return '<button class="fb' + (MODE === t[0] ? ' on' : '') + '" data-m="' + t[0] + '">' +
             t[1] + '<span class="n">' + counts[t[0]] + '</span></button>';
    }).join('');

    if (!all.length) {
      app.innerHTML = '<div class="empty"><b>아직 모인 게 없어요</b>' +
        '스토리 아래 👍 🤔 🔥 를 누르거나 한마디를 남기면<br>' +
        '여기 쌓입니다. <a href="/newsletters/">브리핑 보러 가기 →</a></div>';
      return;
    }
    app.innerHTML = shown.map(function (x) {
      var u = urlOf(x.k, x.d);
      var mk = x.e || '💬';
      return '<a class="it" href="' + (u || '/newsletters/') + '">' +
        '<span class="mk">' + mk + '</span><span class="bd">' +
        (x.l ? '<span class="lb">' + x.l + '</span>' : '') +
        '<span class="tt">' + x.t + '</span>' +
        '<span class="dt">' + x.d.slice(5).replace('-', '.') +
        (x.c && x.e ? ' · 💬 한마디 남김' : '') + '</span>' +
        '</span></a>';
    }).join('');
  }

  bar.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.fb');
    if (b) { MODE = b.getAttribute('data-m'); paint(); }
  });

  // 저장한 게 없으면 56KB를 받을 이유가 없다
  var rc = rd('ss_react'), cm = rd('ss_cmt');
  if (!Object.keys(rc).length && !Object.keys(cm).length) { MAP = {}; paint(); return; }
  fetch('/saved/stories.json').then(function (r) { return r.json(); })
    .then(function (j) { MAP = j; paint(); })
    .catch(function () {
      app.innerHTML = '<div class="empty"><b>목록을 불러오지 못했어요</b>' +
        '잠시 뒤 새로고침해 주세요.</div>';
    });
})();
"""


def build():
    import build_nav

    if not ATOMS.exists():
        print("  ⚠️ story_atoms.json 없음 — /saved/ 건너뜀")
        return 0
    atoms = json.loads(ATOMS.read_text(encoding="utf-8"))

    # 제목 앞 이모지는 목록에서 마커(👍🤔🔥)와 부딪힌다. /stats/와 같은 규칙으로 떼어낸다.
    smap = {}
    for a in atoms:
        i = a.get("id", "")
        if not re.match(r"^\d{4}c?-\d+$", i):
            continue
        t = re.sub(r"^[^\w<>&\"']{1,4}\s+", "", a.get("title", "")).strip()
        smap[i] = [t, a.get("date", ""), (a.get("label") or "")[:26]]

    OUT.mkdir(exist_ok=True)
    (OUT / "stories.json").write_text(
        json.dumps(smap, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    title = "내가 모은 스토리 — 순살브리핑"
    desc = "순살브리핑에서 반응을 남기거나 한마디를 쓴 스토리를 한자리에 모았습니다."
    canonical = f"{BASE}/saved/"
    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}">
<!-- 사람마다 내용이 다른 화면이라 색인 대상이 아니다 -->
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{canonical}">
{build_nav.FONT_LINK}
<style>{CSS}{build_nav.HEADER_CSS}</style></head><body>
{build_nav.header_html("/saved/")}<div class="wrap">
<h1>내가 모은 스토리</h1>
<p class="sub">반응을 남기거나 한마디를 쓴 스토리가 여기 쌓입니다.</p>
<div class="bar" id="bar"></div>
<div id="app"><div class="empty">불러오는 중…</div></div>
<p class="fine">로그인이 없어서 <b>이 브라우저에만</b> 저장됩니다.
기록을 지우거나 다른 기기로 옮기면 목록도 사라져요.
수집 항목은 <a href="/privacy/">수집 안내</a>에 정리해 뒀습니다.</p>
</div>
<script src="/soonsal.js" defer></script>
<script>{JS}</script>
</body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    kb = len((OUT / "stories.json").read_text(encoding="utf-8")) // 1024
    print(f"🔖 saved: /saved/ 내가 모은 스토리 (스토리 {len(smap)}개 · {kb}KB, 필요할 때만 받음)")
    return 1


if __name__ == "__main__":
    build()

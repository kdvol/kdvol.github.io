#!/usr/bin/env python3
"""홈 새 안 (/home-b/). 기존 index.html은 건드리지 않는다 — 나란히 비교하기 위한 판.

지금 홈의 문제는 취향이 아니라 구조다.
  · 최신호가 <iframe>이라 그 글은 /newsletters/…의 것이지 홈의 것이 아니다.
    검색·AI가 보는 홈은 '제목 없는 껍데기 + 링크 356개'다.
  · <h1>·<h2>가 하나도 없다. "이 페이지는 무엇인가"를 말해주는 태그가 없다.
  · 아카이브 336건을 한 번에 내려보내 39화면(31,671px)이 된다.

그래서 새 안은 세 가지만 다르게 한다.
  1. 최신호를 iframe이 아니라 '홈의 본문'으로 심는다(story_atoms.json에서 가져온다).
     지어내지 않는다 — 제목·라벨·첫 불렛만 쓴다.
  2. h1 하나, h2 몇 개로 문서 구조를 만든다.
  3. 아카이브는 최근 12건만. 나머지는 /newsletters/로 보낸다.

디자인은 기존 톤(어두운 배경, 주황 강조)을 그대로 따른다. 비교할 것은
디자인 취향이 아니라 구조이기 때문이다.
"""

import json
import re
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "home-b"
ATOMS = ROOT / "content" / "story_atoms.json"
TICKER = Path(__file__).resolve().parent / "_ticker.html"
BASE = "https://soonsal.com"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#111;color:#e8e3da;font-family:'Pretendard',-apple-system,BlinkMacSystemFont,
'Segoe UI',sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:720px;margin:0 auto;padding:0 18px 70px}
h1,h2{font-size:.72rem;font-weight:800;letter-spacing:.1em;color:#E55A00;
margin:46px 0 12px;text-transform:uppercase}
h1{margin-top:26px}
/* 뉴스레터 CSS가 뒤에 실려 margin이 덮인다 — padding으로 못박는다 */
.issue{color:#6f6a60;font-size:.78rem;font-weight:600;padding-left:9px;
letter-spacing:0;text-transform:none}
/* 들어오자마자 전체를 펴 놓으면 39화면이 된다. 한 화면 반쯤 보여주고
   나머지는 접는다 — 서식은 그대로 살아 있고 글도 DOM에 다 있다(검색용). */
.nlwrap{position:relative;max-height:min(44vh,420px);overflow:hidden;
border:1px solid #232323;border-radius:12px}
.nlwrap.open{max-height:none}
.nlwrap .fade{position:absolute;left:0;right:0;bottom:0;height:150px;pointer-events:none;
background:linear-gradient(180deg,rgba(255,255,255,0),#fff)}
.nlwrap.open .fade{display:none}
.expand{display:block;width:100%;margin-top:10px;padding:12px;background:#1a1a1a;
border:1px solid #2c2c2c;border-radius:9px;color:#e8e3da;font-family:inherit;
font-size:.88rem;font-weight:700;cursor:pointer}
.expand:hover{background:#222;border-color:#3a3a3a}
/* 구역 설명 한 줄. 제목만 있으면 무슨 구역인지 안 잡힌다. */
.sec{color:#7a756c;font-size:.85rem;line-height:1.7;margin:-6px 0 14px}
/* 그림만 놓지 않는다 — 무슨 얘긴지 위에 적어야 구역이 바뀐 것도 보인다 */
.chart{display:block;margin:0;text-decoration:none;border:1px solid #232323;
border-radius:12px;overflow:hidden;background:#151515}
.chart .cap{display:block;padding:14px 16px 12px;color:#e8e3da;font-size:.95rem;
font-weight:700;letter-spacing:-.02em;line-height:1.45}
.chart img{display:block;width:100%;height:auto;max-width:100%}
.chart .go{display:block;padding:12px 16px;border-top:1px solid #1e1e1e;
color:#F07040;font-size:.83rem;font-weight:700}
.chart:hover{border-color:#3a3a3a}
.chart:hover .go{color:#FF8A5B}
.more{display:inline-block;margin-top:16px;color:#F07040;font-size:.86rem;
font-weight:700;text-decoration:none}
.more:hover{text-decoration:underline}
.arch{display:grid;gap:1px;background:#1c1c1c;border:1px solid #1c1c1c;border-radius:10px;
overflow:hidden}
.arch a{display:flex;gap:12px;align-items:baseline;background:#141414;padding:12px 14px;
text-decoration:none;color:#b8b2a8;font-size:.87rem}
.arch a:hover{background:#191919;color:#fff}
.arch .d{flex:0 0 auto;color:#6f6a60;font-size:.76rem;font-variant-numeric:tabular-nums}
.arch .t{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ch{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
.ch a{background:#151515;border:1px solid #232323;border-radius:10px;padding:14px 15px;
text-decoration:none;color:#e8e3da}
.ch a:hover{border-color:#3a3a3a}
.ch b{display:block;font-size:.92rem;font-weight:700;letter-spacing:-.02em}
.ch span{display:block;color:#7a756c;font-size:.79rem;margin-top:4px;line-height:1.5}
@media(max-width:560px){.ch{grid-template-columns:1fr}}
"""


def _lead(body: str, n: int = 92) -> str:
    b = re.sub(r"<[^>]+>", "", body or "")
    parts = b.split("◾")
    s = parts[1] if len(parts) > 1 else b
    return re.sub(r"\s+", " ", s).strip()[:n]


def _clean(title: str) -> str:
    """제목은 이모지째로 쓴다.

    /stats/에서는 앞 이모지를 뗀다 — 목록 마커(👍🤔🔥)와 부딪히기 때문이다.
    홈에는 그런 마커가 없고, 이모지는 순살 제목의 일부다. 검색 때문에 뗀 게
    아니다(구조화 데이터와 h1이 검색을 맡는다).
    """
    return (title or "").strip()


CHANNELS = [
    ("https://t.me/soonsal", "순살 텔레그램",
     "발행 알림부터 짧은 생각, 가끔 투표까지"),
    ("/talk/", "순살톡", "브리핑 읽고 남긴 한 줄이 모이는 곳"),
    ("/cardnews/", "카드뉴스", "인스타에서 한 장씩 넘겨 보기"),
    ("/school/", "순살스쿨", "현직자가 여는 IBD·IPO·M&A 클래스"),
]


def _chart():
    """홈에 걸 차트 하나. 절대 빈손으로 돌아오지 않는다.

    1) /morning/ 목록의 .lead-chart — 그날의 핵심 차트로 지정된 것
    2) 없으면 최신 회차 페이지에 '실린 순서'대로 첫 번째 다이어그램
    3) 그것도 없으면 자산 폴더에서 아무거나

    2번이 필요한 이유: 파일명 알파벳순으로 집으면 그날 제일 중요한 게 아니라
    이름이 빠른 게 올라간다(ai-… 가 cpi-… 를 이긴다). 페이지에 실린 순서가
    사람이 정한 순서다.
    """
    # (1) 지정된 핵심 차트
    idx = ROOT / "morning" / "index.html"
    if idx.exists():
        s = idx.read_text(encoding="utf-8")
        m = re.search(r'<a class="lead-chart" href="([^"]+)".*?'
                      r'<span class="lead-chart-title">(.*?)</span>\s*'
                      r'<img src="([^"]+)"', s, re.S)
        if m:
            mob = m.group(3)
            wide = mob.replace("-diagram-mobile.svg", "-diagram.svg")
            if not (ROOT / wide.lstrip("/")).exists():
                wide = mob
            return {"wide": wide, "mob": mob,
                    "page": "/morning/" + m.group(1).split("#")[0],
                    "title": re.sub(r"<[^>]+>", "", m.group(2)).strip()}

    # (2) 최신 회차에서 페이지 순서대로 첫 그림
    pages = sorted(ROOT.glob("morning/2026/*.html"), reverse=True)
    for pg in pages:
        s = pg.read_text(encoding="utf-8")
        im = re.search(r'src="(/morning/assets/\d+/[a-z0-9-]+-diagram[^"]*\.svg)', s)
        if not im:
            continue
        mob = im.group(1).split("?")[0]
        slug = re.sub(r"-diagram(-mobile)?\.svg$", "", mob.rsplit("/", 1)[1])
        title = ""
        sm = re.search(rf'data-ss-story="m\d{{8}}-{re.escape(slug)}"', s)
        if sm:
            h = re.search(r"<h2[^>]*>(.*?)</h2>", s[sm.start():sm.start() + 4000], re.S)
            if h:
                title = re.sub(r"<[^>]+>", "", h.group(1)).strip()
        wide = mob.replace("-diagram-mobile.svg", "-diagram.svg")
        if not (ROOT / wide.lstrip("/")).exists():
            wide = mob
        return {"wide": wide, "mob": mob,
                "page": "/morning/" + str(pg.relative_to(ROOT / "morning")).replace("\\", "/"),
                "title": title or "오늘의 순살차트"}

    # (3) 최후 — 자산 폴더에 있는 아무 그림이라도
    for d in sorted((ROOT / "morning" / "assets").glob("2026*"), reverse=True):
        got = sorted(d.glob("*-diagram.svg"))
        if got:
            u = f"/morning/assets/{d.name}/{got[0].name}"
            return {"wide": u, "mob": None, "page": "/morning/", "title": "오늘의 순살차트"}
    return None


def _ticker() -> str:
    """상단 실시간 시황 바. index.html에서 떼어 둔 블록을 그대로 쓴다 —
    새로 만들면 같은 것이 두 벌이 되고 한쪽만 고쳐지는 날이 온다."""
    return TICKER.read_text(encoding="utf-8") if TICKER.exists() else ""


def _issue_body(page: Path):
    """뉴스레터에서 style과 .content 마크업만 떼어 온다.

    style은 body 규칙 하나만 일반 태그를 건드린다(나머지는 전부 클래스라
    홈 CSS와 안 부딪힌다). 그 한 줄만 .nl로 바꿔 담는다.
    """
    if not page.exists():
        return None
    t = page.read_text(encoding="utf-8")

    m = re.search(r"<style[^>]*>(.*?)</style>", t, re.S)
    css = m.group(1) if m else ""
    css = re.sub(r"(?m)^\s*body\s*\{", ".nl{", css)

    i = t.find('<div class="content">')
    if i < 0:
        return None
    depth, pos = 1, i + len('<div class="content">')
    end = None
    for x in re.finditer(r"</?div\b[^>]*>", t[pos:]):
        depth += -1 if x.group(0).startswith("</") else 1
        if depth == 0:
            end = pos + x.end()
            break
    if end is None:
        return None
    body = t[i:end]
    # 본문 안에 base64가 남아 있으면 홈이 무거워진다 — 실제로는 헤더에만 있다
    body = re.sub(r'src="data:image/[^"]+"', 'src=""', body)

    # 원본 뉴스레터의 div 짝이 맞지 않는 회차가 있다(여는 태그가 하나 더 많다).
    # 그대로 심으면 이 블록이 안 닫히고, 뒤에 오는 것(전체 보기 버튼·순살차트·
    # 지난 뉴스레터·채널 카드)이 전부 이 상자 안으로 빨려 들어간다.
    # 상자는 접혀 있으니(overflow:hidden) 화면에서 통째로 사라진다.
    # 그래서 여기서 짝을 맞춘다. 남는 닫는 태그는 버리고, 모자라면 채운다.
    plain = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    gap = len(re.findall(r"<div\b", plain)) - len(re.findall(r"</div>", plain))
    if gap > 0:
        body += "</div>" * gap
    elif gap < 0:
        for _ in range(-gap):
            body = body[::-1].replace(">vid/<"[::-1], "", 1)[::-1]

    chk = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    assert len(re.findall(r"<div\b", chk)) == len(re.findall(r"</div>", chk)), \
        "div 짝을 못 맞췄다 — 그대로 심으면 뒤 섹션이 삼켜진다"
    return css, body


def build(atoms=None):
    import build_nav

    if atoms is None:
        atoms = json.loads(ATOMS.read_text(encoding="utf-8")) if ATOMS.exists() else []
    if not atoms:
        print("  ⚠️ story_atoms.json 없음 — /home-b/ 건너뜀")
        return 0

    ordered = sorted(atoms, key=lambda a: (a.get("date", ""), a.get("n", 0)), reverse=True)
    latest_date = ordered[0]["date"]
    today = sorted([a for a in ordered if a["date"] == latest_date],
                   key=lambda a: a.get("n", 0))
    dt = f"{latest_date[5:7]}.{latest_date[8:10]}"

    nl = _issue_body(ROOT / today[0]["newsletter"].lstrip("/"))
    if not nl:
        print("  ⚠️ 뉴스레터 본문을 못 읽음 — /home-b/ 건너뜀")
        return 0
    nl_css, nl_body = nl

    # 아카이브는 회차 단위로 최근 12개. 336개를 다 내려보낼 이유가 없다.
    seen, arch = set(), []
    for a in ordered:
        u = a.get("newsletter")
        if not u or u in seen:
            continue
        seen.add(u)
        arch.append((a["date"], u, _clean(a["title"])))
        if len(arch) >= 12:
            break
    arch_html = "".join(
        f'<a href="{u}"><span class="d">{d[5:7]}.{d[8:10]}</span>'
        f'<span class="t">{escape(t)}</span></a>' for d, u, t in arch)

    ch = "".join(
        f'<a href="{h}"' + (' target="_blank" rel="noopener"' if h.startswith("http") else '')
        + f'><b>{escape(n)}</b><span>{escape(s)}</span></a>'
        for h, n, s in CHANNELS)

    ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"순살브리핑 {latest_date}",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "url": BASE + a["url"], "name": _clean(a["title"])}
            for i, a in enumerate(today)],
    }

    ticker = _ticker()
    c = _chart()
    chart_html = ""
    if c:
        src = c["mob"] or c["wide"]
        srcset = (f'<source media="(min-width:640px)" srcset="{c["wide"]}">'
                  if c["mob"] else "")
        cap = escape(c["title"]) if c["title"] else "무빙 차트로 한눈에 순살만 쏙쏙"
        chart_html = (
            '<h2>순살차트</h2>'
            '<p class="sec">장 열리기 전, 오늘 시장에서 볼 것만 그림으로 정리합니다.</p>'
            f'<a class="chart" href="{c["page"]}">'
            f'<span class="cap"><b>{cap}</b></span>'
            f'<picture>{srcset}<img src="{src}" alt="{cap}" loading="lazy"></picture>'
            '<span class="go">순살차트 전체 보기 →</span></a>')

    title = "순살브리핑 — 글로벌 금융·경제·크립토 뉴스레터"
    desc = ("모건스탠리 홍콩 출신 금융인의 글로벌 금융·경제·크립토 뉴스 살코기. "
            "매일 아침 5분, 월~금 발행.")
    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}">
<meta name="robots" content="noindex,nofollow">
{build_nav.FONT_LINK}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{CSS}{build_nav.HEADER_CSS}</style>
<style>{nl_css}</style></head><body>
{ticker}
{build_nav.header_html("/newsletters/")}<div class="wrap">


<h1>오늘자 뉴스레터<span class="issue">{dt}</span></h1>
<div class="nlwrap" id="nlwrap">
  <div class="nl">{nl_body}</div>
  <div class="fade"></div>
</div>
<button type="button" class="expand" id="expand">전체 보기 ↓</button>

{chart_html}

<h2>지난 뉴스레터</h2>
<div class="arch">{arch_html}</div>
<a class="more" href="/newsletters/">뉴스레터 전체 보기 →</a>

<h2>더 많은 순살 둘러보기</h2>
<div class="ch">{ch}</div>

</div>
<script>
(function () {{
  var w = document.getElementById('nlwrap'), b = document.getElementById('expand');
  if (!w || !b) return;
  b.addEventListener('click', function () {{
    var open = w.classList.toggle('open');
    b.textContent = open ? '접기 ↑' : '전체 보기 ↓';
    if (!open) w.scrollIntoView({{ block: 'start' }});
  }});
}})();
</script>
<script src="/soonsal.js" defer></script>
</body></html>"""
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"🏠 home-b: /home-b/ 홈 새 안 — {len(html)//1024}KB "
          f"(스토리 {len(today)} · 아카이브 {len(arch)})")
    return 1


if __name__ == "__main__":
    build()

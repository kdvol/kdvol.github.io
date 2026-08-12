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
BASE = "https://soonsal.com"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#111;color:#e8e3da;font-family:'Pretendard',-apple-system,BlinkMacSystemFont,
'Segoe UI',sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:720px;margin:0 auto;padding:0 18px 70px}
.lede{padding:34px 0 26px;border-bottom:1px solid #1e1e1e}
h1{font-size:1.72rem;font-weight:800;letter-spacing:-.035em;line-height:1.32;color:#fff}
.lede p{color:#8f8a80;font-size:.95rem;margin-top:11px;line-height:1.75}
.lede .cta{display:inline-block;margin-top:18px;background:#E55A00;color:#fff;
padding:11px 22px;border-radius:8px;font-size:.9rem;font-weight:700;text-decoration:none}
.lede .cta:hover{background:#CC4E00}
.lede .sub{display:block;margin-top:10px;color:#5f5b53;font-size:.78rem}
h2{font-size:.72rem;font-weight:800;letter-spacing:.1em;color:#E55A00;
margin:34px 0 14px;text-transform:uppercase}
.issue{color:#6f6a60;font-size:.78rem;font-weight:600;margin-left:8px;letter-spacing:0}
.st{display:block;padding:15px 0;border-bottom:1px solid #1c1c1c;text-decoration:none;color:inherit}
.st:first-of-type{border-top:1px solid #1c1c1c}
.st .lb{font-size:.63rem;font-weight:800;letter-spacing:.07em;color:#8a6f5c}
.st .ti{display:block;font-size:1.02rem;font-weight:700;letter-spacing:-.025em;
line-height:1.4;color:#e8e3da;margin-top:4px}
.st:hover .ti{color:#fff}
.st .ld{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
font-size:.85rem;line-height:1.6;color:#7a756c;margin-top:6px}
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
.cmp{margin:26px 0 0;padding:13px 15px;background:#17140f;border:1px solid #2e2418;
border-radius:9px;color:#8a8073;font-size:.78rem;line-height:1.7}
.cmp b{color:#F0A070}
"""


def _lead(body: str, n: int = 92) -> str:
    b = re.sub(r"<[^>]+>", "", body or "")
    parts = b.split("◾")
    s = parts[1] if len(parts) > 1 else b
    return re.sub(r"\s+", " ", s).strip()[:n]


def _clean(title: str) -> str:
    return re.sub(r"^[^\w<>&\"']{1,4}\s+", "", title or "").strip()


CHANNELS = [
    ("/morning/", "순살차트", "장 열리기 전, 오늘 시장에서 볼 것만"),
    ("/talk/", "순살톡", "브리핑을 읽다 남긴 한 줄이 모이는 곳"),
    ("/cardnews/", "카드뉴스", "인스타에서 한 장씩 넘겨 보는 판"),
    ("/school/", "순살스쿨", "현직자가 여는 IBD·IPO·M&A 클래스"),
]


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

    stories = "".join(
        f'<a class="st" href="{a["url"]}">'
        f'<span class="lb">{escape((a.get("label") or "")[:30])}</span>'
        f'<span class="ti">{escape(_clean(a["title"]))}</span>'
        f'<span class="ld">{escape(_lead(a.get("body", "")))}…</span></a>'
        for a in today)

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

    ch = "".join(f'<a href="{h}"><b>{escape(n)}</b><span>{escape(s)}</span></a>'
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
<style>{CSS}{build_nav.HEADER_CSS}</style></head><body>
{build_nav.header_html("/newsletters/")}<div class="wrap">

<div class="cmp"><b>홈 새 안 (비교용)</b> — 현재 홈은 <a href="/" style="color:#F0A070">soonsal.com</a>
그대로입니다. 검색에 잡히지 않도록 noindex 처리했습니다.</div>

<section class="lede">
<h1>매일 아침 5분,<br>글로벌 금융·경제 살코기</h1>
<p>{escape(desc)}</p>
<a class="cta" href="https://subscribe.soonsal.com/subscribe" target="_blank"
 rel="noopener">무료로 구독하기</a>
<span class="sub">월~금 아침 발행 · 언제든 해지</span>
</section>

<h2>오늘의 브리핑<span class="issue">{dt}</span></h2>
{stories}
<a class="more" href="{today[0]['newsletter']}">이 회차 전체 보기 →</a>

<h2>순살의 다른 판</h2>
<div class="ch">{ch}</div>

<h2>지난 회차</h2>
<div class="arch">{arch_html}</div>
<a class="more" href="/newsletters/">전체 아카이브 보기 →</a>

</div>
<script src="/soonsal.js" defer></script>
</body></html>"""
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"🏠 home-b: /home-b/ 홈 새 안 — {len(html)//1024}KB "
          f"(스토리 {len(today)} · 아카이브 {len(arch)})")
    return 1


if __name__ == "__main__":
    build()

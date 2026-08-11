#!/usr/bin/env python3
"""/school/ — 팔리는 구조로.

지금은 가격표만 나열돼 있다. 17만~50만원짜리를 사려는 사람이 판단할 재료가
없다 — 누가 가르치는지, 몇 시간짜리인지, 뭘 얻는지가 없다. 그래서 '수강하기'를
누르기 전에 이탈한다.

강의 정보는 liveklass 판매 페이지에서 실제로 확인해 옮겼다(지어내지 않았다).
없는 것은 넣지 않는다 — 수강생 수와 후기 문구는 공개된 값이 없어서 뺐다.
"가장 많이 팔린" 같은 표현도 쓰지 않는다. 확인할 수 없는 인기 지표를 붙이면
그 순간 페이지 전체의 신뢰가 깎인다.
평점은 표시된 강의(10659, 5.0)만 붙인다.

구조:
  1. 강사가 누구인지 먼저. 이 가격대에선 그게 첫 번째 질문이다
  2. 통합본을 앵커로 — 개별 63만 vs 통합 50만, 절감액을 숫자로
  3. 강의마다 '이런 분께' + '이걸 배웁니다' + 분량
  4. 트랙으로 묶는다. 7개를 한 줄로 늘어놓으면 고르지 못한다
"""

import html as H
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "school"
BASE = "https://soonsal.liveklass.com/classes/"

CAPTAINS = {
    "ibd": {
        "n": "IBD 캡틴",
        "b": ["전 Deutsche Bank 기업금융부(IBD) 등 글로벌 기업금융 10년+",
              "현 국내 유니콘 기업 Head of Corporate Development",
              "대규모 투자유치·전략투자 집행 총괄"],
    },
    "jack": {
        "n": "캡틴 Jack",
        "b": ["현직 홍콩 Portfolio Manager",
              "글로벌 자산운용사 바이사이드 현업",
              "연합뉴스 보도"],
    },
    "quant": {
        "n": "퀀트 캡틴",
        "b": ["홍콩 스위스계 은행 퀀트 펀드 6년 — 퀀트 리서치·트레이딩",
              "스탠포드 경제·수학 전공"],
    },
}

TRACKS = [
    ("투자은행(IBD) 트랙", "기업의 자본 조달과 인수합병을 다루는 쪽",
     ["42917", "38648", "42392", "42832"]),
    ("바이사이드·퀀트 트랙", "돈을 굴리는 쪽, 그리고 그걸 자동화하는 쪽",
     ["10659", "10965", "10662"]),
]

CSS = """
*{box-sizing:border-box}
.sc{max-width:860px;margin:0 auto;padding:0 16px 70px}
.hero{background:linear-gradient(135deg,#1c1c1c,#33302b);border-radius:20px;padding:34px 28px;
color:#f5f2ea;margin-bottom:14px}
.hero .kk{display:inline-block;background:rgba(240,112,64,.2);color:#F5A481;font-size:.72rem;
font-weight:700;border-radius:20px;padding:4px 11px;margin-bottom:13px}
.hero h1{font-size:1.72rem;font-weight:800;margin:0 0 10px;letter-spacing:-.03em;line-height:1.32}
.hero p{margin:0;color:#bdb8ad;font-size:.94rem;line-height:1.68}
.caps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:11px;margin:14px 0 30px}
.cap{background:#fff;border:1px solid #ece8de;border-radius:14px;padding:15px 16px}
.cap .nm{font-weight:800;font-size:.93rem;margin-bottom:7px}
.cap li{font-size:.79rem;color:#6b6659;line-height:1.62;margin-bottom:3px;list-style:none;
padding-left:11px;position:relative}
.cap li:before{content:"·";position:absolute;left:2px;color:#c4bfb2}
.cap ul{margin:0;padding:0}
h2.tk{font-size:1.16rem;font-weight:800;margin:34px 0 3px;letter-spacing:-.02em}
h2.tk + p{margin:0 0 15px;color:#8a8578;font-size:.85rem}
.card{background:#fff;border:1px solid #ece8de;border-radius:16px;padding:20px 19px;margin-bottom:12px;
display:block;text-decoration:none;color:inherit;transition:border-color .15s,transform .15s}
.card:hover{border-color:#F07040;transform:translateY(-1px)}
.card.best{border:2px solid #F07040;background:linear-gradient(180deg,#fff9f5,#fff)}
.tag{display:inline-block;font-size:.68rem;font-weight:700;border-radius:5px;padding:2px 7px;
margin-bottom:9px;background:#fdf0e9;color:#E55A00}
.card h3{font-size:1.06rem;font-weight:800;margin:0 0 4px;letter-spacing:-.02em;line-height:1.4}
.card .sb{color:#8a8578;font-size:.83rem;margin:0 0 13px}
.meta{display:flex;flex-wrap:wrap;gap:9px;font-size:.75rem;color:#8a8578;margin-bottom:13px}
.meta span{background:#f6f3ec;border-radius:6px;padding:3px 8px}
.meta .rt{background:#fdf0e9;color:#E55A00;font-weight:700}
.sec{font-size:.72rem;font-weight:700;color:#a8a294;margin:0 0 5px;letter-spacing:.02em}
.card ul{margin:0 0 13px;padding:0}
.card li{list-style:none;font-size:.85rem;line-height:1.62;color:#4a4740;padding-left:15px;
position:relative;margin-bottom:3px}
.card li:before{content:"→";position:absolute;left:0;color:#c4a08c;font-size:.78rem}
.who li:before{content:"✓";color:#8fa87f}
.buy{display:flex;align-items:center;gap:11px;margin-top:15px;padding-top:14px;border-top:1px solid #f2efe7}
.pr{font-size:1.18rem;font-weight:800;letter-spacing:-.02em}
.pr s{font-size:.82rem;font-weight:400;color:#b5b0a4;margin-right:6px}
.save{font-size:.72rem;color:#E55A00;font-weight:700;background:#fdf0e9;border-radius:5px;padding:3px 7px}
.go{margin-left:auto;background:#E55A00;color:#fff;border-radius:10px;padding:11px 19px;
font-size:.87rem;font-weight:700;white-space:nowrap}
.card.best .go{background:linear-gradient(93deg,#F07040,#E55A00)}
.note{color:#a8a294;font-size:.78rem;line-height:1.7;margin-top:26px;text-align:center}
@media(max-width:560px){
 .hero{padding:26px 20px}.hero h1{font-size:1.42rem}
 .card{padding:17px 16px}
 .buy{flex-wrap:wrap}.go{margin-left:0;width:100%;text-align:center}
}
"""


def won(n):
    return f"{n:,}원"


def card_html(c):
    cap = CAPTAINS[c["cap"]]
    meta = [f"<span>{c['time']}</span>"]
    if c.get("lessons"):
        meta.insert(0, f"<span>{c['lessons']}강</span>")
    meta.append(f"<span>{H.escape(cap['n'])}</span>")
    meta.append("<span>180일 수강</span>")
    if c.get("rating"):
        meta.append(f"<span class='rt'>★ {c['rating']}</span>")

    price = f"<span class='pr'>{won(c['price'])}</span>"
    save = ""
    if c.get("list"):
        price = (f"<span class='pr'><s>{won(c['list'])}</s>{won(c['price'])}</span>")
        save = f"<span class='save'>{won(c['list'] - c['price'])} 아낌</span>"

    return f"""<a class="card{' best' if c.get('best') else ''}" href="{BASE}{c['id']}"
 target="_blank" rel="noopener">
{'<span class="tag">3종 통합 · 개별 구매 대비 20% 할인</span>' if c.get('best') else ''}
<h3>{H.escape(c['t'])}</h3>
<p class="sb">{H.escape(c['sub'])}</p>
<div class="meta">{''.join(meta)}</div>
<p class="sec">이런 분께</p>
<ul class="who">{''.join(f'<li>{H.escape(w)}</li>' for w in c['who'])}</ul>
<p class="sec">이걸 배웁니다</p>
<ul>{''.join(f'<li>{H.escape(l)}</li>' for l in c['learn'])}</ul>
<div class="buy">{price}{save}<span class="go">자세히 보기 →</span></div>
</a>"""


def build(courses=None):
    if courses is None:
        courses = json.loads((ROOT / "content/school_courses.json").read_text(encoding="utf-8"))
    by = {c["id"]: c for c in courses}
    OUT.mkdir(exist_ok=True)

    caps = "".join(
        f"""<div class="cap"><div class="nm">{H.escape(v['n'])}</div>
<ul>{''.join(f'<li>{H.escape(b)}</li>' for b in v['b'])}</ul></div>"""
        for v in CAPTAINS.values())

    body = f"""<div class="hero">
<span class="kk">Soonsal School</span>
<h1>현업에 있는 사람에게<br>직접 듣는 금융 커리어</h1>
<p>홍콩·한국의 투자은행과 헤지펀드에서 지금도 일하고 있는 캡틴들이,
검색으로는 안 나오는 것만 골라 알려드립니다.</p>
</div>
<div class="caps">{caps}</div>"""

    for title, sub, ids in TRACKS:
        cards = "".join(card_html(by[i]) for i in ids if i in by)
        body += f'<h2 class="tk">{title}</h2><p>{sub}</p>{cards}'

    body += """<p class="note">모든 강의는 결제 후 180일간 무제한 다시 보기.
결제와 수강은 순살스쿨(liveklass)에서 진행됩니다.</p>"""

    try:
        import build_nav
        nav = "<style>" + build_nav.HEADER_CSS + "</style>" + build_nav.header_html("/school/")
    except Exception:
        nav = ""

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>순살 스쿨 | 금융권 취업·투자 클래스</title>
<meta name="description" content="홍콩·한국의 투자은행과 헤지펀드 현직자에게 배우는 IBD·IPO·M&A·바이사이드·퀀트 클래스."/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&display=swap" rel="stylesheet"/>
<script src="/ss-config.js"></script>
<style>
body{{margin:0;background:#faf8f3;color:#2b2b2b;
font-family:'DM Sans',-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;
-webkit-font-smoothing:antialiased}}
{CSS}
</style></head><body>
{nav}
<div class="sc">{body}</div>
<script src="/soonsal.js" defer></script>
</body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"🎓 school: 강의 {len(courses)}개 · 캡틴 {len(CAPTAINS)}명")


if __name__ == "__main__":
    build()

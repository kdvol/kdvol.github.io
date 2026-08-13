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
        # 현직이 맨 위. 유니콘 Head of Corp Dev와 투자유치 총괄은 이제 전 직장이다.
        "b": ["현 국내 대형 PE 투자운용역",
              "전 국내 유니콘 기업 Head of Corporate Development — 대규모 투자유치·전략투자 집행 총괄",
              "전 Deutsche Bank 기업금융부(IBD) 등 글로벌 기업금융 10년+"],
        # 구조화 데이터에는 현직과 가장 강한 이력을 한 줄로 붙인다.
        # b[0]만 쓰면 Deutsche Bank가 검색 결과에서 통째로 빠진다.
        "seo": "현 국내 대형 PE 투자운용역 · 전 Deutsche Bank 기업금융부(IBD) 등 글로벌 기업금융 10년+",
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
.sc{max-width:1000px;margin:0 auto;padding:38px 20px 90px}

/* 머리 */
.ph{margin-bottom:30px;padding-bottom:26px;border-bottom:1px solid #1e1e1e}
.ph .ey{font-size:.7rem;font-weight:800;letter-spacing:.12em;color:#F07040;
text-transform:uppercase;margin-bottom:12px}
.ph h1{font-size:2.1rem;font-weight:800;letter-spacing:-.04em;line-height:1.22;
margin:0 0 12px;color:#f5f2ea}
.ph p{margin:0;color:#8b8578;font-size:.93rem;line-height:1.75;max-width:50ch}

/* 강사 — 세 칸 균등. 사진 없이 타이포만으로 신뢰를 만든다 */
.caps{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1px;
background:#1e1e1e;border:1px solid #1e1e1e;border-radius:12px;overflow:hidden;margin-bottom:52px}
.cap{background:#141414;padding:18px 17px}
.cap .nm{font-weight:800;font-size:.9rem;color:#f2efe8;margin-bottom:9px;
display:flex;align-items:center;gap:7px}
.cap .nm:before{content:"";width:5px;height:5px;border-radius:50%;background:#F07040;flex:0 0 auto}
.cap ul{margin:0;padding:0}
.cap li{list-style:none;font-size:.76rem;color:#807a6e;line-height:1.65;margin-bottom:3px}

/* 트랙 머리 */
.trk{margin-bottom:54px}
.tk{display:flex;align-items:baseline;gap:9px;margin:0 0 3px}
.tk h2{font-size:1.2rem;font-weight:800;letter-spacing:-.025em;color:#f2efe8;margin:0}
.tk .n{font-size:.7rem;color:#57524a;font-variant-numeric:tabular-nums}
.tkd{color:#736e66;font-size:.83rem;margin:0 0 20px;line-height:1.6}

/* 카드 — 통합본은 전체 폭, 나머지는 2열. 한 줄로 늘어놓으면 훑을 수 없다. */
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.card{border:1px solid #212121;border-top:3px solid var(--ac,#2a2a2a);border-radius:14px;
background:#141414;overflow:hidden;display:flex;flex-direction:column;
transition:border-color .18s,transform .18s}
.card:hover{border-color:#2f2f2f;border-top-color:var(--ac,#2a2a2a);transform:translateY(-2px)}
.card.hero{margin-bottom:16px;background:linear-gradient(172deg,#1a1512,#141414)}
.card a{color:inherit;text-decoration:none}

/* 커버 — 빌드 때 전부 880x495로 맞춰 넣었다. CSS는 한 규칙이면 된다. */
.cv{display:block;aspect-ratio:16/9;background:#101010;overflow:hidden}
.cv img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .5s ease}
.card:hover .cv img{transform:scale(1.02)}

.cb{padding:16px 18px 0;flex:1}
.hd{display:flex;align-items:center;gap:8px;margin-bottom:9px;min-height:18px}
.lv{font-size:.66rem;font-weight:800;letter-spacing:.06em;color:var(--ac,#8b8578);
display:inline-flex;align-items:center;gap:6px}
.lv:before{content:"";width:14px;height:2px;background:var(--ac,#2a2a2a);border-radius:2px}
.tag{font-size:.65rem;font-weight:800;border-radius:4px;padding:3px 8px;
background:rgba(240,112,64,.14);color:#F5A481;letter-spacing:.02em}

.card h3{margin:0 0 6px;font-size:1.24rem;font-weight:800;letter-spacing:-.03em;
line-height:1.3;color:#fbf9f5}
.card.hero h3{font-size:1.7rem}
.card .sb{color:#847e73;font-size:.85rem;margin:0 0 13px;line-height:1.55}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.meta span{font-size:.7rem;color:#847e73;border:1px solid #242424;border-radius:5px;padding:3px 8px}
.meta .rt{border-color:#4a2d1c;color:#F5A481;font-weight:700}

/* 접힌 상세 — 펼치기 전엔 한 줄이다 */
.det{border-top:1px solid #1c1c1c;margin:0 -18px}
.det>summary{list-style:none;cursor:pointer;padding:12px 18px;font-size:.76rem;
font-weight:700;color:#736e66;display:flex;align-items:center;gap:6px;transition:color .15s}
.det>summary::-webkit-details-marker{display:none}
.det>summary:after{content:"⌄";margin-left:auto;transition:transform .2s;font-size:.9rem}
.det[open]>summary:after{transform:rotate(180deg)}
.det>summary:hover{color:#b8b2a8}
.det .dd{padding:0 18px 14px}
.sec{font-size:.64rem;font-weight:800;color:#57524a;letter-spacing:.09em;
text-transform:uppercase;margin:0 0 6px}
.det ul{margin:0 0 12px;padding:0}
.det li{list-style:none;font-size:.82rem;line-height:1.65;color:#a8a29a;
padding-left:15px;position:relative;margin-bottom:3px}
.det li:before{content:"";position:absolute;left:1px;top:.62em;width:5px;height:1px;background:#413c35}
.who li:before{content:"";left:0;top:.5em;width:5px;height:5px;border-radius:50%;
background:none;border:1px solid #4d5546}

/* 맛보기 */
.tz{display:block;position:relative;cursor:pointer;background:#000;aspect-ratio:16/9;
margin:0 18px 14px;border-radius:9px;overflow:hidden;border:1px solid #242424}
.tz img{width:100%;height:100%;object-fit:cover;display:block;opacity:.78;transition:opacity .25s}
.tz:hover img{opacity:1}
.tz iframe{width:100%;height:100%;border:0;display:block}
.tz .pl{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:44px;height:44px;
border-radius:50%;background:rgba(0,0,0,.5);border:1.5px solid rgba(255,255,255,.5);
color:#fff;display:flex;align-items:center;justify-content:center;font-size:14px;padding-left:3px}
.tz .lb{position:absolute;left:11px;bottom:10px;background:rgba(0,0,0,.62);color:#fff;
font-size:.66rem;font-weight:700;border-radius:4px;padding:3px 8px}

/* 결제 줄 */
.card a.buy{display:flex;align-items:center;flex-wrap:wrap;gap:12px;padding:15px 18px;
border-top:1px solid #1c1c1c;background:#111;margin-top:auto}
.pr{font-size:1.08rem;font-weight:800;letter-spacing:-.025em;color:#f2efe8;
font-variant-numeric:tabular-nums}
.card.hero .pr{font-size:1.24rem}
.pr s{display:block;font-size:.72rem;font-weight:400;color:#57524a;margin-bottom:1px}
.save{font-size:.68rem;color:#F5A481;font-weight:700;border:1px solid #4a2d1c;
border-radius:4px;padding:3px 8px;white-space:nowrap}
.go{margin-left:auto;background:#E55A00;color:#fff;border-radius:8px;padding:11px 18px;
font-size:.82rem;font-weight:800;white-space:nowrap;transition:background .15s;flex:0 0 auto}
.card:hover .go{background:#F07040}

.note{color:#57524a;font-size:.77rem;line-height:1.75;margin-top:10px;
padding-top:26px;border-top:1px solid #1a1a1a;text-align:center}
@media(max-width:640px){
 .sc{padding:26px 15px 74px}
 .ph h1{font-size:1.62rem}
 .grid{grid-template-columns:1fr;gap:14px}
 .card.hero h3{font-size:1.42rem}
 .card h3{font-size:1.18rem}
 .cb{padding:15px 16px 0}
 .det{margin:0 -16px}.det>summary,.det .dd{padding-left:16px;padding-right:16px}
 .tz{margin:0 16px 13px}
 .card a.buy{padding:14px 16px;gap:10px}
 .go{margin-left:0;width:100%;text-align:center;padding:13px;margin-top:2px}
}
"""




def won(n):
    return f"{n:,}원"


def card_html(c, hero=False):
    cap = CAPTAINS[c["cap"]]
    meta = []
    if c.get("lessons"):
        meta.append(f"<span>{c['lessons']}강</span>")
    meta += [f"<span>{c['time']}</span>", f"<span>{H.escape(cap['n'])}</span>"]
    if c.get("rating"):
        meta.append(f"<span class='rt'>★ {c['rating']}</span>")

    if c.get("list"):
        price = f"<span class='pr'><s>{won(c['list'])}</s>{won(c['price'])}</span>"
        save = f"<span class='save'>{won(c['list'] - c['price'])} 절약</span>"
    else:
        price, save = f"<span class='pr'>{won(c['price'])}</span>", ""

    cover = (f'<span class="cv"><img src="{c["img"]}" alt="{H.escape(c["t"])}"'
             f' loading="lazy" decoding="async" width="880" height="495"/></span>'
             ) if c.get("img") else ""

    # 접어 둔다. 카드마다 5~7줄을 펼쳐 놓으면 훑을 수 없다.
    det = (f'<details class="det"><summary>커리큘럼 · 대상 보기</summary>'
           f'<div class="dd"><p class="sec">이런 분께</p>'
           f'<ul class="who">{"".join(f"<li>{H.escape(w)}</li>" for w in c["who"])}</ul>'
           f'<p class="sec">이걸 배웁니다</p>'
           f'<ul>{"".join(f"<li>{H.escape(l)}</li>" for l in c["learn"])}</ul></div></details>')

    teaser = ""
    if c.get("teaser"):
        teaser = (f'<span class="tz" data-v="{c["teaser"]}">'
                  f'<img src="https://i.ytimg.com/vi/{c["teaser"]}/hqdefault.jpg"'
                  f' alt="맛보기 영상" loading="lazy" width="480" height="270"/>'
                  f'<span class="pl">▶</span><span class="lb">1분 맛보기</span></span>')

    lv = f'<span class="lv">{H.escape(c["level"])}</span>' if c.get("level") else ""
    ac = f' style="--ac:{c["accent"]}"' if c.get("accent") else ""
    tag = ('<span class="tag">3종 통합 · 20% 할인</span>' if hero else "")

    return f"""<div class="card{' hero' if hero else ''}"{ac}>
<a class="top" href="{BASE}{c['id']}" target="_blank" rel="noopener">{cover}</a>
<div class="cb">
<div class="hd">{lv}{tag}</div>
<h3><a href="{BASE}{c['id']}" target="_blank" rel="noopener">{H.escape(c['t'])}</a></h3>
<p class="sb">{H.escape(c['sub'])}</p>
<div class="meta">{''.join(meta)}</div>
{det}
</div>{teaser}
<a class="buy" href="{BASE}{c['id']}" target="_blank" rel="noopener">
{price}{save}<span class="go">자세히 보기 →</span></a>
</div>"""


def course_ld(courses):
    """강의 목록을 Course로 표시한다. 검색에서 강의 리치결과(제공자·분량·가격)로
    잡히는 형태다. 지어낸 값은 넣지 않는다 — 평점은 표시된 강의만."""
    items = []
    for i, c in enumerate(courses, 1):
        cap = CAPTAINS[c["cap"]]
        node = {
            "@type": "Course",
            "name": c["t"],
            "description": c["sub"] + " — " + " / ".join(c["learn"])[:180],
            "url": BASE + c["id"],
            "provider": {"@type": "Organization", "name": "순살 스쿨",
                         "url": "https://soonsal.com/school/"},
            "inLanguage": "ko",
            "offers": {"@type": "Offer", "price": c["price"], "priceCurrency": "KRW",
                       "category": "Paid", "availability": "https://schema.org/InStock",
                       "url": BASE + c["id"]},
            "hasCourseInstance": {
                "@type": "CourseInstance",
                "courseMode": "online",
                "courseWorkload": _iso_dur(c["time"]),
                "instructor": {"@type": "Person", "name": cap["n"],
                               "description": cap.get("seo") or cap["b"][0]},
            },
        }
        if c.get("img"):
            node["image"] = "https://soonsal.com" + c["img"]
        if c.get("rating"):
            node["aggregateRating"] = {"@type": "AggregateRating",
                                       "ratingValue": c["rating"], "ratingCount": 1,
                                       "bestRating": "5"}
        items.append({"@type": "ListItem", "position": i, "item": node})
    return {"@context": "https://schema.org", "@type": "ItemList",
            "name": "순살 스쿨 클래스", "itemListElement": items}


def _iso_dur(s):
    """'8시간 48분' → 'PT8H48M'. 검색이 읽는 형식은 ISO 8601이다."""
    import re as _re
    h = _re.search(r"(\d+)시간", s)
    m = _re.search(r"(\d+)분", s)
    out = "PT" + (f"{h.group(1)}H" if h else "") + (f"{m.group(1)}M" if m else "")
    return out if out != "PT" else None


def build(courses=None):
    if courses is None:
        courses = json.loads((ROOT / "content/school_courses.json").read_text(encoding="utf-8"))
    by = {c["id"]: c for c in courses}
    OUT.mkdir(exist_ok=True)

    caps = "".join(
        f"""<div class="cap"><div class="nm">{H.escape(v['n'])}</div>
<ul>{''.join(f'<li>{H.escape(b)}</li>' for b in v['b'])}</ul></div>"""
        for v in CAPTAINS.values())

    body = f"""<div class="ph">
<div class="ey">Soonsal School</div>
<h1>현업에 있는 사람에게<br>직접 듣는 금융 커리어</h1>
<p>홍콩·한국의 투자은행과 헤지펀드에서 지금도 일하고 있는 캡틴들이,
검색으로는 나오지 않는 것만 골라 알려드립니다.</p>
</div>
<div class="caps">{caps}</div>"""

    for title, sub, ids in TRACKS:
        # 통합본은 전체 폭, 나머지는 2열. 7장을 한 줄로 세우면 훑을 수 없다.
        hero_html, rest = "", []
        for i in ids:
            if i not in by:
                continue
            if by[i].get("best"):
                hero_html = card_html(by[i], hero=True)
            else:
                rest.append(card_html(by[i]))
        grid = f'<div class="grid">{"".join(rest)}</div>' if rest else ""
        body += (f'<div class="trk"><div class="tk"><h2>{title}</h2>'
                 f'<span class="n">{len(ids)}개 클래스</span></div>'
                 f'<p class="tkd">{sub}</p>{hero_html}{grid}</div>')

    body += """<p class="note">모든 클래스는 결제 후 180일간 무제한 다시 보기.<br>
결제와 수강은 순살스쿨(liveklass)에서 진행됩니다.</p>"""

    try:
        import build_nav
        nav = "<style>" + build_nav.HEADER_CSS + "</style>" + build_nav.header_html("/school/")
    except Exception:
        nav = ""

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>순살 스쿨 | 금융권 취업·투자 클래스</title>
<meta name="description" content="홍콩·한국의 투자은행과 헤지펀드 현직자에게 배우는 IBD·IPO·M&A·바이사이드·퀀트 클래스. 31강 8시간 48분 통합본부터 1분 맛보기까지."/>
<link rel="canonical" href="https://soonsal.com/school/"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="순살 스쿨 — 현직자가 여는 금융 커리어 클래스"/>
<meta property="og:description" content="전 Deutsche Bank IBD · 현직 홍콩 PM · 홍콩 퀀트펀드 6년. IBD·IPO·M&A·바이사이드·퀀트."/>
<meta property="og:url" content="https://soonsal.com/school/"/>
<meta property="og:image" content="https://soonsal.com/assets/school/42917.jpg"/>
<meta name="twitter:card" content="summary_large_image"/>
<script type="application/ld+json">{json.dumps(course_ld(courses), ensure_ascii=False)}</script>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&display=swap" rel="stylesheet"/>
<script src="/ss-config.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#111;color:#eee;font-family:'DM Sans','Apple SD Gothic Neo',sans-serif;
min-height:100vh;-webkit-text-size-adjust:100%;-webkit-font-smoothing:antialiased}}
a{{color:#eee;text-decoration:none}}
{CSS}
</style></head><body>
{nav}
<div class="sc">{body}</div>
<script src="/soonsal.js" defer></script>
<script>
document.querySelectorAll('.tz[data-v]').forEach(function (b) {{
  b.addEventListener('click', function (e) {{
    e.preventDefault();
    var v = b.getAttribute('data-v');
    b.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + v +
      '?autoplay=1&rel=0" allow="autoplay; encrypted-media" allowfullscreen></iframe>';
    b.removeAttribute('data-v');
  }});
}});
</script>
</body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"🎓 school: 강의 {len(courses)}개 · 캡틴 {len(CAPTAINS)}명")


if __name__ == "__main__":
    build()

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
.sc{max-width:880px;margin:0 auto;padding:34px 16px 80px}

/* 머리 — 배경 박스를 쓰지 않는다. nav 바로 아래 어두운 박스를 또 얹으면
   층이 겹쳐 보인다. 여백과 타이포로 위계를 만든다. */
.ph{margin-bottom:34px;padding-bottom:30px;border-bottom:1px solid #202020}
.ph .ey{font-size:.72rem;font-weight:700;letter-spacing:.09em;color:#F07040;
text-transform:uppercase;margin-bottom:11px}
.ph h1{font-size:2rem;font-weight:800;letter-spacing:-.035em;line-height:1.24;
margin:0 0 13px;color:#f2efe8}
.ph p{margin:0;color:#8b8578;font-size:.95rem;line-height:1.75;max-width:54ch}

/* 강사 — 이 가격대에선 첫 질문이다. 사진 없이 타이포만으로 신뢰를 만든다 */
.caps{display:grid;grid-template-columns:repeat(auto-fit,minmax(232px,1fr));gap:1px;
background:#202020;border:1px solid #202020;border-radius:14px;overflow:hidden;margin-bottom:44px}
.cap{background:#141414;padding:19px 18px}
.cap .nm{font-weight:800;font-size:.94rem;color:#f2efe8;margin-bottom:10px;
display:flex;align-items:center;gap:7px}
.cap .nm:before{content:"";width:5px;height:5px;border-radius:50%;background:#F07040;flex:0 0 auto}
.cap ul{margin:0;padding:0}
.cap li{list-style:none;font-size:.79rem;color:#8b8578;line-height:1.66;margin-bottom:4px}

/* 트랙 */
.tk{display:flex;align-items:baseline;gap:10px;margin:0 0 4px}
.tk h2{font-size:1.14rem;font-weight:800;letter-spacing:-.02em;color:#f2efe8;margin:0}
.tk .n{font-size:.72rem;color:#5f5a52;font-variant-numeric:tabular-nums}
.tkd{color:#7a756c;font-size:.85rem;margin:0 0 18px;line-height:1.6}
.trk{margin-bottom:46px}

/* 강의 카드 */
.card{border:1px solid #222;border-radius:16px;background:#141414;margin-bottom:13px;
overflow:hidden;transition:border-color .18s}
.card:hover{border-color:#333}
.card.best{border-color:#4a2d1c;background:linear-gradient(168deg,#191512,#141414)}
.card.best:hover{border-color:#6b3f24}
.card>a{display:block;color:inherit}
/* 커버 — 글만 있는 카드는 안 팔린다. liveklass 상세페이지의 실제 커버를 쓴다. */
.cv{display:block;position:relative;aspect-ratio:16/9;overflow:hidden;background:#0d0d0d}
.cv img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .4s ease}
.card:hover .cv img{transform:scale(1.025)}
.cv:after{content:"";position:absolute;inset:0;
background:linear-gradient(180deg,transparent 55%,rgba(20,20,20,.92) 100%)}
.cb{padding:18px 21px 0}
.tag{display:inline-block;font-size:.68rem;font-weight:700;letter-spacing:.02em;
border-radius:5px;padding:3px 9px;margin-bottom:11px;background:rgba(240,112,64,.13);color:#F5A481}
.card h3{font-size:1.1rem;font-weight:800;letter-spacing:-.025em;line-height:1.4;
margin:0 0 5px;color:#f2efe8}
.card .sb{color:#7a756c;font-size:.85rem;margin:0 0 14px;line-height:1.55}
.meta{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:16px}
.meta span{font-size:.72rem;color:#8b8578;border:1px solid #262626;border-radius:6px;padding:3px 9px}
.meta .rt{border-color:#4a2d1c;color:#F5A481;font-weight:700}

.sec{font-size:.68rem;font-weight:700;color:#5f5a52;letter-spacing:.08em;
text-transform:uppercase;margin:0 0 7px}
.card ul{margin:0 0 15px;padding:0}
.card li{list-style:none;font-size:.86rem;line-height:1.68;color:#b8b2a8;
padding-left:17px;position:relative;margin-bottom:4px}
.card li:before{content:"";position:absolute;left:2px;top:.62em;width:5px;height:1px;background:#4a453d}
.who li:before{content:"";left:1px;top:.5em;width:6px;height:6px;border-radius:50%;
background:none;border:1px solid #57604f}

/* 맛보기 */
.tz{display:block;position:relative;cursor:pointer;background:#000;aspect-ratio:16/9;
margin:0 21px 17px;border-radius:11px;overflow:hidden;border:1px solid #262626}
.tz img{width:100%;height:100%;object-fit:cover;display:block;opacity:.8;transition:opacity .25s}
.tz:hover img{opacity:1}
.tz iframe{width:100%;height:100%;border:0;display:block}
.tz .pl{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:50px;height:50px;
border-radius:50%;background:rgba(0,0,0,.5);border:1.5px solid rgba(255,255,255,.5);
color:#fff;display:flex;align-items:center;justify-content:center;font-size:15px;padding-left:3px}
.tz .lb{position:absolute;left:12px;bottom:11px;background:rgba(0,0,0,.6);color:#fff;
font-size:.69rem;font-weight:700;border-radius:5px;padding:3px 9px;letter-spacing:.02em}

/* 결제 줄 — 버튼이 카드 폭을 꽉 채우게. 예전엔 오른쪽에 떠서 어정쩡했다 */
/* 결제 줄. .card a{display:block}이 이 flex를 이겨서 값들이 겹쳐 보였다 —
   선택자를 .card>a로 좁히고 여기선 명시적으로 flex를 건다. */
.card a.buy{display:flex;align-items:center;flex-wrap:wrap;gap:14px;padding:17px 21px;
border-top:1px solid #1f1f1f;background:#121212}
.pr{font-size:1.16rem;font-weight:800;letter-spacing:-.025em;color:#f2efe8;
font-variant-numeric:tabular-nums}
.pr s{display:block;font-size:.76rem;font-weight:400;color:#5f5a52;margin-bottom:1px}
.save{font-size:.71rem;color:#F5A481;font-weight:700;border:1px solid #4a2d1c;
border-radius:5px;padding:4px 9px;white-space:nowrap}
.go{margin-left:auto;background:#E55A00;color:#fff;border-radius:9px;padding:12px 22px;
font-size:.86rem;font-weight:700;white-space:nowrap;transition:background .15s;
flex:0 0 auto}
.card:hover .go{background:#F07040}

.note{color:#5f5a52;font-size:.79rem;line-height:1.75;margin-top:34px;
padding-top:24px;border-top:1px solid #1c1c1c;text-align:center}
@media(max-width:600px){
 .sc{padding:26px 15px 70px}
 .ph h1{font-size:1.6rem}
 .cb{padding:18px 17px 0}
 .tz{margin:0 17px 15px}
 .card a.buy{padding:16px 17px;gap:11px}
 .go{margin-left:0;width:100%;text-align:center;padding:14px;margin-top:3px}
}
"""



def won(n):
    return f"{n:,}원"


def card_html(c):
    cap = CAPTAINS[c["cap"]]
    meta = []
    if c.get("lessons"):
        meta.append(f"<span>{c['lessons']}강</span>")
    meta += [f"<span>{c['time']}</span>", f"<span>{H.escape(cap['n'])}</span>",
             "<span>180일 수강</span>"]
    if c.get("rating"):
        meta.append(f"<span class='rt'>★ {c['rating']}</span>")

    if c.get("list"):
        price = f"<span class='pr'><s>{won(c['list'])}</s>{won(c['price'])}</span>"
        save = f"<span class='save'>{won(c['list'] - c['price'])} 절약</span>"
    else:
        price, save = f"<span class='pr'>{won(c['price'])}</span>", ""

    # 티저는 누를 때만 재생한다 — 카드마다 iframe을 미리 심으면 페이지가 무거워진다
    teaser = ""
    if c.get("teaser"):
        teaser = (f'<span class="tz" data-v="{c["teaser"]}">'
                  f'<img src="https://i.ytimg.com/vi/{c["teaser"]}/hqdefault.jpg"'
                  f' alt="맛보기 영상" loading="lazy" width="480" height="270"/>'
                  f'<span class="pl">▶</span><span class="lb">1분 맛보기</span></span>')

    cover = (f'<span class="cv"><img src="{c["img"]}" alt="{H.escape(c["t"])}"'
             f' loading="lazy" width="880" height="495"/></span>') if c.get("img") else ""

    return f"""<div class="card{' best' if c.get('best') else ''}">
<a href="{BASE}{c['id']}" target="_blank" rel="noopener">{cover}<div class="cb">
{'<span class="tag">3종 통합 · 개별 구매 대비 20% 할인</span>' if c.get('best') else ''}
<h3>{H.escape(c['t'])}</h3>
<p class="sb">{H.escape(c['sub'])}</p>
<div class="meta">{''.join(meta)}</div>
<p class="sec">이런 분께</p>
<ul class="who">{''.join(f'<li>{H.escape(w)}</li>' for w in c['who'])}</ul>
<p class="sec">이걸 배웁니다</p>
<ul>{''.join(f'<li>{H.escape(l)}</li>' for l in c['learn'])}</ul>
</div></a>{teaser}
<a class="buy" href="{BASE}{c['id']}" target="_blank" rel="noopener">
{price}{save}<span class="go">자세히 보기 →</span></a>
</div>"""


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
        cards = "".join(card_html(by[i]) for i in ids if i in by)
        body += (f'<div class="trk"><div class="tk"><h2>{title}</h2>'
                 f'<span class="n">{len(ids)}개 클래스</span></div>'
                 f'<p class="tkd">{sub}</p>{cards}</div>')

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
<meta name="description" content="홍콩·한국의 투자은행과 헤지펀드 현직자에게 배우는 IBD·IPO·M&A·바이사이드·퀀트 클래스."/>
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

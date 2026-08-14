#!/usr/bin/env python3
"""공개 지식베이스(위키) 생성 — 엔티티 페이지 + 허브.

각 엔티티(기업·인물·자산·기관)마다 /wiki/{slug}.html 을 만든다:
 - 등장 스토리 타임라인(최신순, 뉴스레터 딥링크)
 - 연관 엔티티(같은 스토리 동시등장 상위) — 위키 그래프
 - 관련 주제(/topics/ 로 링크)
 - 스토리에 붙은 영어 표현

엔티티 태그는 통제 어휘를 균일 적용해 뽑으므로 섹션라벨보다 일관적.
generate_seo.py 파이프라인이 atomize 다음에 호출. 데이터 파일(entities.json)만
관리하면 되고 사람이 페이지를 손댈 필요 없음.
"""
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

import atomize

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"
OUT = ROOT / "wiki"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#111;color:#eee;font-family:'DM Sans','Apple SD Gothic Neo',sans-serif;min-height:100vh}
.wrap{max-width:840px;margin:0 auto;padding:32px 20px}
a{color:#eee;text-decoration:none}
.home{color:#F07040;font-size:.9rem;display:inline-block;margin-bottom:18px}
h1{font-size:1.6rem;margin-bottom:4px}
.kind{color:#f5a623;font-size:.82rem;letter-spacing:.04em;text-transform:uppercase}
.sub{color:#888;font-size:.9rem;margin:6px 0 22px}
.sec{margin:22px 0}
.sec h2{font-size:1.05rem;margin-bottom:10px;color:#ddd}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{border:1px solid #333;border-radius:999px;padding:6px 13px;font-size:.86rem;transition:.15s}
.chip:hover{border-color:#F07040;color:#F07040}
.chip b{color:#888;font-weight:400;margin-left:5px;font-size:.8rem}
.tp{background:#1a2030;border-color:#2a3550}
/* 인용 블록 — 커뮤니티·위키에서 그대로 퍼갈 수 있는 한 덩어리 */
.cite{background:#161616;border:1px solid #232323;border-left:3px solid #F07040;
border-radius:0 10px 10px 0;padding:15px 17px;margin:14px 0 18px}
.cite p{margin:0}
.cite .c1{font-size:1rem;line-height:1.65;color:#e8e4dc}
.cite .c1 b{color:#fff;font-weight:700}
.cite .c2{font-size:.88rem;line-height:1.7;color:#9a948a;margin-top:9px}
.cite .c3{font-size:.72rem;color:#5f5a52;margin-top:11px}
/* 월 구분 — 목록이 아니라 기록으로 읽히게 */
.mo{display:flex;align-items:baseline;gap:8px;margin:22px 0 4px;padding-bottom:6px;
border-bottom:1px solid #1e1e1e}
.mo span{font-size:.92rem;font-weight:800;color:#cfc9bf;letter-spacing:-.01em}
.mo b{font-size:.72rem;font-weight:400;color:#57524a}
.stx{display:flex;flex-direction:column;gap:3px;min-width:0}
.lead{font-size:.84rem;line-height:1.6;color:#8b857b}
.story{padding:11px 4px;border-bottom:1px solid #1c1c1c}
.story a{display:flex;gap:12px;align-items:baseline}
.d{color:#777;font-size:.82rem;white-space:nowrap;font-variant-numeric:tabular-nums;padding-top:2px}
.st{font-size:.98rem;line-height:1.5;transition:.15s;font-weight:500}
.story:hover .st{color:#F07040}
.lb{display:inline-block;font-size:.7rem;color:#888;letter-spacing:.03em;margin-top:4px}
details.eng{margin:6px 0 2px}
details.eng>summary{list-style:none;font-size:.72rem;color:#2ecc71;cursor:pointer;display:inline-block}
details.eng>summary::-webkit-details-marker{display:none}
details.eng>summary::before{content:"🔤 "}
details.eng[open]>summary{margin-bottom:6px;color:#888}
.engbox{border-left:2px solid #2ecc71;padding:2px 0 2px 11px}
.eng-t{font-size:.82rem;color:#2ecc71;font-weight:600;margin-top:10px}
.eng-t:first-child{margin-top:0}
.eng-k{font-size:.78rem;color:#9aa;margin-top:2px;line-height:1.55}
.eng-x{font-size:.76rem;color:#8a978a;line-height:1.55;margin-top:4px;font-style:italic}
.eng-xl{color:#667;font-size:.7rem;font-style:normal;display:block;margin-bottom:1px}
.grp{margin:26px 0}
.grp h2{font-size:1.15rem;margin-bottom:12px}
.more{color:#F07040;font-size:.86rem;margin-top:12px;display:inline-block}
"""


def head(title, desc, canonical, ld=None, crumb=("/topics/", "주제별 전체")):
    import build_nav
    ldtag = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    crumb_html = f'<a class="crumb" href="{crumb[0]}">← {crumb[1]}</a>' if crumb else ""
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title><meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{canonical}"><meta name="robots" content="index, follow">
<meta property="og:type" content="website"><meta property="og:site_name" content="순살브리핑 Soonsal">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{canonical}"><meta property="og:locale" content="ko_KR">
{build_nav.FONT_LINK}
{ldtag}<style>{CSS}{build_nav.HEADER_CSS}</style></head><body>
{build_nav.header_html("/topics/")}<div class="wrap">
{crumb_html}"""

FOOT = "</div></body></html>"


def first_sentence(body, limit=150):
    """스토리 본문 첫 문장. 요약을 지어내지 않고 우리가 쓴 문장을 그대로 쓴다."""
    s = re.sub(r"^[◾▪·\s]+", "", (body or "").strip())
    s = re.sub(r"\s+", " ", s)
    m = re.search(r"^(.{20,%d}?[.。!?])\s" % limit, s)
    out = (m.group(1) if m else s[:limit]).strip()
    return out.rstrip(",;·")


def span_label(items):
    """'2026년 2월~8월' — 인용할 때 기간이 있어야 사실이 된다."""
    ds = sorted(a["date"] for a in items)
    a0, a1 = ds[0], ds[-1]
    if a0[:4] == a1[:4]:
        if a0[5:7] == a1[5:7]:
            return f"{a0[:4]}년 {int(a0[5:7])}월"
        return f"{a0[:4]}년 {int(a0[5:7])}월~{int(a1[5:7])}월"
    return f"{a0[:4]}년 {int(a0[5:7])}월~{a1[:4]}년 {int(a1[5:7])}월"


def by_month(items):
    """월별로 묶는다. 목록은 훑을 수 없고 타임라인은 읽힌다."""
    out = []
    for a in items:                      # items는 최신순
        key = a["date"][:7]
        if not out or out[-1][0] != key:
            out.append((key, []))
        out[-1][1].append(a)
    return out


def clean_title(t):
    return re.sub(r"^[^\w<>&\"']{1,4}\s+", "", t).strip()


def build(atoms=None):
    if atoms is None:
        atoms = atomize.build()
    ent = atomize.load_entities()
    tax = atomize.load_tax()
    ent_by_slug = {e["slug"]: e for e in ent["entities"]}
    topic_names = {t["slug"]: t for t in tax["topics"]}
    types = ent["types"]
    min_n = ent.get("min_stories", 3)
    OUT.mkdir(exist_ok=True)
    today = date.today().isoformat()

    # 엔티티별 집계
    stories_of = defaultdict(list)
    cooc = defaultdict(Counter)
    topics_of = defaultdict(Counter)
    for a in atoms:
        es = a["entities"]
        for e in es:
            stories_of[e].append(a)
            for other in es:
                if other != e:
                    cooc[e][other] += 1
            for tp in a["topics"]:
                topics_of[e][tp] += 1

    built = []
    for e in ent["entities"]:
        slug = e["slug"]
        items = sorted(stories_of.get(slug, []), key=lambda a: a["date"], reverse=True)
        if len(items) < min_n:
            continue
        built.append(e)
        emoji = types.get(e["type"], {}).get("emoji", "🔖")
        type_label = types.get(e["type"], {}).get("label", "")
        canonical = f"{BASE}/wiki/{slug}.html"

        # 연관도 = lift: 동시등장수를 상대 엔티티의 전체 빈도로 정규화.
        # 원시 동시등장은 bitcoin·oil 같은 편재 엔티티가 지배 → 특이 연관을 못 봄.
        cand = []
        for s, n in cooc[slug].items():
            if s not in ent_by_slug or len(stories_of.get(s, [])) < min_n or n < 2:
                continue
            lift = n / len(stories_of[s])          # 상대가 나오면 이 엔티티도 나올 확률
            cand.append((ent_by_slug[s], n, lift))
        cand.sort(key=lambda x: (-x[2], -x[1]))
        related = [(e, n) for e, n, _ in cand[:8]]
        rel_html = "".join(
            f'<a class="chip" href="/wiki/{r["slug"]}.html">'
            f'{types.get(r["type"], {}).get("emoji", "")} {escape(r["name"])}<b>{n}</b></a>'
            for r, n in related)
        tps = [(topic_names[s], n) for s, n in topics_of[slug].most_common(6) if s in topic_names]
        tp_html = "".join(
            f'<a class="chip tp" href="/topics/{t["slug"]}.html">{t["emoji"]} {escape(t["name"])}<b>{n}</b></a>'
            for t, n in tps)

        # 월별 타임라인. 각 줄에 첫 문장을 붙여 '무슨 일이 있었나'가 읽히게 한다 —
        # 제목만 나열하면 목록이고, 한 줄이 붙으면 기록이 된다.
        rows = []
        for month, group in by_month(items):
            y, mm = month[:4], int(month[5:7])
            rows.append(f'<div class="mo" id="m{month}"><span>{y}년 {mm}월</span>'
                        f'<b>{len(group)}건</b></div>')
            for a in group:
                eng = ""
                if a["english"]:
                    eng = (f'<details class="eng"><summary>영어 표현 {len(a["english"])}</summary>'
                           f'<div class="engbox">{atomize.english_html(a["english"])}</div></details>')
                lead = first_sentence(a.get("body", ""))
                rows.append(
                    f'<div class="story"><a href="{a["url"]}">'
                    f'<span class="d">{a["date"][5:].replace("-", ".")}</span>'
                    f'<span class="stx"><span class="st">{escape(clean_title(a["title"]))}</span>'
                    + (f'<span class="lead">{escape(lead)}</span>' if lead else "")
                    + '</span></a>'
                    + (f'<div class="lb">{escape(a["label"])}</div>' if a["label"] else "")
                    + eng + "</div>")

        n_eng = sum(len(a["english"]) for a in items)
        ld = {"@context": "https://schema.org", "@type": "CollectionPage",
              "name": f"{e['name']} 관련 브리핑", "url": canonical, "inLanguage": "ko",
              "about": {"@type": {"company": "Organization", "person": "Person"}.get(e["type"], "Thing"),
                        "name": e["name"]},
              "isPartOf": {"@type": "WebSite", "name": "순살브리핑", "url": f"{BASE}/"},
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "url": f"{BASE}{a['url']}",
                   "name": clean_title(a["title"])} for i, a in enumerate(items[:40])]}}
        span = span_label(items)
        latest = items[0]
        lead = first_sentence(latest.get("body", ""), 170)
        # 인용되려면 '무엇을·언제·몇 건' 한 덩어리가 필요하다. 이 블록이 인용 단위다.
        cite = (
            f'<div class="cite"><p class="c1">'
            f'<b>{escape(e["name"])}</b>는 순살브리핑이 <b>{span}</b>에 걸쳐 '
            f'<b>{len(items)}건</b> 다룬 {type_label or "대상"}입니다.</p>'
            + (f'<p class="c2">가장 최근({latest["date"]}): {escape(lead)}</p>' if lead else "")
            + f'<p class="c3">이 페이지는 발행 때마다 자동 갱신됩니다 · '
              f'최종 {today}</p></div>')

        desc = (f"{e['name']} — 순살브리핑이 {span}에 걸쳐 {len(items)}건 다룬 기록. "
                + (f"가장 최근({latest['date']}): {lead[:80]} " if lead else "")
                + f"연관 {', '.join(r['name'] for r, _ in related[:4])}.")
        body = (head(f"{e['name']} 타임라인 — 순살브리핑 {len(items)}건 ({span})", desc, canonical, ld)
                + f'<div class="kind">{emoji} {type_label}</div>'
                + f'<h1>{escape(e["name"])} 타임라인</h1>'
                + cite
                + f'<p class="sub">스토리 {len(items)}건 · 영어 표현 {n_eng}개 · '
                  f'<a href="/topics/" style="color:#F07040">주제·대상 전체</a> · '
                  f'<a href="/search/" style="color:#F07040">검색</a></p>'
                + (f'<div class="sec"><h2>연관</h2><div class="chips">{rel_html}</div></div>' if rel_html else "")
                + (f'<div class="sec"><h2>주제</h2><div class="chips">{tp_html}</div></div>' if tp_html else "")
                + f'<div class="sec"><h2>타임라인 · {len(items)}건</h2>{"".join(rows)}</div>'
                + FOOT)
        (OUT / f"{slug}.html").write_text(body, encoding="utf-8")

    # 엔티티 탐색은 주제별(/topics/)로 통합 → /wiki/ 허브는 리다이렉트만(중복 제거)
    total_stories = len({a["id"] for a in atoms})
    (OUT / "index.html").write_text(
        '<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">'
        '<meta http-equiv="refresh" content="0; url=/topics/">'
        '<link rel="canonical" href="https://soonsal.com/topics/">'
        '<title>주제별 브리핑 — 순살브리핑</title>'
        '<meta name="robots" content="noindex,follow"></head>'
        '<body><a href="/topics/">주제별 브리핑으로 이동…</a></body></html>',
        encoding="utf-8")

    print(f"📚 wiki: 엔티티 페이지 {len(built)}개(허브→주제별 리다이렉트) · 스토리 {total_stories}")
    return built


if __name__ == "__main__":
    build()

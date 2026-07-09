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
.chip{border:1px solid #333;border-radius:16px;padding:5px 13px;font-size:.86rem;transition:.15s}
.chip:hover{border-color:#F07040;color:#F07040}
.chip b{color:#888;font-weight:400;margin-left:5px;font-size:.8rem}
.tp{background:#1a2030;border-color:#2a3550}
.story{padding:13px 4px;border-bottom:1px solid #222}
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
.eng-t{font-size:.82rem;color:#2ecc71;font-weight:600;margin-top:6px}
.eng-t:first-child{margin-top:0}
.eng-k{font-size:.78rem;color:#9aa;margin-top:1px;line-height:1.5}
.grp{margin:26px 0}
.grp h2{font-size:1.15rem;margin-bottom:12px}
.more{color:#F07040;font-size:.86rem;margin-top:12px;display:inline-block}
"""


def head(title, desc, canonical, ld=None):
    ldtag = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title><meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{canonical}"><meta name="robots" content="index, follow">
<meta property="og:type" content="website"><meta property="og:site_name" content="순살브리핑 Soonsal">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{canonical}"><meta property="og:locale" content="ko_KR">
{ldtag}<style>{CSS}</style></head><body><div class="wrap">
<a class="home" href="/">← 순살 홈</a>"""

FOOT = "</div></body></html>"


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

        rows = []
        for a in items:
            eng = ""
            if a["english"]:
                rows_e = "".join(
                    f'<div class="eng-t">{escape(w["en"])}</div>'
                    f'<div class="eng-k">{escape(w["ko"][:100])}</div>' for w in a["english"])
                eng = (f'<details class="eng"><summary>영어 표현 {len(a["english"])}</summary>'
                       f'<div class="engbox">{rows_e}</div></details>')
            rows.append(
                f'<div class="story"><a href="{a["url"]}">'
                f'<span class="d">{a["date"]}</span>'
                f'<span class="st">{escape(clean_title(a["title"]))}</span></a>'
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
        desc = (f"{e['name']}이(가) 등장한 순살브리핑 스토리 {len(items)}건을 최신순으로. "
                f"연관 {', '.join(r['name'] for r, _ in related[:4])}.")
        body = (head(f"{e['name']} 관련 브리핑 {len(items)}건 | 순살브리핑", desc, canonical, ld)
                + f'<div class="kind">{emoji} {type_label}</div><h1>{escape(e["name"])}</h1>'
                + f'<p class="sub">이 {type_label}이(가) 등장한 스토리 {len(items)}건 · '
                  f'최근 {items[0]["date"]} · 영어 표현 {n_eng}개 · '
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

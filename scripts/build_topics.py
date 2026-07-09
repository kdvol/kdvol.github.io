#!/usr/bin/env python3
"""주제별 태그 페이지 생성 — 스토리 단위 (atomize.py 산출 소비).

각 주제 페이지는 그 주제로 분류된 개별 스토리를 최신순으로 나열하고,
스토리에 연결된 영어 표현을 함께 보여준다. 뉴스레터 통짜가 아니라
스토리 하나하나가 항목. 각 항목은 뉴스레터의 해당 스토리 앵커로 딥링크.

generate_seo.py가 atomize→여기 순으로 호출하므로 매 발행마다 자동 갱신.
분류 사전(topics_taxonomy.json)은 데이터 파일 — 사람이 신경 쓸 필요 없음.
"""
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

import atomize

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"
OUT = ROOT / "topics"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#111;color:#eee;font-family:'DM Sans','Apple SD Gothic Neo',sans-serif;min-height:100vh;-webkit-text-size-adjust:100%}
.wrap{max-width:760px;margin:0 auto;padding:24px 16px 60px}
a{color:#eee;text-decoration:none}
h1{font-size:1.45rem;margin-bottom:4px;letter-spacing:-.02em}
.sub{color:#888;font-size:.85rem;margin-bottom:8px}
.home{color:#F07040;font-size:.88rem;display:inline-block;margin-bottom:14px}
.searchbar{display:block;width:100%;background:#1a1a1a;border:1px solid #2c2c2c;border-radius:10px;
  padding:11px 14px;color:#eee;font-size:.95rem;margin:6px 0 18px}
.searchbar::placeholder{color:#666}
.tags{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}
.tag{border:1px solid #333;border-radius:18px;padding:6px 13px;font-size:.88rem;transition:.15s;white-space:nowrap}
.tag:hover,.tag:active{border-color:#F07040;color:#F07040}
.tag b{color:#F07040;font-weight:700;margin-left:5px;font-size:.82rem}
/* 균일 높이 스토리 행 — 영어는 기본 접힘 */
.item{border-bottom:1px solid #1c1c1c}
.item-row{display:flex;gap:11px;align-items:baseline;padding:11px 2px}
.dt{color:#666;font-size:.76rem;font-variant-numeric:tabular-nums;white-space:nowrap;flex:0 0 auto;padding-top:2px}
.ti{font-size:.95rem;line-height:1.4;color:#eee;flex:1;
  overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;transition:color .15s}
.item-row:hover .ti,.item-row:active .ti{color:#F07040}
.chips{display:flex;gap:5px;flex-wrap:wrap;margin:-4px 0 8px 46px}
.mtag{font-size:.68rem;color:#8b93a0;background:#181b20;border-radius:4px;padding:1px 7px;white-space:nowrap}
details.eng{margin:-2px 0 8px 46px}
details.eng>summary{list-style:none;font-size:.7rem;color:#2ecc71;cursor:pointer;display:inline-block}
details.eng>summary::-webkit-details-marker{display:none}
details.eng>summary::before{content:"🔤 ";}
details.eng[open]>summary{margin-bottom:6px;color:#888}
.engbox{border-left:2px solid #2ecc71;padding:2px 0 2px 11px}
.eng-t{font-size:.82rem;color:#2ecc71;font-weight:600;margin-top:6px}
.eng-t:first-child{margin-top:0}
.eng-k{font-size:.78rem;color:#9aa;line-height:1.5;margin-top:1px}
.count{color:#666;font-size:.8rem;margin:16px 0 4px}
@media(min-width:640px){.wrap{padding:32px 20px 60px}.ti{font-size:1rem}}
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


def topic_name_map(tax):
    return {t["slug"]: t for t in tax["topics"]}


def _mmdd(iso):
    return iso[5:].replace("-", ".")          # 2026-07-09 → 07.09


def story_html(a, names, self_slug):
    """균일 높이 컴팩트 행. 영어는 <details>로 기본 접힘(모바일 스캔성)."""
    other = [names[s]["name"] for s in a["topics"] if s != self_slug and s in names]
    chips = ('<div class="chips">' + "".join(f'<span class="mtag">{n}</span>' for n in other)
             + "</div>") if other else ""
    eng = ""
    if a["english"]:
        n = len(a["english"])
        rows = "".join(
            f'<div class="eng-t">{escape(e["en"])}</div><div class="eng-k">{escape(e["ko"][:110])}</div>'
            for e in a["english"])
        eng = (f'<details class="eng"><summary>영어 표현 {n}</summary>'
               f'<div class="engbox">{rows}</div></details>')
    return (f'<div class="item"><a class="item-row" href="{a["url"]}">'
            f'<span class="dt">{_mmdd(a["date"])}</span>'
            f'<span class="ti">{escape(clean_title(a["title"]))}</span></a>'
            + chips + eng + "</div>")


def main(atoms=None):
    if atoms is None:
        atoms = atomize.build()
    tax = atomize.load_tax()
    ent = atomize.load_entities()
    ent_by_slug = {e["slug"]: e for e in ent["entities"]}
    ent_types = ent.get("types", {})
    names = topic_name_map(tax)
    OUT.mkdir(exist_ok=True)
    today = date.today().isoformat()
    min_n = tax.get("min_stories_per_topic", 3)

    built = []
    for t in tax["topics"]:
        slug, name, emoji = t["slug"], t["name"], t["emoji"]
        matched = [a for a in atoms if slug in a["topics"]]
        if len(matched) < min_n:
            continue
        built.append((slug, name, emoji, len(matched)))
        n_eng = sum(len(a["english"]) for a in matched)

        # 이 주제에서 가장 자주 등장한 엔티티 → 위키로 크로스링크
        ent_freq = Counter(e for a in matched for e in a["entities"])
        top_ent = [(ent_by_slug[s], n) for s, n in ent_freq.most_common(12) if s in ent_by_slug][:10]
        ent_html = ("".join(
            f'<a class="tag" href="/wiki/{e["slug"]}.html">'
            f'{ent_types.get(e["type"], {}).get("emoji", "")} {escape(e["name"])}<b>{n}</b></a>'
            for e, n in top_ent))
        ent_box = (f'<div style="margin:10px 0 18px"><div style="color:#888;font-size:.82rem;'
                   f'margin-bottom:8px">이 주제에 자주 나오는 대상 →</div>'
                   f'<div class="tags">{ent_html}</div></div>') if ent_html else ""

        canonical = f"{BASE}/topics/{slug}.html"
        ld = {"@context": "https://schema.org", "@type": "CollectionPage",
              "name": f"{name} 관련 스토리 모음", "url": canonical, "inLanguage": "ko",
              "isPartOf": {"@type": "WebSite", "name": "순살브리핑", "url": f"{BASE}/"},
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "url": f"{BASE}{a['url']}",
                   "name": clean_title(a["title"])} for i, a in enumerate(matched[:40])]}}
        body = (head(f"{name} 관련 브리핑 스토리 {len(matched)}건 — 순살브리핑",
                     f"{name} 주제를 다룬 순살브리핑 스토리 {len(matched)}건을 최신순으로. "
                     f"관련 영어 표현 {n_eng}개 포함.", canonical, ld)
                + f'<h1>{emoji} {name}</h1><p class="sub">스토리 {len(matched)}건 · 영어 표현 {n_eng}개 · '
                  f'<a href="/topics/" style="color:#F07040">주제</a> · '
                  f'<a href="/wiki/" style="color:#F07040">위키</a></p>'
                + f'<a class="searchbar" href="/search/" style="color:#666">🔍 전체 브리핑 검색…</a>'
                + ent_box
                + f'<div class="count">최신순 · {len(matched)}건</div>'
                + "".join(story_html(a, names, slug) for a in matched)
                + FOOT)
        (OUT / f"{slug}.html").write_text(body, encoding="utf-8")

    # 허브
    canonical = f"{BASE}/topics/"
    ld = {"@context": "https://schema.org", "@type": "CollectionPage",
          "name": "주제별 브리핑 아카이브", "url": canonical, "inLanguage": "ko"}
    tags = "".join(
        f'<a class="tag" href="/topics/{slug}.html">{emoji} {name}<b>{n}</b></a>'
        for slug, name, emoji, n in sorted(built, key=lambda x: -x[3]))
    total_eng = sum(len(a["english"]) for a in atoms)
    hub = (head("주제별 브리핑 — 순살브리핑",
                "크립토·AI·반도체·연준 등 주제별로 모아 보는 순살브리핑. 뉴스레터를 스토리 단위로 분류.",
                canonical, ld)
           + f'<h1>주제별 브리핑</h1><p class="sub">스토리 {len(atoms)}건을 {len(built)}개 주제로 분류 · '
             f'<a href="/wiki/" style="color:#F07040">위키</a></p>'
           + f'<a class="searchbar" href="/search/" style="color:#666">🔍 전체 브리핑 검색…</a>'
           + f'<div class="tags">{tags}</div>' + FOOT)
    (OUT / "index.html").write_text(hub, encoding="utf-8")

    print(f"🏷️  topics: {len(built)}개 주제 페이지(+허브) · 스토리 {len(atoms)} · 영어 {total_eng}")


if __name__ == "__main__":
    main()

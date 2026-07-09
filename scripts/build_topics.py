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
body{background:#111;color:#eee;font-family:'DM Sans','Apple SD Gothic Neo',sans-serif;min-height:100vh}
.wrap{max-width:820px;margin:0 auto;padding:32px 20px}
a{color:#eee;text-decoration:none}
h1{font-size:1.5rem;margin-bottom:6px}
.sub{color:#888;font-size:.9rem;margin-bottom:22px}
.home{color:#F07040;font-size:.9rem;display:inline-block;margin-bottom:18px}
.tags{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}
.tag{border:1px solid #333;border-radius:20px;padding:7px 16px;font-size:.92rem;transition:.15s}
.tag:hover{border-color:#F07040;color:#F07040}
.tag b{color:#F07040;font-weight:600;margin-left:6px}
.story{padding:16px 4px;border-bottom:1px solid #222}
.story-head{display:flex;gap:12px;align-items:baseline}
.d{color:#777;font-size:.82rem;white-space:nowrap;font-variant-numeric:tabular-nums;padding-top:2px}
.st{font-size:1.02rem;line-height:1.5;transition:.15s;font-weight:600}
.story:hover .st{color:#F07040}
.lb{display:inline-block;font-size:.7rem;color:#f5a623;letter-spacing:.04em;margin-top:5px;text-transform:uppercase}
.xtags{margin-top:6px}
.xtag{font-size:.74rem;color:#888;border:1px solid #2a2a2a;border-radius:4px;padding:1px 7px;margin-right:5px}
.eng{margin:9px 0 2px;padding:9px 12px;background:#161616;border-left:2px solid #2ecc71;border-radius:0 6px 6px 0}
.eng-t{font-size:.85rem;color:#2ecc71;font-weight:600}
.eng-k{font-size:.82rem;color:#aaa;margin-top:2px;line-height:1.5}
.eng-h{font-size:.72rem;color:#666;margin-bottom:6px;letter-spacing:.03em}
.more{color:#F07040;font-size:.85rem;margin-top:8px;display:inline-block}
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


def story_html(a, names, self_slug):
    other = [names[s]["name"] for s in a["topics"] if s != self_slug and s in names]
    xtags = ('<div class="xtags">' + "".join(f'<span class="xtag">{n}</span>' for n in other)
             + "</div>") if other else ""
    eng = ""
    if a["english"]:
        rows = "".join(
            f'<div class="eng-t">{escape(e["en"])}</div><div class="eng-k">{escape(e["ko"][:110])}</div>'
            for e in a["english"])
        eng = f'<div class="eng"><div class="eng-h">📎 이 스토리의 영어 표현</div>{rows}</div>'
    return (f'<div class="story"><a href="{a["url"]}"><div class="story-head">'
            f'<span class="d">{a["date"]}</span>'
            f'<span class="st">{escape(clean_title(a["title"]))}</span></div></a>'
            + (f'<span class="lb">{escape(a["label"])}</span>' if a["label"] else "")
            + xtags + eng + "</div>")


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
                + f'<h1>{emoji} {name}</h1><p class="sub">이 주제를 다룬 스토리 {len(matched)}건 · '
                  f'영어 표현 {n_eng}개 · {today} 기준 · '
                  f'<a href="/topics/" style="color:#F07040">전체 주제 보기</a> · '
                  f'<a href="/wiki/" style="color:#F07040">위키</a></p>'
                + ent_box
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
             f'영어 표현 {total_eng}개 연결 · {today} 기준</p>'
           + f'<div class="tags">{tags}</div>' + FOOT)
    (OUT / "index.html").write_text(hub, encoding="utf-8")

    print(f"🏷️  topics: {len(built)}개 주제 페이지(+허브) · 스토리 {len(atoms)} · 영어 {total_eng}")


if __name__ == "__main__":
    main()

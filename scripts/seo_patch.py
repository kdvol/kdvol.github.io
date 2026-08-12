#!/usr/bin/env python3
"""리포 스크립트가 만들지 않는 페이지에 SEO 기본을 채운다.

morning/(모닝순살)은 챗 워크플로가 만들어 커밋된다. 그래서 canonical·OG·
구조화 데이터가 아예 없었다 — 검색은 이 페이지를 '제목만 있는 문서'로 본다.
발행 뒤에 채우는 편이 확실하다(발행 쪽 템플릿을 건드리면 매일 깨질 위험이 있다).

넣는 것:
  canonical      중복 색인 방지. 쿼리 붙은 주소로 들어와도 한 곳으로 모인다
  og:*           카톡·슬랙 공유 시 카드가 뜬다
  NewsArticle    검색·AI가 '언제 나온 무슨 기사'인지 안다
  BreadcrumbList 검색 결과에 경로가 뜨고, 사이트 구조를 알려준다

지어내지 않는다 — 제목·날짜·설명은 페이지에서 읽은 값만 쓴다.
이미 있으면 건너뛴다(매 빌드마다 중복으로 쌓이면 안 된다).
"""

import html as H
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"
MARK = "<!-- soonsal:seo -->"

PUB = {"@type": "Organization", "name": "순살브리핑", "url": BASE + "/",
       "logo": {"@type": "ImageObject", "url": BASE + "/apple-touch-icon.png"}}


def _meta(t, name=None, prop=None):
    pat = (rf'<meta[^>]+name="{name}"[^>]+content="([^"]*)"' if name
           else rf'<meta[^>]+property="{prop}"[^>]+content="([^"]*)"')
    m = re.search(pat, t, re.I)
    return H.unescape(m.group(1)).strip() if m else ""


def _title(t):
    m = re.search(r"<title>([^<]*)</title>", t)
    return H.unescape(m.group(1)).split("|")[0].strip() if m else ""


def _date_from_path(p: Path):
    """chart/2026/0812.html → 2026-08-12. 경로가 곧 날짜다."""
    m = re.search(r"/(\d{4})/(\d{2})(\d{2})", "/" + str(p).replace("\\", "/"))
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def patch_morning(p: Path) -> bool:
    t = p.read_text(encoding="utf-8")
    if MARK in t or "</head>" not in t:
        return False

    rel = "/" + str(p.relative_to(ROOT)).replace("\\", "/")
    url = BASE + rel
    title = _title(t) or "모닝순살"
    desc = _meta(t, name="description") or "장 열리기 전 5분, 오늘 시장에서 볼 것만."
    date = _date_from_path(p)

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "NewsArticle", "headline": title[:110], "description": desc[:300],
             "url": url, "mainEntityOfPage": url, "inLanguage": "ko",
             "publisher": PUB, "isAccessibleForFree": True,
             "articleSection": "모닝순살",
             **({"datePublished": date, "dateModified": date} if date else {})},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "순살브리핑", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "모닝순살",
                 "item": BASE + "/chart/"},
                {"@type": "ListItem", "position": 3, "name": title[:80], "item": url},
            ]},
        ],
    }

    add = [MARK, f'<link rel="canonical" href="{url}"/>']
    if not _meta(t, prop="og:title"):
        add += [
            '<meta property="og:type" content="article"/>',
            f'<meta property="og:title" content="{H.escape(title)}"/>',
            f'<meta property="og:description" content="{H.escape(desc[:160])}"/>',
            f'<meta property="og:url" content="{url}"/>',
            '<meta property="og:site_name" content="순살브리핑"/>',
            '<meta name="twitter:card" content="summary_large_image"/>',
        ]
    add.append('<script type="application/ld+json">'
               + json.dumps(ld, ensure_ascii=False) + "</script>")

    p.write_text(t.replace("</head>", "\n".join(add) + "\n</head>", 1), encoding="utf-8")
    return True


BC_MARK = "<!-- soonsal:bc -->"

# 경로가 붙는 자리. 검색 결과에 'soonsal.com > 위키 > 엔비디아'로 뜨고,
# 크롤러가 사이트 구조를 이해한다. 위키·주제별·뉴스레터는 이미 LD가 있어서
# BreadcrumbList만 따로 얹는다(기존 LD를 건드리면 매 빌드마다 충돌한다).
BREADCRUMBS = [
    ("wiki", "위키", "/wiki/"),
    ("topics", "주제별", "/topics/"),
    ("newsletters", "브리핑", "/newsletters/"),
]


def patch_breadcrumb(p: Path, section_name: str, section_url: str) -> bool:
    t = p.read_text(encoding="utf-8")
    if BC_MARK in t or "</head>" not in t:
        return False
    rel = "/" + str(p.relative_to(ROOT)).replace("\\", "/")
    url = BASE + rel
    title = _title(t) or section_name
    crumbs = [
        {"@type": "ListItem", "position": 1, "name": "순살브리핑", "item": BASE + "/"},
        {"@type": "ListItem", "position": 2, "name": section_name,
         "item": BASE + section_url},
    ]
    # 목록 페이지 자신은 2단까지. 개별 문서면 3단.
    if not rel.rstrip("/").endswith(section_url.strip("/")):
        crumbs.append({"@type": "ListItem", "position": 3, "name": title[:80], "item": url})
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList",
          "itemListElement": crumbs}
    add = (BC_MARK + '<script type="application/ld+json">'
           + json.dumps(ld, ensure_ascii=False) + "</script>")
    p.write_text(t.replace("</head>", add + "\n</head>", 1), encoding="utf-8")
    return True


def main():
    n = 0
    base = ROOT / "chart"
    if base.exists():
        for p in sorted(base.rglob("*.html")):
            n += patch_morning(p)
    print(f"🔍 seo_patch: 모닝순살 {n}개에 canonical·OG·구조화 데이터 추가")

    b = 0
    for folder, label, sec_url in BREADCRUMBS:
        d = ROOT / folder
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.html")):
            b += patch_breadcrumb(p, label, sec_url)
    print(f"🔍 seo_patch: 경로(BreadcrumbList) {b}개 페이지")
    return n + b


if __name__ == "__main__":
    main()

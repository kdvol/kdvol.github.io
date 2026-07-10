#!/usr/bin/env python3
"""sitemap.xml / rss.xml / robots.txt 자동 생성.

deploy.py가 git commit 직전에 호출한다 (단독 실행도 가능).
콘텐츠 파일을 건드리지 않고 루트에 3개 파일만 쓴다.
"""
import re
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"
KST = timezone(timedelta(hours=9))

SECTIONS = [  # (glob, 우선순위)
    ("newsletters/2026/*.html", "0.8"),
    ("cardnews/2026/*.html", "0.6"),
    ("english/2026/*.html", "0.6"),
    ("financial-english/*.html", "0.5"),
    ("special/*.html", "0.5"),
    ("topics/*.html", "0.7"),
    ("wiki/*.html", "0.7"),
]
INDEXES = ["", "newsletters/", "cardnews/", "english/", "financial-english/", "youtube/", "topics/", "search/"]

DATED = re.compile(r"(\d{2})(\d{2})(?:-[a-z0-9-]+)?\.html$")


def page_date(path):
    m = DATED.search(path.name)
    if m:
        year = int(path.parent.name) if path.parent.name.isdigit() else date.today().year
        try:
            return date(year, int(m.group(1)), int(m.group(2)))
        except ValueError:
            pass
    return date.fromtimestamp(path.stat().st_mtime)


def get_title(path):
    head = path.read_text(encoding="utf-8", errors="replace")[:3000]
    m = re.search(r"<title>([^<]+)</title>", head)
    return m.group(1).strip() if m else path.stem


def build_sitemap():
    urls = []
    today = date.today().isoformat()
    for idx in INDEXES:
        p = ROOT / idx / "index.html"
        if p.exists():
            urls.append((f"{BASE}/{idx}", today, "1.0" if idx == "" else "0.7"))
    for pattern, prio in SECTIONS:
        for p in sorted(ROOT.glob(pattern)):
            if p.name == "index.html":
                continue
            rel = p.relative_to(ROOT).as_posix()
            urls.append((f"{BASE}/{rel}", page_date(p).isoformat(), prio))
    body = "".join(
        f"<url><loc>{escape(u)}</loc><lastmod>{d}</lastmod><priority>{pr}</priority></url>\n"
        for u, d, pr in urls)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n",
        encoding="utf-8")
    return len(urls)


def build_rss(limit=20):
    posts = sorted((ROOT / "newsletters" / "2026").glob("*.html"),
                   key=page_date, reverse=True)[:limit]
    items = []
    for p in posts:
        rel = p.relative_to(ROOT).as_posix()
        d = page_date(p)
        pub = datetime(d.year, d.month, d.day, 9, 0, tzinfo=KST)
        title = escape(get_title(p))
        link = f"{BASE}/{rel}"
        items.append(
            f"<item><title>{title}</title><link>{link}</link>"
            f"<guid isPermaLink=\"true\">{link}</guid>"
            f"<pubDate>{pub.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate></item>")
    (ROOT / "rss.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>\n'
        f"<title>순살브리핑</title><link>{BASE}/</link>"
        "<description>뼈 발라낸 금융·경제 데일리 브리핑</description>"
        "<language>ko</language>\n" + "\n".join(items) + "\n</channel></rss>\n",
        encoding="utf-8")
    return len(items)


def build_robots():
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nDisallow: /_queue/\n\nSitemap: {BASE}/sitemap.xml\n",
        encoding="utf-8")


def main():
    # nav 자동 동기화 → 콘텐츠 메타 → 아톰화 → 사전 진화 → 주제/위키/검색 → sitemap/rss
    try:
        import build_nav
        build_nav.main()
    except Exception as e:
        print(f"⚠️ build_nav 실패(계속 진행): {e}")
    try:
        import enrich_articles
        enrich_articles.main()
    except Exception as e:
        print(f"⚠️ enrich_articles 실패(계속 진행): {e}")
    atoms = None
    try:
        import atomize, auto_evolve, entity_discovery
        atomize.build()                     # 1차: story_atoms.json + _pending 축적
        auto_evolve.main()                  # 주제 자동 승격(키 있을 때)
        entity_discovery.main()             # 엔티티 자동 발굴·승격(키 있을 때)
        atoms = atomize.build()             # 2차: 진화된 사전으로 최종 분류 (이후 재사용)
    except Exception as e:
        print(f"⚠️ atomize/evolve 실패(계속 진행): {e}")
    try:
        import build_topics
        build_topics.main(atoms)            # 스토리 단위 주제 페이지 (아톰 재사용)
    except Exception as e:
        print(f"⚠️ build_topics 실패(계속 진행): {e}")
    try:
        import build_wiki
        build_wiki.build(atoms)             # 엔티티 지식베이스(위키) (아톰 재사용)
    except Exception as e:
        print(f"⚠️ build_wiki 실패(계속 진행): {e}")
    try:
        import build_search
        build_search.build(atoms)           # 클라이언트 사이드 검색 색인+페이지
    except Exception as e:
        print(f"⚠️ build_search 실패(계속 진행): {e}")
    try:
        import build_sharepages
        build_sharepages.build(atoms)       # 스토리별 OG 공유 페이지(/s/)
    except Exception as e:
        print(f"⚠️ build_sharepages 실패(계속 진행): {e}")
    try:
        import build_llms
        build_llms.build(atoms)             # llms.txt/llms-full.txt (AEO, 매 발행 갱신)
    except Exception as e:
        print(f"⚠️ build_llms 실패(계속 진행): {e}")
    try:
        import build_include
        build_include.main()                # /soonsal.js 태그 1회 보장(FAB+공유는 그 파일에)
    except Exception as e:
        print(f"⚠️ build_include 실패(계속 진행): {e}")
    n_urls = build_sitemap()
    n_items = build_rss()
    build_robots()
    print(f"🗺️  SEO 생성: sitemap {n_urls} URLs · rss {n_items} items · robots.txt")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""sitemap.xml / rss.xml / robots.txt 자동 생성.

deploy.py가 git commit 직전에 호출한다 (단독 실행도 가능).
콘텐츠 파일을 건드리지 않고 루트에 3개 파일만 쓴다.
"""
import json
import re
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://soonsal.com"
KST = timezone(timedelta(hours=9))

SECTIONS = [  # (glob, 우선순위)
    ("newsletters/2026/*.html", "0.8"),
    ("chart/2026/*.html", "0.8"),
    ("cardnews/2026/*.html", "0.6"),
    ("english/2026/*.html", "0.6"),
    ("financial-english/*.html", "0.5"),
    ("special/*.html", "0.5"),
    ("topics/*.html", "0.7"),
    ("wiki/*.html", "0.7"),
]
# ★ `advertise/` 가 아니라 `collab/` 이다 (2026-08-17).
#   문의 페이지가 /collab/ 로 옮겨지면서 /advertise/ 는 리다이렉트 껍데기만
#   남았고, 그 껍데기에는 noindex 가 달려 있다. 그런데 사이트맵은 계속 옛
#   주소를 가리켰다 — 「색인해 달라」와 「색인하지 마라」를 동시에 보낸 것이다.
#   Search Console 이 「NOINDEX 태그에 의해 제외됨」으로 잡은 게 이것이다.
INDEXES = ["", "newsletters/", "chart/", "cardnews/", "english/",
           "financial-english/", "youtube/", "topics/", "search/", "collab/"]

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


def _traffic_priority():
    """실제로 읽히는 페이지의 우선순위를 올린다.

    auto_improve.py가 남긴 content/signals.json의 조회수를 읽어, 상위 트래픽 페이지에
    가산점을 준다. 여기서 적용해야 매 빌드마다 유지된다 — sitemap을 통째로 다시 쓰기
    때문에 밖에서 고쳐두면 다음 빌드에 날아간다. 파일이 없으면 가산점 0.
    """
    p = ROOT / "content" / "signals.json"
    if not p.exists():
        return {}
    try:
        top = json.loads(p.read_text(encoding="utf-8")).get("top_paths", [])
    except (OSError, ValueError) as e:
        print(f"⚠️ signals.json 읽기 실패(가산점 없이 진행): {type(e).__name__}")
        return {}
    hits = {r["path"]: r["hits"] for r in top if r.get("hits")}
    if not hits:
        return {}
    peak = max(hits.values())
    return {path: (0.2 if h >= peak * 0.5 else 0.1) for path, h in hits.items()}


def build_sitemap():
    urls = []
    today = date.today().isoformat()
    bonus = _traffic_priority()

    def prio_of(url, base):
        # sitemap은 디렉터리를 슬래시 없이 쓰고(/newsletters) 브라우저는 있게 보낸다
        path = url.replace(BASE, "") or "/"
        b = bonus.get(path) or bonus.get(path.rstrip("/") + "/") or bonus.get(path + "/") or 0
        return f"{min(1.0, float(base) + b):.1f}"

    for idx in INDEXES:
        p = ROOT / idx / "index.html"
        if p.exists():
            u = f"{BASE}/{idx}"
            urls.append((u, today, prio_of(u, "1.0" if idx == "" else "0.7")))
    for pattern, prio in SECTIONS:
        for p in sorted(ROOT.glob(pattern)):
            if p.name == "index.html":
                continue
            rel = p.relative_to(ROOT).as_posix()
            u = f"{BASE}/{rel}"
            urls.append((u, page_date(p).isoformat(), prio_of(u, prio)))
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
        "<description>순살만 발라낸 금융·경제 데일리 브리핑</description>"
        "<language>ko</language>\n" + "\n".join(items) + "\n</channel></rss>\n",
        encoding="utf-8")
    return len(items)


def build_robots():
    # _publish=발행 작업사본(카드뉴스 중복), s=공유 OG 썸(noindex이지만 크롤 낭비 차단)
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n"
        # /partners=거래처별 제안서(단가 포함), /stats=운영자 대시보드.
        # 크롤러를 막는 건 최소 조치일 뿐 접근 통제가 아니다 — 실제 보호는 암호화다.
        f"Disallow: /_queue/\nDisallow: /_publish/\nDisallow: /node_modules/\n"
        f"Disallow: /stats/\nDisallow: /partners/\nDisallow: /ops/\n"
        f"\nSitemap: {BASE}/sitemap.xml\n",
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
        import build_advertise
        build_advertise.build()             # 광고·파트너십 문의 페이지
    except Exception as e:
        print(f"⚠️ build_advertise 실패(계속 진행): {e}")
    try:
        import build_stats
        build_stats.build(atoms)            # 운영자용 반응 통계(/stats/, noindex)
    except Exception as e:
        print(f"⚠️ build_stats 실패(계속 진행): {e}")
    try:
        import build_saved
        build_saved.build()                 # 내가 모은 스토리(/saved/, 브라우저 로컬)
    except Exception as e:
        print(f"⚠️ build_saved 실패(계속 진행): {e}")
    try:
        import build_home
        build_home.build(atoms)             # 홈(index.html) — 최신 회차·차트로 매일 갱신
    except Exception as e:
        print(f"⚠️ build_home 실패(계속 진행): {e}")
    try:
        import build_api
        build_api.build(atoms)              # /api/entities.json (챗이 아카이브 줄 만들 때 조회)
    except Exception as e:
        print(f"⚠️ build_api 실패(계속 진행): {e}")
    try:
        import build_privacy
        build_privacy.build()               # /privacy/ 수집 안내 (푸터 링크에서만 닿음)
    except Exception as e:
        print(f"⚠️ build_privacy 실패(계속 진행): {e}")
    try:
        import build_talk
        build_talk.build(atoms)             # /talk/ 스토리 막론 전체 코멘트
    except Exception as e:
        print(f"⚠️ build_talk 실패(계속 진행): {e}")
    try:
        import add_talk_link
        add_talk_link.main()                # 발행 HTML 자체에 한마디 링크(메일에서도 살아남게)
    except Exception as e:
        print(f"⚠️ add_talk_link 실패(계속 진행): {e}")
    try:
        import build_cardnews_light
        build_cardnews_light.main()         # 새 카드뉴스 페이지도 자동 경량화
    except Exception as e:
        print(f"⚠️ build_cardnews_light 실패(계속 진행): {e}")
    try:
        import build_youtube
        build_youtube.build()               # /youtube/ 최근 숏츠 (채널 RSS)
    except Exception as e:
        print(f"⚠️ build_youtube 실패(계속 진행): {e}")
    try:
        import build_school
        build_school.build()                # /school/ 강의 판매 (liveklass 링크)
    except Exception as e:
        print(f"⚠️ build_school 실패(계속 진행): {e}")
    try:
        import build_legacy_redirects
        build_legacy_redirects.build()      # 2월 이관 전 옛 URL → 현재 주소
    except Exception as e:
        print(f"⚠️ build_legacy_redirects 실패(계속 진행): {e}")
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
    try:
        import seo_patch
        seo_patch.main()                    # 발행본에 canonical·OG·구조화 데이터 채움
    except Exception as e:
        print(f"⚠️ seo_patch 실패(계속 진행): {e}")

    # build_nav를 맨 앞에서 한 번 돌리지만, 그 뒤 생성기들이 페이지를 새로 쓰면서
    # 주입한 nav 스타일이 지워진다(topics·wiki·search 등). 마지막에 한 번 더 돌려
    # 모든 페이지가 같은 nav를 갖도록 맞춘다.
    try:
        import build_nav
        build_nav.main()
    except Exception as e:
        print(f"⚠️ build_nav(최종) 실패(계속 진행): {e}")

    n_urls = build_sitemap()
    n_items = build_rss()
    build_robots()
    print(f"🗺️  SEO 생성: sitemap {n_urls} URLs · rss {n_items} items · robots.txt")

    # ★ 만들고 나서 스스로 본다 (2026-08-17). 문의 페이지가 /collab/ 로
    #   옮겨졌는데 INDEXES 만 안 고쳐서, 사이트맵이 noindex 껍데기를 계속
    #   가리켰다. Search Console 이 몇 달을 「문제」로 들고 있었다.
    try:
        import subprocess, sys as _sys
        subprocess.run([_sys.executable, str(Path(__file__).parent / "sitemap_lint.py")],
                       cwd=str(ROOT), check=False)
    except Exception as e:
        print(f"⚠️ 사이트맵 자기검사 실패: {e}")


if __name__ == "__main__":
    main()

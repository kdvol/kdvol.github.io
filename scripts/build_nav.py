#!/usr/bin/env python3
"""내비게이션 자동 동기화 — 모든 인덱스 페이지의 nav를 한 정의로 통일(자가치유).

nav가 페이지마다 하드코딩돼 있어 최신 페이지만 새 탭을 갖던 문제 → 매 빌드마다
generate_seo가 이 함수를 호출해 전 페이지 nav를 정규형으로 덮어쓴다. deploy.py가
아카이브 인덱스를 재생성하며 옛 nav를 써도 그 직후 여기서 교정된다.

위키는 공개 탭에서 제외(어드민이 entities.json으로 관리). 엔티티 탐색은 주제별 안에서.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ITEMS = [("/", "최신"), ("/search/", "🔍 검색"), ("/newsletters/", "뉴스레터"),
         ("/topics/", "주제별"), ("/community/", "커뮤니티"), ("/cardnews/", "카드뉴스"),
         ("/english/", "English"), ("/school/", "스쿨"), ("/youtube/", "YouTube")]

PAGES = {"index.html": "/", "newsletters/index.html": "/newsletters/",
         "cardnews/index.html": "/cardnews/", "english/index.html": "/english/",
         "school/index.html": "/school/", "youtube/index.html": "/youtube/"}

NAV_RE = re.compile(r'<div class="nav">.*?</div>', re.S)


def _nav(active):
    links = "".join(
        f'<a href="{h}"{" class=\"active\"" if h == active else ""}>{l}</a>'
        for h, l in ITEMS)
    return f'<div class="nav">{links}</div>'


def main():
    n = 0
    for rel, active in PAGES.items():
        p = ROOT / rel
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        new = NAV_RE.sub(_nav(active), t, count=1)
        if new != t:
            p.write_text(new, encoding="utf-8")
            n += 1
    print(f"🧭 nav 동기화: {n}개 페이지")
    return n


if __name__ == "__main__":
    main()
